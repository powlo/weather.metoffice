from datetime import datetime
from unittest import TestCase
from unittest.mock import Mock, patch

import xbmc

from metoffice import utilities, constants


class TestUtilities(TestCase):

    def test_strptime(self):
        date = '23:06 Mon 4 Jan 2013'
        fmt = '%H:%M %a %d %b %Y'
        self.assertEqual(datetime.strptime(date, fmt), utilities.strptime(date, fmt))

    @patch('xbmc.log')
    def test_log(self, mock_log):
        msg = "Log message"
        utilities.log(msg)
        mock_log.assert_called_with('weather.metoffice: {0}'.format(msg), xbmc.LOGINFO)

    @patch('xbmcgui.getCurrentWindowId', Mock(return_value=constants.WEATHER_WINDOW_ID))
    @patch('xbmc.executebuiltin')
    def test_xbmcbusy(self, mock_executebuiltin):
        mock_func = Mock()
        mock_func.__name__ = "Mock"
        decorated_func = utilities.xbmcbusy(mock_func)
        decorated_func(1, 2, 3)
        self.assertEqual(2, len(mock_executebuiltin.call_args_list))
        self.assertEqual(mock_executebuiltin.call_args_list[0], (("ActivateWindow(busydialognocancel)",),))
        self.assertEqual(mock_executebuiltin.call_args_list[1], (("Dialog.Close(busydialognocancel)",),))
        mock_func.assert_called_with(1, 2, 3)

    @patch('metoffice.utilities.WINDOW')
    def test_panelbusy(self, mock_window):
        mock_func = Mock()
        mock_func.__name__ = "Mock"
        rightbusy = utilities.panelbusy("RightPanel")
        decorated_func = rightbusy(mock_func)
        decorated_func(1, 2, 3)
        mock_window.setProperty.assert_called_once_with('RightPanel.IsBusy', 'true')
        mock_window.clearProperty.assert_called_once_with('RightPanel.IsBusy')
        mock_func.assert_called_with(1, 2, 3)

    # Have to write a stubby because lambdas contain expressions not statements
    def lambda_raise(self):
        raise IOError('An IOError occurred')

    @patch('xbmc.log')
    @patch('metoffice.utilities.DIALOG')
    @patch('xbmcgui.getCurrentWindowId', Mock(return_value=constants.WEATHER_WINDOW_ID))
    def test_failgracefully(self, mock_dialog, mock_log):
        message = ('Oh no', 'It all went wrong')
        mock_func = Mock(side_effect=IOError(*message))
        mock_func.__name__ = "Mock"
        decorated_func = utilities.failgracefully(mock_func)
        decorated_func(1, 2, 3)
        mock_func.assert_called_once_with(1, 2, 3)
        self.assertTrue(mock_log.called)
        self.assertTrue(mock_dialog.ok.called)
        mock_dialog.ok.assert_called_once_with(message[0].title(), message[1])

        # Test when exception called with only one arg
        mock_dialog.ok.reset_mock()
        message = ('Oh no',)
        mock_func.side_effect = IOError(*message)
        decorated_func(1, 2, 3)
        mock_dialog.ok.assert_called_once_with(message[0].title(), 'See log file for details')

        # Test when exception called with no args
        mock_dialog.ok.reset_mock()
        mock_func.side_effect = IOError()
        decorated_func(1, 2, 3)
        mock_dialog.ok.assert_called_once_with('Error', 'See log file for details')

    def test_minutes_as_time(self):
        self.assertEqual("03:00", utilities.minutes_as_time(180))

    @patch('metoffice.utilities.TEMPERATUREUNITS', 'C')
    def test_localise_temperature_celsius(self):
        self.assertEqual('0', utilities.localised_temperature('0'))
        self.assertEqual('-20', utilities.localised_temperature('-20'))
        self.assertEqual('20', utilities.localised_temperature('20'))

    @patch('metoffice.utilities.TEMPERATUREUNITS', 'F')
    def test_localise_temperature_fahrenheit(self):
        self.assertEqual('32', utilities.localised_temperature('0'))
        self.assertEqual('-4', utilities.localised_temperature('-20'))
        self.assertEqual('68', utilities.localised_temperature('20'))
        self.assertEqual('', utilities.localised_temperature(''))

    def test_rownd(self):
        self.assertEqual('11', utilities.rownd('10.7'))
        self.assertEqual('10', utilities.rownd('10.1'))
        self.assertEqual('10', utilities.rownd('10.5'))
        self.assertEqual('', utilities.rownd(''))

    @patch('xbmc.LOGWARNING', 3)
    @patch('metoffice.utilities.log')
    @patch('metoffice.utilities.ADDON')
    def test_gettext(self, mock_addon, mock_log):
        trans = "Nire aerolabangailua aingirez beteta dago"
        known_string = "Observation Location"
        unknown_string = "Observation Position"
        mock_addon.getLocalizedString = Mock(return_value=trans)

        # successful translation
        result = utilities.gettext(known_string)
        self.assertTrue(mock_addon.getLocalizedString.called)
        self.assertEqual(trans, result)

        # KeyError
        mock_addon.getLocalizedString.reset_mock()
        result = utilities.gettext(unknown_string)
        self.assertTrue(mock_log.called)
        self.assertEqual(unknown_string, result)

        # TranslationError
        mock_addon.getLocalizedString.reset_mock()
        mock_addon.getLocalizedString = Mock(return_value='')
        result = utilities.gettext(known_string)
        self.assertTrue(utilities.ADDON.getLocalizedString.called)
        self.assertEqual(known_string, result)
