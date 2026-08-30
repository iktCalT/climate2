from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd
import plotly.graph_objects as go

from helpers import draw_chart


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
            with patch("helpers.LOCATION_CHART_DIRECTORY", chart_directory):
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
        self.assertEqual(figure.layout.yaxis.title.text, "Temperature (°C)")
        self.assertFalse("yaxis2" in figure.layout)

        spring = figure.data[0]
        self.assertEqual(list(spring.x), [2025, 2026])
        self.assertEqual(list(spring.y), [4.0, 16.0])

        buttons = figure.layout.updatemenus[0].buttons
        self.assertEqual(
            [button.label for button in buttons],
            [
                "Mean temperature",
                "Minimum temperature",
                "Maximum temperature",
                "Precipitation",
            ],
        )
        for metric_index, button in enumerate(buttons):
            expected = [False] * 16
            expected[metric_index * 4 : metric_index * 4 + 4] = [True] * 4
            self.assertEqual(list(button.args[0]["visible"]), expected)

    def test_chart_filename_cannot_escape_the_generated_chart_directory(self):
        history = pd.DataFrame(
            {"temp_mean": [10.0]},
            index=pd.to_datetime(["2026-03-01"]),
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            chart_directory = Path(temporary_directory) / "location_data"
            with patch("helpers.LOCATION_CHART_DIRECTORY", chart_directory):
                with patch.object(go.Figure, "write_html") as write_html:
                    draw_chart(1, 2, history, filename="../personal-chart.html")

            write_html.assert_called_once_with(
                str(chart_directory / "personal-chart.html")
            )


if __name__ == "__main__":
    unittest.main()
