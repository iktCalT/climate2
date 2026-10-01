from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd
import plotly.graph_objects as go

from climate.web.helpers import draw_chart


class ChartRenderingTests(unittest.TestCase):
    def test_location_chart_defaults_to_four_mean_temperature_seasons(self):
        dates = pd.date_range("2025-01-01", periods=24, freq="MS")
        history = pd.DataFrame(
            {
                "temp_mean": range(1, 25),
                "temp_min": range(-4, 20),
                "temp_max": range(6, 30),
                "precip": range(24),
            },
            index=dates,
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            chart_directory = Path(temporary_directory) / "location_data"
            with patch("climate.web.helpers.LOCATION_CHART_DIRECTORY", chart_directory):
                with patch.object(go.Figure, "write_html") as write_html:
                    figure = draw_chart(1, 2, history, filename="test-chart.html")

            self.assertTrue(chart_directory.is_dir())
            write_html.assert_called_once_with(
                str(chart_directory / "test-chart.html")
            )

        self.assertEqual(len(figure.data), 16)
        self.assertEqual(
            [trace.name for trace in figure.data[:4]],
            ["Spring", "Summer", "Fall", "Winter"],
        )
        self.assertTrue(all(trace.visible is True for trace in figure.data[:4]))
        self.assertTrue(all(trace.visible is False for trace in figure.data[4:]))
        self.assertEqual(
            figure.layout.title.text, "Seasonal mean temperature at 1, 2"
        )
        self.assertEqual(figure.layout.title.y, 0.80)
        self.assertEqual(figure.layout.title.yanchor, "middle")
        self.assertEqual(figure.layout.height, 680)
        self.assertEqual(figure.layout.yaxis.title.text, "Temperature (°C)")
        self.assertFalse("yaxis2" in figure.layout)

        spring = figure.data[0]
        self.assertEqual(list(spring.x), [2025, 2026, 2027])
        self.assertEqual(list(spring.y[:2]), [4.0, 16.0])
        self.assertTrue(pd.isna(spring.y[2]))

        buttons = figure.layout.updatemenus[0].buttons
        self.assertEqual(figure.layout.updatemenus[0].y, 1.38)
        self.assertGreater(figure.layout.updatemenus[0].y, figure.layout.title.y)
        self.assertEqual(
            [button.label for button in buttons],
            ["Mean temperature", "Minimum temperature", "Maximum temperature", "Precipitation"],
        )
        for metric_index, button in enumerate(buttons):
            expected = [False] * 16
            expected[metric_index * 4 : metric_index * 4 + 4] = [True] * 4
            self.assertEqual(list(button.args[0]["visible"]), expected)
            self.assertEqual(button.method, "update")
            self.assertEqual(
                button.args[1]["title.text"],
                f"Seasonal {button.label.lower()} at 1, 2",
            )

    def test_each_metric_reports_month_coverage_and_preserves_seasonal_means(self):
        dates = pd.to_datetime([
            "2020-01-01", "2020-03-01", "2020-04-01", "2020-05-01",
            "2020-06-01", "2020-07-01", "2020-10-01", "2021-12-01",
        ])
        history = pd.DataFrame(
            {
                "temp_mean": [1, 3, 4, 5, 6, 7, 10, 12],
                "temp_min": [2, 6, 8, float("nan"), 12, 14, 20, 24],
                "temp_max": [3, 9, float("nan"), 15, 18, float("nan"), 30, 36],
                "precip": [4, 12, 16, 20, float("nan"), 28, 40, 48],
            },
            index=dates,
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            with patch(
                "climate.web.helpers.LOCATION_CHART_DIRECTORY",
                Path(temporary_directory) / "location_data",
            ), patch.object(go.Figure, "write_html"):
                figure = draw_chart(1, 2, history)

        self.assertEqual(len(figure.data), 16)
        self.assertTrue(all(trace.connectgaps is False for trace in figure.data))
        for metric_index in range(4):
            traces = figure.data[metric_index * 4 : metric_index * 4 + 4]
            self.assertTrue(all(trace.visible is (metric_index == 0) for trace in traces))
            for trace in traces:
                self.assertEqual(list(trace.x), [2020, 2021, 2022])
                self.assertEqual(len(trace.customdata), 3)
                self.assertEqual([list(item) for item in trace.customdata][1], [0, 3])
                self.assertTrue(pd.isna(trace.y[1]))
                self.assertIn("%{customdata[0]}/%{customdata[1]} months", trace.hovertemplate)

        # Existing means remain simple means of available monthly values.
        self.assertEqual(list(figure.data[0].y)[0], 4.0)
        self.assertEqual(list(figure.data[0].customdata[0]), [3, 3])
        self.assertEqual(list(figure.data[1].customdata[0]), [2, 3])
        self.assertEqual(list(figure.data[2].customdata[0]), [1, 3])
        # December 2021 belongs to winter 2022, labelled by January's year.
        self.assertEqual(list(figure.data[3].x), [2020, 2021, 2022])
        self.assertEqual(list(figure.data[3].customdata[2]), [1, 3])
        self.assertEqual(list(figure.data[3].y)[2], 12.0)

        expected_units = ["°C", "°C", "°C", "mm/day"]
        for metric_index, unit in enumerate(expected_units):
            self.assertIn(unit, figure.data[metric_index * 4].hovertemplate)
        self.assertEqual(figure.layout.yaxis.title.text, "Temperature (°C)")
        self.assertEqual(
            figure.layout.updatemenus[0].buttons[3].args[1]["yaxis.title.text"],
            "Mean daily precipitation (mm/day)",
        )

    def test_all_metrics_count_only_values_used_in_the_mean(self):
        history = pd.DataFrame(
            {
                "temp_mean": [3, 6, 9, 12, 18, None, 24, None, None],
                "temp_min": [3, 9, None, 12, None, None, 18, 24, 30],
                "temp_max": [6, None, None, 12, 18, 24, 30, 36, None],
                "precip": [3, 6, 9, 12, 18, None, 24, None, None],
            },
            index=pd.date_range("2020-03-01", periods=9, freq="MS"),
        )
        # A stored month with every metric null must still have zero coverage.
        history.loc[pd.Timestamp("2020-01-01")] = float("nan")
        with tempfile.TemporaryDirectory() as directory:
            with patch("climate.web.helpers.LOCATION_CHART_DIRECTORY", Path(directory)), \
                 patch.object(go.Figure, "write_html"):
                figure = draw_chart(1, 2, history)

        expected = (
            ((3, 6), (2, 15), (1, 24)),
            ((2, 6), (1, 12), (3, 24)),
            ((1, 6), (3, 18), (2, 33)),
            ((3, 6), (2, 15), (1, 24)),
        )
        for metric_index, seasons in enumerate(expected):
            for season_index, (count, mean) in enumerate(seasons):
                with self.subTest(metric=metric_index, season=season_index):
                    trace = figure.data[metric_index * 4 + season_index]
                    self.assertEqual(list(trace.x), [2020])
                    self.assertEqual(list(trace.customdata[0]), [count, 3])
                    self.assertEqual(list(trace.y), [mean])
            winter = figure.data[metric_index * 4 + 3]
            self.assertEqual(list(winter.customdata[0]), [0, 3])
            self.assertTrue(pd.isna(winter.y[0]))

    def test_winter_crosses_year_boundary_and_sparse_years_remain_gaps(self):
        history = pd.DataFrame(
            {field: [9, 12, 15, 21] for field in
             ("temp_mean", "temp_min", "temp_max", "precip")},
            index=pd.to_datetime(["2020-12-01", "2021-01-01", "2021-02-01", "2024-03-01"]),
        )
        with tempfile.TemporaryDirectory() as directory:
            with patch("climate.web.helpers.LOCATION_CHART_DIRECTORY", Path(directory)), \
                 patch.object(go.Figure, "write_html"):
                figure = draw_chart(1, 2, history)

        for trace in figure.data:
            self.assertEqual(list(trace.x), [2021, 2022, 2023, 2024])
            self.assertFalse(trace.connectgaps)
            for index in (1, 2):
                self.assertTrue(pd.isna(trace.y[index]))
                self.assertEqual(list(trace.customdata[index]), [0, 3])
        for metric_index in range(4):
            winter = figure.data[metric_index * 4 + 3]
            self.assertEqual(winter.y[0], 12)
            self.assertEqual(list(winter.customdata[0]), [3, 3])
            spring = figure.data[metric_index * 4]
            self.assertEqual(spring.y[3], 21)
            self.assertEqual(list(spring.customdata[3]), [1, 3])

    def test_empty_history_has_no_synthetic_seasonal_points(self):
        history = pd.DataFrame(
            columns=["temp_mean", "temp_min", "temp_max", "precip"],
            index=pd.DatetimeIndex([]),
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            with patch(
                "climate.web.helpers.LOCATION_CHART_DIRECTORY",
                Path(temporary_directory) / "location_data",
            ), patch.object(go.Figure, "write_html"):
                figure = draw_chart(1, 2, history)
        self.assertEqual(len(figure.data), 16)
        for trace in figure.data:
            self.assertEqual(len(trace.x), 0)
            self.assertEqual(len(trace.y), 0)
            self.assertEqual(len(trace.customdata), 0)

    def test_chart_filename_cannot_escape_the_generated_chart_directory(self):
        history = pd.DataFrame(
            {"temp_mean": [10.0]},
            index=pd.to_datetime(["2026-03-01"]),
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            chart_directory = Path(temporary_directory) / "location_data"
            with patch("climate.web.helpers.LOCATION_CHART_DIRECTORY", chart_directory):
                with patch.object(go.Figure, "write_html") as write_html:
                    draw_chart(1, 2, history, filename="../personal-chart.html")

            write_html.assert_called_once_with(
                str(chart_directory / "personal-chart.html")
            )


if __name__ == "__main__":
    unittest.main()
