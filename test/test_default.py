from unittest import TestCase
from unittest.mock import Mock, patch

import default


class TestMain(TestCase):
    @patch("default.properties")
    @patch("default.API_KEY", "12345")
    def test_simple(self, mock_properties):
        default.main.__wrapped__()
        self.assertTrue(mock_properties.observation.called)
        self.assertTrue(mock_properties.daily.called)
        self.assertTrue(mock_properties.threehourly.called)
        self.assertFalse(mock_properties.forecastlayer.called)
        self.assertFalse(mock_properties.observationlayer.called)
        self.assertFalse(mock_properties.text.called)

    @patch("default.properties")
    @patch("default._", Mock(side_effect=lambda x: x))
    @patch("default.API_KEY", "")
    def test_no_api_key(self, mock_properties):
        """When the user has not added an api key an exception should be raised."""
        # Assume here that the call to getSetting is for 'EraseCache'.
        mock_properties.ADDON.getSetting = Mock(return_value="false")

        # Test no API Key Exception raising
        with self.assertRaises(Exception) as cm:
            default.main.__wrapped__()
        self.assertEqual(
            (
                "No API Key.",
                "Enter your Met Office API Key under settings.",
            ),
            cm.exception.args,
        )
        self.assertFalse(mock_properties.observation.called)
        self.assertFalse(mock_properties.daily.called)
        self.assertFalse(mock_properties.threehourly.called)
        self.assertFalse(mock_properties.forecastlayer.called)
        self.assertFalse(mock_properties.observationlayer.called)
        self.assertFalse(mock_properties.text.called)
        mock_properties.reset_mock()

    @patch("default.properties", Mock())  # Stub out functions to speed up test.
    @patch("default.ADDON")
    @patch("default.API_KEY", "12345")
    @patch("default.urlcache.URLCache")
    def test_erase_cache(self, mock_urlcache, mock_addon):
        """
        If the EraseCache setting is true then we erase the
        cache and reset the value to false.
        """
        # Assume here that the call to getSetting is for 'EraseCache'.
        mock_addon.getSetting = Mock(return_value="true")
        default.main.__wrapped__()
        self.assertTrue(mock_urlcache.return_value.erase.called)
        mock_addon.setSetting.assert_called_once_with("EraseCache", "false")

    @patch("sys.argv", ["something", "ForecastLocation"])
    @patch("default.API_KEY", "12345")
    @patch("setlocation.main")
    @patch("default.properties", Mock())
    def test_setlocation(self, mock_setlocation_main):
        """
        When default is invoked with Location setting args, the
        setlocation script is run.
        """
        default.main.__wrapped__()
        self.assertTrue(mock_setlocation_main.called)
        self.assertEqual(mock_setlocation_main.call_args.args, ("ForecastLocation",))
