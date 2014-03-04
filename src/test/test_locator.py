import os
import json
from xbmctestcase import XBMCTestCase
from mock import patch

TEST_FOLDER = os.path.dirname(__file__)
RESULTS_FOLDER = os.path.join(TEST_FOLDER, 'results')
DATA_FOLDER = os.path.join(TEST_FOLDER, 'data')

TELIZE_DATA = os.path.join(DATA_FOLDER, 'telize.json')
SITELIST_DATA = os.path.join(DATA_FOLDER, 'forecastsitelist.json')

class TestLocator(XBMCTestCase):
    @patch('metoffice.utils.locator.URLCache')
    def test_distances(self, MockCache):
        from metoffice.utils import locator
        mock_instance = MockCache.return_value
        mock_instance.__enter__.return_value.jsonretrieve.return_value = json.load(open(TELIZE_DATA))
        sitelist = json.load(open(SITELIST_DATA))['Locations']['Location']
        locator.distances(sitelist, 2) #2 = Telize
        for site in sitelist:
            self.assertIn('distance', site)
        self.assertEqual(640, sitelist[0]['distance'], 'Distance was not calculated correctly')
        self.assertEqual(614, sitelist[1]['distance'], 'Distance was not calculated correctly')
        self.assertEqual(703, sitelist[2]['distance'], 'Distance was not calculated correctly')