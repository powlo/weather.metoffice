import datetime
import os
import shutil
from unittest import TestCase
from unittest.mock import Mock, call, patch

import xbmc

from metoffice import constants, properties

TEST_FOLDER = os.path.dirname(__file__)
DATA_FOLDER = os.path.join(TEST_FOLDER, "data")
RESULTS_FOLDER = os.path.join(TEST_FOLDER, "results")
OBSERVATIONHOURLY = os.path.join(DATA_FOLDER, "observationhourly.json")
OBSERVATIONHOURLY2 = os.path.join(DATA_FOLDER, "observationhourly2.json")
FORECASTDAILY = os.path.join(DATA_FOLDER, "forecastdaily.json")
FORECAST3HOURLY = os.path.join(DATA_FOLDER, "forecast3hourly.json")
FORECASTTEXT = os.path.join(DATA_FOLDER, "forecasttext.json")
FORECASTLAYERCAPABILITIES = os.path.join(DATA_FOLDER, "forecastlayercapabilities.json")
OBSERVATIONLAYERCAPABILITIES = os.path.join(
    DATA_FOLDER, "observationlayercapabilities.json"
)
CORRUPTFORECASTLAYERCAPABILITIES = os.path.join(
    DATA_FOLDER, "corruptforecastlayercapabilities.json"
)
CORRUPTOBSERVATIONLAYERCAPABILITIES = os.path.join(
    DATA_FOLDER, "corruptobservationlayercapabilities.json"
)
FORECASTSITELIST = os.path.join(DATA_FOLDER, "forecastsitelist.json")
TEXTSITELIST = os.path.join(DATA_FOLDER, "textsitelist.json")
GEOIP = os.path.join(DATA_FOLDER, "ip-api.json")
EMPTY_FILE = os.path.join(DATA_FOLDER, "empty.json")


def mock_get_region(id):
    region_settings = {"tempunit": "C"}
    return region_settings[id]


class Addon:
    # Move to a dedicated mocks package.
    def __init__(self, settings):
        if settings is None:
            settings = {}
        self._settings = settings

    def getSetting(self, key):
        return self._settings[key]

    def setSetting(self, key, value):
        self._settings[key] = value


class Window:
    # Create a thing that behaves like xbmcgui.Window.
    def __init__(self, properties):
        if properties is None:
            properties = {}
        self._properties = properties

    def getProperty(self, key):
        return self._properties.get(key)

    def setProperty(self, key, value):
        self._properties[key] = value

    def clearProperty(self, key):
        self._properties.pop(key, None)


