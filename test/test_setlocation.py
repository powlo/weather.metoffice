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
REGIONALSITELIST = os.path.join(DATA_FOLDER, "regionalsitelist.json")
GEOIP = os.path.join(DATA_FOLDER, "ip-api.json")


def mock_get(url, callback):
    if url == constants.FORECAST_SITELIST_URL:
        return FORECASTSITELIST
    elif url == constants.REGIONAL_SITELIST_URL:
        return REGIONALSITELIST
    elif url == constants.GEOIP_PROVIDER["url"]:
        return GEOIP
    elif url == "www.bad-geo.com":
        return os.path.join(DATA_FOLDER, "bad-geo.json")
    else:
        return None


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
            "RegionalLocation": "Wales",
            "RegionalLocationID": "516",
        }

    @patch("metoffice.urlcache.URLCache")
    @patch("setlocation.GEOLOCATION", "true")
    def test_getsitelist_with_geolocation(self, mock_cache):
        mock_cache.return_value.__enter__.return_value.get = Mock(side_effect=mock_get)
        # Get Regional sitelist
        result = setlocation.getsitelist.__wrapped__(
            "RegionalLocation", "Northeast England"
        )
        expected = [
            {"display": "Northeast England", "id": "508", "name": "Northeast England"}
        ]
        self.assertEqual(expected, result)

        # Get Forecast sitelist
        result = setlocation.getsitelist.__wrapped__("ForecastLocation", "Cairnwell")
        expected = [
            {
                "distance": 640,
                "elevation": "933.0",
                "name": "Cairnwell",
                "region": "ta",
                "longitude": "-3.42",
                "display": "Cairnwell (640km)",
                "nationalPark": "Cairngorms National Park",
                "latitude": "56.879",
                "unitaryAuthArea": "Perth and Kinross",
                "id": "3072",
            }
        ]
        self.assertEqual(expected, result)

    @patch("metoffice.urlcache.URLCache")
    @patch("setlocation.GEOLOCATION", "false")
    def test_getsitelist_without_geolocation(self, mock_cache):
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

    @patch("metoffice.urlcache.URLCache")
    @patch("setlocation.GEOLOCATION", "true")
    @patch("setlocation.GEOIP_PROVIDER", {"url": "www.bad-geo.com"})
    def test_getsitelist_bad_provider(self, mock_cache):
        mock_cache.return_value.__enter__.return_value.get = Mock(side_effect=mock_get)
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
    @patch("setlocation.keyboard")
    @patch("metoffice.urlcache.URLCache")
    def test_main(self, mock_cache, mock_keyboard, mock_dialog, mock_addon):
        # Pontpandy shouldn't be found, and a message should be displayed saying so
        mock_cache.return_value.__enter__.return_value.get = Mock(side_effect=mock_get)
        mock_keyboard.return_value.getText = Mock(return_value="Pontypandy")
        mock_keyboard.return_value.isConfirmed = Mock(return_value=True)

        # Assume that main is decorated with failgracefully
        # get and test the wrapped function, sidestepping the decorator.
        setlocation.main.__wrapped__("ForecastLocation")
        self.assertTrue(mock_dialog.return_value.ok.called)

        # Rosehearty Samos should be found given search text 'hearty'
        mock_keyboard.return_value.getText = Mock(return_value="hearty")
        mock_dialog.return_value.select = Mock(return_value=0)
        setlocation.main.__wrapped__("ForecastLocation")
        self.assertTrue(mock_dialog.return_value.select.called)
        expected = [
            (("ForecastLocation", "Rosehearty Samos"),),
            (("ForecastLocationID", "3094"),),
            (("ForecastLocationLatitude", "57.698"),),
            (("ForecastLocationLongitude", "-2.121"),),
        ]
        self.assertEqual(expected, mock_addon.return_value.setSetting.call_args_list)

    def tearDown(self):
        super(TestSetLocation, self).tearDown()
        shutil.rmtree(RESULTS_FOLDER)
