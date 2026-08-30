from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd
import plotly.graph_objects as go

from helpers import draw_chart


class ChartRenderingTests(unittest.TestCase):
    def test_location_chart_uses_current_plotly_axis_titles(self):
        history = pd.DataFrame(
            {
                "temp_mean": [10.0, 11.0],
                "temp_max": [15.0, 16.0],
                "temp_min": [5.0, 6.0],
                "precip": [2.0, 3.0],
            },
            index=pd.to_datetime(["2026-01-01", "2026-02-01"]),
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            chart_directory = Path(temporary_directory) / "location_data"
            with patch("helpers.LOCATION_CHART_DIRECTORY", chart_directory):
                with patch.object(go.Figure, "write_html") as write_html:
                    figure = draw_chart(1, 2, history, filename="test-chart.html")

            self.assertTrue(chart_directory.is_dir())

        self.assertEqual(figure.layout.yaxis.title.text, "Temperature (°C)")
        self.assertEqual(figure.layout.yaxis.title.font.color, "red")
        self.assertEqual(
            figure.layout.yaxis2.title.text, "Mean daily precipitation (mm)"
        )
        self.assertEqual(figure.layout.yaxis2.title.font.color, "blue")
        write_html.assert_called_once_with(str(chart_directory / "test-chart.html"))


if __name__ == "__main__":
    unittest.main()
