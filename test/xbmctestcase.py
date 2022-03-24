import unittest
from unittest.mock import patch, Mock


class XBMCTestCase(unittest.TestCase):
    def setUp(self):
        # Mock up any calls to modules that cannot be imported
        self.xbmcgui = Mock()
        self.xbmcaddon = Mock()

        modules = {
            'xbmcgui': self.xbmcgui,
            'xbmcaddon': self.xbmcaddon
        }
        self.module_patcher = patch.dict('sys.modules', modules)  # @UndefinedVariable
        self.addon_patcher = patch('xbmcaddon.Addon')
        self.module_patcher.start()
        self.addon_patcher.start()

        self.info_labels = {'System.TemperatureUnits': 'C',
                            'System.BuildVersion': '16.0 Git:12345678-90a1234'}

        self.region = {'tempunit': 'C',
                       'speedunit': 'mph'}

    def mock_getInfoLabel(self, key):
        return self.info_labels[key]

    def tearDown(self):
        self.module_patcher.stop()
        self.addon_patcher.stop()
