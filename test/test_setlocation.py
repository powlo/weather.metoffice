import os
import shutil
from unittest import TestCase
from unittest.mock import Mock, patch

import setlocation
from metoffice import constants

TEST_FOLDER = os.path.dirname(__file__)
RESULTS_FOLDER = os.path.join(TEST_FOLDER, "results")
DATA_FOLDER = os.path.join(TEST_FOLDER, "data")
FORECASTSITELIST = os.path.join(DATA_FOLDER, "forecastsitelist.json")
GEOIP = os.path.join(DATA_FOLDER, "ip-api.json")


def mock_get(url, callback):
    if url == constants.FORECAST_SITELIST_URL:
        return FORECASTSITELIST
    elif url == constants.GEOIP_PROVIDER["url"]:
        return GEOIP
    elif url == "www.bad-geo.com":
        return os.path.join(DATA_FOLDER, "bad-geo.json")
    else:
        return None


def mock_getSetting(id: str):
    settings = {"GeoLocation": "true", "GeoIPProvider": "0"}
    return settings.get(id)


class TestSetLocation(TestCase):
    def setUp(self):
        super(TestSetLocation, self).setUp()
        # create a disposable area for testing
        try:
            os.mkdir(RESULTS_FOLDER)
        except OSError:
            pass

        self.settings = {
            "ApiKey": "12345",
            "GeoLocation": "true",
            "GeoIPProvider": "0",
            "ForecastLocation": "CAMBRIDGE NIAB",
            "ForecastLocationID": "99123",
            "ForecastLocationLatitude": "52.245",
            "ForecastLocationLongitude": "0.103",
            "ObservationLocation": "BEDFORD",
            "ObservationLocationID": "3560",
        }

    @patch("metoffice.urlcache.URLCache")
    @patch("setlocation.addon")
    def test_getsitelist_without_geolocation(self, mock_addon, mock_cache):
        # Assumes a call to addon.getSetting("GeoLocation")
        mock_addon.getSetting.return_value = "false"
        mock_cache.return_value.__enter__.return_value.get = Mock(side_effect=mock_get)
        # Same request for forecast location, but with geolocation off
        result = setlocation.getsitelist.__wrapped__("ForecastLocation", "Cairnwell")
        expected = [
            {
                "elevation": "933.0",
                "name": "Cairnwell",
                "region": "ta",
                "longitude": "-3.42",
                "display": "Cairnwell",
                "nationalPark": "Cairngorms National Park",
                "latitude": "56.879",
                "unitaryAuthArea": "Perth and Kinross",
                "id": "3072",
            }
        ]
        self.assertEqual(expected, result)

    @patch("setlocation.addon")
    @patch("setlocation.dialog")
    @patch("setlocation.xbmc.Keyboard")
    @patch("metoffice.urlcache.URLCache")
    @patch("setlocation.API_KEY", "123abc")
    def test_main(self, mock_cache, mock_keyboard, mock_dialog, mock_addon):
        # Pontpandy shouldn't be found, and a message should be displayed saying so
        mock_cache.return_value.__enter__.return_value.get = Mock(side_effect=mock_get)
        mock_keyboard.return_value.getText = Mock(return_value="Pontypandy")
        mock_keyboard.return_value.isConfirmed = Mock(return_value=True)
        setlocation.main("ForecastLocation")
        # Assume OK message is 'not found'.
        self.assertTrue(mock_dialog.ok.called)

        # Rosehearty Samos should be found given search text 'hearty'
        mock_keyboard.return_value.getText = Mock(return_value="hearty")
        mock_dialog.select = Mock(return_value=0)
        setlocation.main("ForecastLocation")
        self.assertTrue(mock_dialog.select.called)
        expected = [
            (("ForecastLocation", "Rosehearty Samos"),),
            (("ForecastLocationID", "3094"),),
            (("ForecastLocationLatitude", "57.698"),),
            (("ForecastLocationLongitude", "-2.121"),),
        ]
        self.assertEqual(expected, mock_addon.setSetting.call_args_list)

    def tearDown(self):
        super(TestSetLocation, self).tearDown()
        shutil.rmtree(RESULTS_FOLDER)