class TestProperties(TestCase):
    def setUp(self):
        super(TestProperties, self).setUp()

        # Use the patch start/stop mechanism so that we don't have to
        # pass in a mock object to every test.
        # See https://docs.python.org/3/library/unittest.mock-examples.html#applying-the-same-patch-to-every-test-method

        def mock_window():
            return Window(
                {
                    "ForecastMap.LayerSelection": "Rainfall",
                    "ObservationMap.LayerSelection": "Rainfall",
                    "ForecastMap.Slider": "0",
                    "ObservationMap.Slider": "0",
                    "Weather.CurrentView": "Doesnt matter",
                }
            )

        window_patcher = patch("metoffice.properties.window", new=mock_window)
        self.addCleanup(window_patcher.stop)
        window_patcher.start()

        def mock_addon():
            return Addon(
                {
                    "ApiKey": "12345",
                    "GeoLocation": "true",
                    "GeoIPProvider": "0",
                    "ForecastLocation": "CAMBRIDGE NIAB",
                    "ForecastLocationID": "99123",
                    "ForecastLocationLatitude": "52.245",
                    "ForecastLocationLongitude": "0.103",
                    "ObservationLocation": "BEDFORD",
                    "ObservationLocationID": "3560",
                    "RegionalLocation": "Wales",
                    "RegionalLocationID": "516",
                }
            )

        addon_patcher = patch("metoffice.constants.addon", new=mock_addon)
        self.addCleanup(addon_patcher.stop)
        addon_patcher.start()

        xbmc.getRegion = Mock(side_effect=mock_get_region)

        # create a disposable area for testing
        try:
            os.mkdir(RESULTS_FOLDER)
        except OSError:
            pass

    def mock_get(self, url, expiry_callback, resource_callback=None):
        cache = {
            constants.FORECAST_SITELIST_URL: FORECASTSITELIST,
            constants.DAILY_LOCATION_FORECAST_URL: FORECASTDAILY,
            constants.THREEHOURLY_LOCATION_FORECAST_URL: FORECAST3HOURLY,
            constants.FORECAST_LAYER_CAPABILITIES_URL: FORECASTLAYERCAPABILITIES,
            constants.OBSERVATION_LAYER_CAPABILITIES_URL: OBSERVATIONLAYERCAPABILITIES,
            constants.TEXT_FORECAST_URL: FORECASTTEXT,
            constants.HOURLY_LOCATION_OBSERVATION_URL: OBSERVATIONHOURLY,
            constants.GEOIP_PROVIDER["url"]: GEOIP,
        }
        return cache[url]

    @patch("metoffice.urlcache.URLCache")
    @patch("metoffice.properties.window")
    def test_observation(self, mock_window, mock_cache):
        mock_cache.return_value.__enter__.return_value.get = Mock(
            side_effect=self.mock_get
        )

        properties.observation()
        self.assertTrue(
            call("HourlyObservation.IssuedAt", "17:00 Thu 06 Mar 2014")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Current.Condition", "Cloudy")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Current.Visibility", "45000")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Current.Pressure", "1021")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Current.Temperature", "10")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Current.Wind", "23.0")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Current.WindDirection", "SW")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Current.WindGust", "n/a")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Current.OutlookIcon", "26.png")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Current.OutlookIcon", "26.png")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Current.DewPoint", "6")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Current.Humidity", "79")
            in mock_window.return_value.setProperty.call_args_list
        )

    @patch("metoffice.urlcache.URLCache")
    @patch("metoffice.properties.window")
    def test_observation_missing(self, mock_window, mock_cache):
        # Test the cases when reports don't contain list items.
        mock_cache.return_value.__enter__.return_value.get = Mock(
            return_value=OBSERVATIONHOURLY2
        )

        properties.observation()
        self.assertTrue(
            call("HourlyObservation.IssuedAt", "17:00 Thu 06 Mar 2014")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Current.Condition", "Sunny")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Current.Visibility", "45000")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Current.Pressure", "1021")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Current.Temperature", "10")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Current.Wind", "16.0")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Current.WindDirection", "WSW")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Current.WindGust", "n/a")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Current.OutlookIcon", "32.png")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Current.FanartCode", "32.png")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Current.DewPoint", "4")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Current.Humidity", "66")
            in mock_window.return_value.setProperty.call_args_list
        )

        # Test exception handling when given json without proper keys
        mock_cache.return_value.__enter__.return_value.get = Mock(
            return_value=EMPTY_FILE
        )
        with self.assertRaises(KeyError) as cm:
            properties.observation()
        self.assertEqual(
            (
                "Key Error in JSON File",
                "Key 'SiteRep' not found while processing file from url:",
                constants.HOURLY_LOCATION_OBSERVATION_URL,
            ),
            cm.exception.args,
        )

    @patch("metoffice.utilities.TEMPERATUREUNITS", "C")
    @patch("metoffice.urlcache.URLCache")
    @patch("metoffice.properties.window")
    def test_daily(self, mock_window, mock_cache):
        mock_cache.return_value.__enter__.return_value.get = Mock(
            side_effect=self.mock_get
        )

        properties.daily()
        self.assertTrue(
            call("DailyForecast.IssuedAt", "14:00 Mon 24 Feb 2014")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Day0.Title", "Mon")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Day0.HighTemp", "13")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Day0.LowTemp", "7")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Day0.WindSpeed", "13")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Day0.WindDirection", "ssw")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Day0.Outlook", "Light Rain")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Day0.OutlookIcon", "11.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Day1.Title", "Tue")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Day1.HighTemp", "12")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Day1.LowTemp", "3")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Day1.WindSpeed", "18")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Day1.WindDirection", "ssw")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Day1.Outlook", "Sunny")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Day1.OutlookIcon", "32.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Day2.Title", "Wed")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Day2.HighTemp", "11")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Day2.LowTemp", "4")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Day2.WindSpeed", "13")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Day2.WindDirection", "wsw")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Day2.Outlook", "Sunny")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Day2.OutlookIcon", "32.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Day3.Title", "Thu")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Day3.HighTemp", "11")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Day3.LowTemp", "3")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Day3.WindSpeed", "16")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Day3.WindDirection", "wsw")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Day3.Outlook", "Heavy Rain")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Day3.OutlookIcon", "40.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Day4.Title", "Fri")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Day4.HighTemp", "9")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Day4.LowTemp", "2")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Day4.WindSpeed", "11")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Day4.WindDirection", "sw")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Day4.Outlook", "Light Rain")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Day4.OutlookIcon", "11.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        # Test exception handling when given json without proper keys
        mock_cache.return_value.__enter__.return_value.get = Mock(
            return_value=EMPTY_FILE
        )
        with self.assertRaises(KeyError) as cm:
            properties.daily()
        self.assertEqual(
            (
                "Key Error in JSON File",
                "Key 'SiteRep' not found while processing file from url:",
                constants.DAILY_LOCATION_FORECAST_URL,
            ),
            cm.exception.args,
        )

    @patch("metoffice.utilities.TEMPERATUREUNITS", "C")
    @patch("metoffice.urlcache.URLCache")
    @patch("metoffice.properties.window")
    def test_threehourly(self, mock_window, mock_cache):
        # This test is a bit long and cumbersome. TODO: Figure out how to cut it down.
        mock_cache.return_value.__enter__.return_value.get = Mock(
            side_effect=self.mock_get
        )

        properties.threehourly()
        self.assertTrue(
            call("3HourlyForecast.IssuedAt", "16:00 Sat 01 Mar 2014")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.1.Time", "12:00")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.1.Temperature", "6")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.1.FeelsLikeTemp", "4")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.1.WindSpeed", "4")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.1.WindDirection", "nnw")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.1.GustSpeed", "7")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.1.UVIndex", "1")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.1.Precipitation", "6%")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.1.Outlook", "Cloudy")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.1.OutlookIcon", "26.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Hourly.2.Time", "15:00")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.2.Temperature", "8")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.2.FeelsLikeTemp", "6")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.2.WindSpeed", "7")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.2.WindDirection", "wsw")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.2.GustSpeed", "11")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.2.UVIndex", "1")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.2.Precipitation", "6%")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.2.Outlook", "Cloudy")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.2.OutlookIcon", "26.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Hourly.3.Time", "18:00")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.3.Temperature", "6")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.3.FeelsLikeTemp", "5")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.3.WindSpeed", "2")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.3.WindDirection", "wsw")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.3.GustSpeed", "7")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.3.UVIndex", "0")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.3.Precipitation", "5%")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.3.Outlook", "Cloudy")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.3.OutlookIcon", "26.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Hourly.4.Time", "21:00")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.4.Temperature", "5")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.4.FeelsLikeTemp", "3")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.4.WindSpeed", "4")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.4.WindDirection", "ssw")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.4.GustSpeed", "9")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.4.UVIndex", "0")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.4.Precipitation", "0%")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.4.Outlook", "Clear")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.4.OutlookIcon", "31.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Hourly.5.Time", "00:00")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.5.Temperature", "3")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.5.FeelsLikeTemp", "1")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.5.WindSpeed", "7")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.5.WindDirection", "ssw")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.5.GustSpeed", "16")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.5.UVIndex", "0")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.5.Precipitation", "3%")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.5.Outlook", "Clear")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.5.OutlookIcon", "31.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Hourly.6.Time", "03:00")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.6.Temperature", "3")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.6.FeelsLikeTemp", "0")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.6.WindSpeed", "9")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.6.WindDirection", "ssw")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.6.GustSpeed", "20")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.6.UVIndex", "0")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.6.Precipitation", "5%")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.6.Outlook", "Clear")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.6.OutlookIcon", "31.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Hourly.7.Time", "06:00")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.7.Temperature", "4")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.7.FeelsLikeTemp", "0")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.7.WindSpeed", "11")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.7.WindDirection", "ssw")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.7.GustSpeed", "25")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.7.UVIndex", "0")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.7.Precipitation", "8%")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.7.Outlook", "Cloudy")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.7.OutlookIcon", "26.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Hourly.8.Time", "09:00")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.8.Temperature", "6")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.8.FeelsLikeTemp", "3")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.8.WindSpeed", "13")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.8.WindDirection", "ssw")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.8.GustSpeed", "25")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.8.UVIndex", "1")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.8.Precipitation", "5%")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.8.Outlook", "Cloudy")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.8.OutlookIcon", "26.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Hourly.9.Time", "12:00")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.9.Temperature", "9")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.9.FeelsLikeTemp", "5")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.9.WindSpeed", "18")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.9.WindDirection", "s")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.9.GustSpeed", "31")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.9.UVIndex", "1")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.9.Precipitation", "5%")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.9.Outlook", "Cloudy")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.9.OutlookIcon", "26.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Hourly.10.Time", "15:00")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.10.Temperature", "9")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.10.FeelsLikeTemp", "5")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.10.WindSpeed", "20")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.10.WindDirection", "s")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.10.GustSpeed", "36")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.10.UVIndex", "1")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.10.Precipitation", "31%")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.10.Outlook", "Cloudy")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.10.OutlookIcon", "26.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Hourly.11.Time", "18:00")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.11.Temperature", "8")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.11.FeelsLikeTemp", "3")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.11.WindSpeed", "20")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.11.WindDirection", "s")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.11.GustSpeed", "38")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.11.UVIndex", "0")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.11.Precipitation", "95%")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.11.Outlook", "Heavy Rain")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.11.OutlookIcon", "40.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Hourly.12.Time", "21:00")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.12.Temperature", "7")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.12.FeelsLikeTemp", "3")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.12.WindSpeed", "16")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.12.WindDirection", "s")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.12.GustSpeed", "29")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.12.UVIndex", "0")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.12.Precipitation", "96%")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.12.Outlook", "Heavy Rain")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.12.OutlookIcon", "40.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Hourly.13.Time", "00:00")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.13.Temperature", "5")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.13.FeelsLikeTemp", "1")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.13.WindSpeed", "13")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.13.WindDirection", "wsw")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.13.GustSpeed", "22")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.13.UVIndex", "0")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.13.Precipitation", "54%")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.13.Outlook", "Light Rain")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.13.OutlookIcon", "11.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Hourly.14.Time", "03:00")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.14.Temperature", "3")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.14.FeelsLikeTemp", "-1")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.14.WindSpeed", "11")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.14.WindDirection", "ssw")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.14.GustSpeed", "18")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.14.UVIndex", "0")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.14.Precipitation", "13%")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.14.Outlook", "Clear")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.14.OutlookIcon", "31.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Hourly.15.Time", "06:00")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.15.Temperature", "2")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.15.FeelsLikeTemp", "-2")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.15.WindSpeed", "11")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.15.WindDirection", "s")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.15.GustSpeed", "20")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.15.UVIndex", "0")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.15.Precipitation", "5%")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.15.Outlook", "Cloudy")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.15.OutlookIcon", "26.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Hourly.16.Time", "09:00")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.16.Temperature", "5")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.16.FeelsLikeTemp", "1")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.16.WindSpeed", "11")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.16.WindDirection", "s")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.16.GustSpeed", "22")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.16.UVIndex", "1")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.16.Precipitation", "33%")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.16.Outlook", "Light Rain")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.16.OutlookIcon", "11.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Hourly.17.Time", "12:00")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.17.Temperature", "7")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.17.FeelsLikeTemp", "4")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.17.WindSpeed", "11")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.17.WindDirection", "s")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.17.GustSpeed", "22")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.17.UVIndex", "1")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.17.Precipitation", "65%")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.17.Outlook", "Heavy Rain")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.17.OutlookIcon", "40.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Hourly.18.Time", "15:00")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.18.Temperature", "7")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.18.FeelsLikeTemp", "4")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.18.WindSpeed", "7")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.18.WindDirection", "ssw")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.18.GustSpeed", "16")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.18.UVIndex", "1")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.18.Precipitation", "48%")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.18.Outlook", "Light Rain")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.18.OutlookIcon", "11.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Hourly.19.Time", "18:00")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.19.Temperature", "5")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.19.FeelsLikeTemp", "3")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.19.WindSpeed", "7")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.19.WindDirection", "wsw")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.19.GustSpeed", "11")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.19.UVIndex", "0")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.19.Precipitation", "46%")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.19.Outlook", "Light Rain")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.19.OutlookIcon", "45.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Hourly.20.Time", "21:00")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.20.Temperature", "4")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.20.FeelsLikeTemp", "1")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.20.WindSpeed", "9")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.20.WindDirection", "w")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.20.GustSpeed", "13")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.20.UVIndex", "0")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.20.Precipitation", "13%")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.20.Outlook", "Cloudy")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.20.OutlookIcon", "26.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Hourly.21.Time", "00:00")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.21.Temperature", "3")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.21.FeelsLikeTemp", "0")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.21.WindSpeed", "9")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.21.WindDirection", "wnw")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.21.GustSpeed", "18")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.21.UVIndex", "0")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.21.Precipitation", "2%")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.21.Outlook", "Partly Cloudy")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.21.OutlookIcon", "29.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Hourly.22.Time", "03:00")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.22.Temperature", "3")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.22.FeelsLikeTemp", "-1")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.22.WindSpeed", "9")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.22.WindDirection", "wnw")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.22.GustSpeed", "18")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.22.UVIndex", "0")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.22.Precipitation", "2%")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.22.Outlook", "Partly Cloudy")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.22.OutlookIcon", "29.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Hourly.23.Time", "06:00")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.23.Temperature", "2")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.23.FeelsLikeTemp", "-1")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.23.WindSpeed", "9")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.23.WindDirection", "w")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.23.GustSpeed", "16")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.23.UVIndex", "0")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.23.Precipitation", "2%")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.23.Outlook", "Partly Cloudy")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.23.OutlookIcon", "29.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Hourly.24.Time", "09:00")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.24.Temperature", "5")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.24.FeelsLikeTemp", "2")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.24.WindSpeed", "11")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.24.WindDirection", "w")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.24.GustSpeed", "20")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.24.UVIndex", "1")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.24.Precipitation", "6%")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.24.Outlook", "Partly Cloudy")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.24.OutlookIcon", "30.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Hourly.25.Time", "12:00")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.25.Temperature", "8")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.25.FeelsLikeTemp", "5")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.25.WindSpeed", "11")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.25.WindDirection", "w")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.25.GustSpeed", "22")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.25.UVIndex", "1")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.25.Precipitation", "7%")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.25.Outlook", "Partly Cloudy")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.25.OutlookIcon", "30.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Hourly.26.Time", "15:00")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.26.Temperature", "8")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.26.FeelsLikeTemp", "6")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.26.WindSpeed", "11")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.26.WindDirection", "w")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.26.GustSpeed", "18")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.26.UVIndex", "1")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.26.Precipitation", "10%")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.26.Outlook", "Sunny")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.26.OutlookIcon", "32.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Hourly.27.Time", "18:00")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.27.Temperature", "6")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.27.FeelsLikeTemp", "4")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.27.WindSpeed", "7")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.27.WindDirection", "wsw")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.27.GustSpeed", "11")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.27.UVIndex", "0")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.27.Precipitation", "8%")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.27.Outlook", "Clear")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.27.OutlookIcon", "31.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Hourly.28.Time", "21:00")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.28.Temperature", "5")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.28.FeelsLikeTemp", "2")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.28.WindSpeed", "7")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.28.WindDirection", "sw")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.28.GustSpeed", "13")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.28.UVIndex", "0")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.28.Precipitation", "11%")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.28.Outlook", "Partly Cloudy")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.28.OutlookIcon", "29.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Hourly.29.Time", "00:00")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.29.Temperature", "4")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.29.FeelsLikeTemp", "1")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.29.WindSpeed", "9")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.29.WindDirection", "sw")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.29.GustSpeed", "16")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.29.UVIndex", "0")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.29.Precipitation", "16%")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.29.Outlook", "Cloudy")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.29.OutlookIcon", "26.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Hourly.30.Time", "03:00")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.30.Temperature", "4")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.30.FeelsLikeTemp", "1")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.30.WindSpeed", "9")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.30.WindDirection", "sw")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.30.GustSpeed", "16")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.30.UVIndex", "0")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.30.Precipitation", "23%")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.30.Outlook", "Cloudy")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.30.OutlookIcon", "26.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Hourly.31.Time", "06:00")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.31.Temperature", "4")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.31.FeelsLikeTemp", "1")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.31.WindSpeed", "11")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.31.WindDirection", "sw")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.31.GustSpeed", "20")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.31.UVIndex", "0")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.31.Precipitation", "24%")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.31.Outlook", "Overcast")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.31.OutlookIcon", "26.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Hourly.32.Time", "09:00")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.32.Temperature", "6")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.32.FeelsLikeTemp", "2")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.32.WindSpeed", "13")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.32.WindDirection", "wsw")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.32.GustSpeed", "29")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.32.UVIndex", "1")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.32.Precipitation", "55%")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.32.Outlook", "Light Rain")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.32.OutlookIcon", "11.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Hourly.33.Time", "12:00")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.33.Temperature", "8")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.33.FeelsLikeTemp", "3")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.33.WindSpeed", "18")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.33.WindDirection", "w")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.33.GustSpeed", "38")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.33.UVIndex", "1")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.33.Precipitation", "37%")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.33.Outlook", "Light Rain")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.33.OutlookIcon", "11.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Hourly.34.Time", "15:00")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.34.Temperature", "8")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.34.FeelsLikeTemp", "3")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.34.WindSpeed", "18")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.34.WindDirection", "w")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.34.GustSpeed", "36")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.34.UVIndex", "1")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.34.Precipitation", "14%")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.34.Outlook", "Partly Cloudy")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.34.OutlookIcon", "30.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Hourly.35.Time", "18:00")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.35.Temperature", "7")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.35.FeelsLikeTemp", "2")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.35.WindSpeed", "13")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.35.WindDirection", "w")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.35.GustSpeed", "27")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.35.UVIndex", "0")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.35.Precipitation", "6%")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.35.Outlook", "Partly Cloudy")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.35.OutlookIcon", "29.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Hourly.36.Time", "21:00")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.36.Temperature", "5")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.36.FeelsLikeTemp", "1")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.36.WindSpeed", "13")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.36.WindDirection", "wsw")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.36.GustSpeed", "25")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.36.UVIndex", "0")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.36.Precipitation", "7%")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.36.Outlook", "Partly Cloudy")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Hourly.36.OutlookIcon", "29.png")
            in mock_window.return_value.setProperty.call_args_list
        )

        # Test exception handling when given json without proper keys
        mock_cache.return_value.__enter__.return_value.get = Mock(
            return_value=EMPTY_FILE
        )
        with self.assertRaises(KeyError) as cm:
            properties.threehourly()
        self.assertEqual(
            (
                "Key Error in JSON File",
                "Key 'SiteRep' not found while processing file from url:",
                constants.THREEHOURLY_LOCATION_FORECAST_URL,
            ),
            cm.exception.args,
        )

    @patch("metoffice.properties.LATITUDE", "52.245")
    @patch("metoffice.properties.LONGITUDE", "0.103")
    @patch("metoffice.properties.window")
    def test_sunrise(self, mock_window):
        # We should change this (and all other tests) to just
        # verify the call to getProperty, not the behaviour
        # of getProperty, which is what we're doing.
        properties.sunrisesunset()
        self.assertTrue(mock_window.return_value.setProperty.called)

    @patch("metoffice.properties.urlcache.URLCache")
    @patch("metoffice.properties.window")
    def test_text(self, mock_window, mock_cache):
        mock_cache.return_value.__enter__.return_value.get = Mock(
            side_effect=self.mock_get
        )

        properties.text()
        self.assertTrue(
            call("TextForecast.IssuedAt", "16:00 Mon 24 Feb 2014")
            in mock_window.return_value.setProperty.call_args_list
        )

        self.assertTrue(
            call("Text.Paragraph0.Title", "Headline")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call(
                "Text.Paragraph0.Content",
                "Rain clearing eastwards, showers following, with increasing winds.",
            )
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Text.Paragraph1.Title", "This Evening and Tonight")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call(
                "Text.Paragraph1.Content",
                (
                    "Rain arriving in the far west around dusk will clear eastwards overnight, "
                    "this heaviest in the west and over high ground, where winds will also become "
                    "strong. Mild, with clear spells and scattered showers following. Minimum "
                    "Temperature 5C."
                ),
            )
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Text.Paragraph2.Title", "Tuesday")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call(
                "Text.Paragraph2.Content",
                (
                    "Some dry and bright weather is likely at times but also scattered blustery, "
                    "heavy showers. Remaining windy, especially around exposed coasts and hills "
                    "where gales are likely. Maximum Temperature 9C."
                ),
            )
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Text.Paragraph3.Title", "Wednesday to Friday")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call(
                "Text.Paragraph3.Content",
                (
                    "Sunny spells and lighter winds on Wednesday, some showers along the coast. "
                    "Wet and windy overnight, turning showery on Thursday and Friday, becoming "
                    "wintry over hills."
                ),
            )
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Text.Paragraph4.Title", "Saturday 1 Mar 2014 to Monday 10 Mar 2014")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call(
                "Text.Paragraph4.Content",
                (
                    "The weekend will start unsettled with showers or longer spells of rain, with "
                    "some heavier bursts at first. This will be most persistent in the far southeast "
                    "and far north, with a risk of hill snow in the north. There will be some drier "
                    "slots too, especially on Sunday with a risk of local frost and icy surfaces. "
                    "Temperatures near normal. Through the next week it will remain unsettled in "
                    "northern parts, with further rain or showers, and some hill snow. It will be "
                    "mainly dry but fairly cloudy towards the south with isolated patchy frost. "
                    "During the middle part of the week rain may spread southwards for a time, "
                    "before turning wet and windy in the northwest again later, with a risk of gales."
                ),
            )
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call("Text.Paragraph5.Title", "Tuesday 11 Mar 2014 to Tuesday 25 Mar 2014")
            in mock_window.return_value.setProperty.call_args_list
        )
        self.assertTrue(
            call(
                "Text.Paragraph5.Content",
                (
                    "Current indications suggest a more typically unsettled pattern across the "
                    "United Kingdom through much of March. Through this period we can expect to "
                    "see fairly average conditions, which would mean spells of wet and windy "
                    "weather, mostly in the north and west, but still some decent sunny spells "
                    "in between. The best of the drier, brighter conditions is most likely in the "
                    "south and east of the UK. Temperatures are likely to be around average, which "
                    "may lead to more frequent incidences of frost compared to recent weeks."
                ),
            )
            in mock_window.return_value.setProperty.call_args_list
        )

        # Test exception handling when given json without proper keys
        mock_cache.return_value.__enter__.return_value.get = Mock(
            return_value=EMPTY_FILE
        )
        with self.assertRaises(KeyError) as cm:
            properties.text()
        self.assertEqual(
            (
                "Key Error in JSON File",
                "Key 'RegionalFcst' not found while processing file from url:",
                constants.TEXT_FORECAST_URL,
            ),
            cm.exception.args,
        )

    @patch("metoffice.urlcache.URLCache")
    def test_daily_expiry(self, mock_cache):
        mock_cache.return_value.__enter__.return_value.get = Mock(
            side_effect=self.mock_get
        )

        result = properties.daily_expiry(FORECASTDAILY)
        self.assertEqual(datetime.datetime(2014, 2, 24, 15, 30), result)

    @patch("metoffice.urlcache.URLCache")
    def test_threehourly_expiry(self, mock_cache):
        mock_cache.return_value.__enter__.return_value.get = Mock(
            side_effect=self.mock_get
        )

        result = properties.threehourly_expiry(FORECAST3HOURLY)
        self.assertEqual(datetime.datetime(2014, 3, 1, 17, 30), result)

    @patch("metoffice.urlcache.URLCache")
    def test_text_expiry(self, mock_cache):
        mock_cache.return_value.__enter__.return_value.get = Mock(
            side_effect=self.mock_get
        )

        result = properties.text_expiry(FORECASTTEXT)
        self.assertEqual(datetime.datetime(2014, 2, 25, 4, 0), result)

    @patch("metoffice.urlcache.URLCache")
    def test_observation_expiry(self, mock_cache):
        mock_cache.return_value.__enter__.return_value.get = Mock(
            side_effect=self.mock_get
        )

        result = properties.observation_expiry(OBSERVATIONHOURLY)
        self.assertEqual(datetime.datetime(2014, 3, 6, 18, 30), result)

    def tearDown(self):
        super(TestProperties, self).tearDown()
        shutil.rmtree(RESULTS_FOLDER)
