from datetime import date
import unittest

import numpy as np

import noaa_core


class FakeArchive:
    def __init__(self):
        self.daily_calls = 0

    def records(self, file_url, specifications):
        if "/month/" in file_url:
            return {"temp_mean": b"mean", "precip": b"precip"}
        self.daily_calls += 1
        day = int(file_url[-2:])
        return {
            "temp_min": f"min:{day}".encode(),
            "temp_max": f"max:{day}".encode(),
        }


class FakeDecoder:
    latitudes = np.array([-80.0, -80.0, 80.0, 80.0])
    longitudes = np.array([0.0, 180.0, 0.0, 180.0])

    def decode(self, payload, field_name, expected_date=None):
        token = payload.decode()
        if token == "mean":
            value = 280.0
            short_name = "2t"
            units = "K"
        elif token == "precip":
            value = 2.0 / 86_400.0
            short_name = "prate"
            units = "kg m-2 s-1"
        elif token.startswith("min:"):
            value = 275.0 - int(token.split(":")[1]) / 10.0
            short_name = "2t"
            units = "K"
        else:
            value = 285.0 + int(token.split(":")[1]) / 10.0
            short_name = "2t"
            units = "K"
        return noaa_core.GridField(
            values=np.full(4, value),
            latitudes=self.latitudes,
            longitudes=self.longitudes,
            short_name=short_name,
            units=units,
            grid_type="regular_gg",
        )


class FakeDownloadClient(noaa_core.CoreArchiveClient):
    def __init__(self, index_text, file_bytes):
        super().__init__(sleep=lambda _: None)
        self.index_text = index_text
        self.file_bytes = file_bytes
        self.ranges = []
        self.urls = []

    def _download(self, url, byte_range=None, maximum_bytes=None):
        self.urls.append(url)
        if url.endswith(".idx"):
            return self.index_text.encode("ascii")
        self.ranges.append(byte_range)
        start, end = byte_range
        return self.file_bytes[start : end + 1]


class FakeEccodes:
    def __init__(self, data_date=19500101):
        self.data_date = data_date
        self.released = False
        self.latitudes = np.repeat(np.linspace(-89.5, 89.5, 256), 512)
        self.longitudes = np.tile(np.linspace(0.0, 359.296875, 512), 256)

    def codes_new_from_message(self, payload):
        return object()

    def codes_get(self, handle, key):
        return {
            "shortName": "avg_2t",
            "units": "K",
            "gridType": "regular_gg",
            "typeOfLevel": "heightAboveGround",
            "level": 2,
            "dataDate": self.data_date,
            "stepType": "avg",
            "typeOfStatisticalProcessing": 0,
            "bitmapPresent": 0,
        }[key]

    def codes_get_values(self, handle):
        return np.full(512 * 256, 280.0)

    def codes_get_array(self, handle, key):
        return self.latitudes if key == "latitudes" else self.longitudes

    def codes_release(self, handle):
        self.released = True


class NOAAcoreTests(unittest.TestCase):
    def test_index_parser_assigns_message_ends(self):
        records = noaa_core.parse_grib_index(
            "1:0:first\n2:8:second\n3:16:third\n"
        )

        self.assertEqual(records[0], noaa_core.GribRecord(1, 0, 7, "1:0:first"))
        self.assertEqual(records[1].end, 15)
        self.assertIsNone(records[2].end)

    def test_adjacent_selected_records_use_one_byte_range(self):
        message = b"GRIB7777"
        index_text = "\n".join(
            (
                "1:0:OTHER",
                "2:8:MINIMUM",
                "3:16:MAXIMUM",
                "4:24:TRAILER",
            )
        )
        client = FakeDownloadClient(index_text, message * 4)

        payloads = client.records(
            "https://storage.googleapis.com/example",
            {"temp_min": ("MINIMUM",), "temp_max": ("MAXIMUM",)},
        )

        self.assertEqual(payloads, {"temp_min": message, "temp_max": message})
        self.assertEqual(client.ranges, [(8, 23)])
        self.assertTrue(client.urls[-1].endswith(".grb"))

    def test_decoder_validates_the_encoded_data_date(self):
        eccodes = FakeEccodes(data_date=19500101)
        decoder = noaa_core.EccodesDecoder(eccodes_module=eccodes)

        with self.assertRaisesRegex(noaa_core.CoreDecodeError, "19500101"):
            decoder.decode(
                b"message",
                "temp_mean",
                expected_date=date(1950, 2, 1),
            )

        self.assertTrue(eccodes.released)

    def test_canonical_sampler_wraps_the_dateline(self):
        latitudes = np.repeat(np.array([-80.0, 0.0, 80.0]), 4)
        longitudes = np.tile(np.array([0.0, 90.0, 180.0, 270.0]), 3)
        values = latitudes * 1000 + longitudes
        field = noaa_core.GridField(
            values=values,
            latitudes=latitudes,
            longitudes=longitudes,
            short_name="2t",
            units="K",
            grid_type="regular_gg",
        )

        sampled = noaa_core.sample_canonical(field)

        self.assertEqual(sampled.shape, (91, 91))
        self.assertEqual(sampled[0, 0], -80_000 + 180)
        self.assertEqual(sampled[0, -1], sampled[0, 0])
        self.assertEqual(sampled[45, 45], 0)

    def test_month_loader_uses_daily_extrema_and_monthly_mean_precip(self):
        archive = FakeArchive()

        data = noaa_core.load_core_month(
            date(2024, 2, 1),
            archive=archive,
            decoder=FakeDecoder(),
        )

        self.assertEqual(archive.daily_calls, 29)
        self.assertTrue(np.allclose(data.temp_mean, 6.85))
        self.assertTrue(np.allclose(data.temp_min, 275.0 - 2.9 - 273.15))
        self.assertTrue(np.allclose(data.temp_max, 285.0 + 2.9 - 273.15))
        self.assertTrue(np.allclose(data.precip, 2.0))
        self.assertEqual(len(list(data.rows())), 91 * 91)

    def test_validation_rejects_inconsistent_temperature_order(self):
        shape = (91, 91)
        data = noaa_core.CoreMonthData(
            date(1950, 1, 1),
            temp_mean=np.full(shape, 10.0),
            temp_max=np.full(shape, 5.0),
            temp_min=np.full(shape, 0.0),
            precip=np.full(shape, 1.0),
        )

        with self.assertRaises(noaa_core.CoreDecodeError):
            noaa_core.validate_core_month(data)


if __name__ == "__main__":
    unittest.main()
