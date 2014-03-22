import os
import shutil
from xbmctestcase import XBMCTestCase

from mock import Mock, patch

TEST_FOLDER = os.path.dirname(__file__)
RESULTS_FOLDER = os.path.join(TEST_FOLDER, 'results')
DATA_FOLDER = os.path.join(TEST_FOLDER, 'data')
FORECASTSITELIST = os.path.join(DATA_FOLDER, 'forecastsitelist.json')
TEXTSITELIST = os.path.join(DATA_FOLDER, 'textsitelist.json')
GEOIP = os.path.join(DATA_FOLDER, 'ip-api.json')

class TestSetLocation(XBMCTestCase):    
    def setUp(self):
        super(TestSetLocation, self).setUp()
        #create a disposable area for testing
        try:
            os.mkdir(RESULTS_FOLDER)
        except OSError:
            pass

        self.xbmc.translatePath.return_value = RESULTS_FOLDER
        addon = self.xbmcaddon.Addon.return_value
        addon.getSetting.side_effect = self.mock_getSetting

        from metoffice.urlcache import URLCache
        self.URLCache = URLCache
        from metoffice import constants
        self.constants = constants
        from metoffice import setlocation
        self.setlocation = setlocation
        from metoffice import jsonparser
        self.jsonparser = jsonparser

    def mock_getSetting(self, s):
        return {'ApiKey' : '12345',
         'GeoIPProvider' : '0'}[s]

    def mock_get(self, url, callback):
        if url == self.constants.FORECAST_SITELIST_URL.format(key=self.constants.API_KEY):
            return FORECASTSITELIST
        elif url == self.constants.GEOIP_PROVIDER['url']:
            return GEOIP
        else:
            return None

    def test_noapikey(self):
        #need to mock out cache otherwise exception is due to json value error
        self.constants.API_KEY = ''
        self.assertRaises(Exception, self.setlocation.main('ForecastLocation'))

    def test_main(self):
        #Check dialog "No locations found"
        with patch('metoffice.setlocation.urlcache.URLCache') as mock_class:
            #we should actually just create and populate a test cache.
            mock_class.return_value.__enter__.return_value.get = Mock(side_effect=self.mock_get)
            self.xbmc.Keyboard.return_value.getText = Mock(return_value='Pontypandy')
            self.xbmc.Keyboard.return_value.isConfirmed = Mock(return_value=True)
            self.setlocation.main('ForecastLocation')
            self.assertTrue(self.xbmcgui.Dialog.return_value.ok.called)
    
            self.xbmc.Keyboard.return_value.getText = Mock(return_value='hearty')

            self.xbmcgui.Dialog.return_value.select = Mock(return_value = 0)
            self.setlocation.main('ForecastLocation')
            self.assertTrue(self.xbmcgui.Dialog.return_value.select.called)
            expected = [(('ForecastLocation', 'Rosehearty Samos'),),
                       (('ForecastLocationID', '3094'),),
                       (('ForecastLocationLatitude', '57.698'),),
                       (('ForecastLocationLongitude', '-2.121'),)]
            self.assertEqual(expected, self.xbmcaddon.Addon.return_value.setSetting.call_args_list)

    def tearDown(self):
        super(TestSetLocation, self).tearDown()
        shutil.rmtree(RESULTS_FOLDER)