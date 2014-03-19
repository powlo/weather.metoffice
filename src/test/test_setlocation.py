import os
import shutil
import json
from xbmctestcase import XBMCTestCase

from mock import Mock, patch

TEST_FOLDER = os.path.dirname(__file__)
RESULTS_FOLDER = os.path.join(TEST_FOLDER, 'results')
DATA_FOLDER = os.path.join(TEST_FOLDER, 'data')
FORECASTSITELIST = os.path.join(DATA_FOLDER, 'forecastsitelist.json')
TEXTSITELIST = os.path.join(DATA_FOLDER, 'textsitelist.json')

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

        from metoffice import locator
        locator.distances = Mock(side_effect=self.mock_distances)
        from metoffice.urlcache import URLCache
        self.URLCache = URLCache
        from metoffice import constants
        self.constants = constants
        
    def mock_getSetting(self, s):
        return {'ApiKey' : '12345',
         'GeoIPProvider' : '0'}[s]
    
    def mock_distances(self, sitelist, n=0):
        for site in sitelist:
            site['distance'] = 10

    def test_noapikey(self):
        self.constants.API_KEY = ''
        from metoffice import setlocation #@UnusedImport
        self.assertRaises(Exception, setlocation.main('ForecastLocation'))

    #the fragility of this test probably indicates
    #a fragility in the target code.
    #TODO: Change code so that locator returns a list of distances, then zip them up with sitelist
    def test_fetchandfilter(self):
        from metoffice import setlocation
        with patch.object(self.URLCache, 'get', return_value=open(FORECASTSITELIST)):#@UndefinedVariable
            fetchandfilter = setlocation.fetchandfilter('ForecastLocation', 'Cairn')
            first = [json.load(open(FORECASTSITELIST))['Locations']['Location'][0]]
            first[0]['distance'] = 10
            first[0]['display'] = 'Cairnwell (10km)'
            self.assertEqual(first, fetchandfilter)

        with patch.object(self.URLCache, 'get', return_value=open(TEXTSITELIST)):#@UndefinedVariable
            result = setlocation.fetchandfilter('RegionalLocation', 'East Of England')
            expect = [{'display': 'East of England', u'id': u'512', u'name': 'East of England'}]
            self.assertEqual(expect, result)

    def test_main(self):
        from metoffice import setlocation
        setlocation.fetchandfilter = Mock(return_value=[])
        self.xbmc.Keyboard.return_value.getText = Mock(return_value='Pontypandy')
        self.xbmc.Keyboard.return_value.isConfirmed = Mock(return_value=True)
        setlocation.main('ForecastLocation')
        setlocation.fetchandfilter.assert_called_with('ForecastLocation', 'Pontypandy')#@UndefinedVariable
        self.assertTrue(self.xbmcgui.Dialog.return_value.ok.called)

        setlocation.fetchandfilter = Mock(return_value=[{'display' : 'Pontypandy',
                                                         'name' : 'Pontypandy',
                                                         'id': '1',
                                                         'latitude':'2',
                                                         'longitude':'3'}])
        self.xbmcgui.Dialog.return_value.select = Mock(return_value = 0)
        setlocation.main('ForecastLocation')
        setlocation.fetchandfilter.assert_called_with('ForecastLocation', 'Pontypandy')#@UndefinedVariable
        self.assertTrue(self.xbmcgui.Dialog.return_value.select.called)
        expected = [(('ForecastLocation', 'Pontypandy'),),
                   (('ForecastLocationID', '1'),),
                   (('ForecastLocationLatitude', '2'),),
                   (('ForecastLocationLongitude', '3'),)]
        self.assertEqual(expected, self.xbmcaddon.Addon.return_value.setSetting.call_args_list)

    def tearDown(self):
        super(TestSetLocation, self).tearDown()
        shutil.rmtree(RESULTS_FOLDER)