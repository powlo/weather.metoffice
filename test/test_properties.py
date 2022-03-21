import os
import re
import shutil
import datetime
from PIL import Image
from unittest.mock import Mock, patch
from test.xbmctestcase import XBMCTestCase

TEST_FOLDER = os.path.dirname(__file__)
DATA_FOLDER = os.path.join(TEST_FOLDER, 'data')
RESULTS_FOLDER = os.path.join(TEST_FOLDER, 'results')
OBSERVATIONHOURLY = os.path.join(DATA_FOLDER, 'observationhourly.json')
OBSERVATIONHOURLY2 = os.path.join(DATA_FOLDER, 'observationhourly2.json')
FORECASTDAILY = os.path.join(DATA_FOLDER, 'forecastdaily.json')
FORECAST3HOURLY = os.path.join(DATA_FOLDER, 'forecast3hourly.json')
FORECASTTEXT = os.path.join(DATA_FOLDER, 'forecasttext.json')
FORECASTLAYERCAPABILITIES = os.path.join(DATA_FOLDER, 'forecastlayercapabilities.json')
OBSERVATIONLAYERCAPABILITIES = os.path.join(DATA_FOLDER, 'observationlayercapabilities.json')
CORRUPTFORECASTLAYERCAPABILITIES = os.path.join(DATA_FOLDER, 'corruptforecastlayercapabilities.json')
CORRUPTOBSERVATIONLAYERCAPABILITIES = os.path.join(DATA_FOLDER, 'corruptobservationlayercapabilities.json')
FORECASTSITELIST = os.path.join(DATA_FOLDER, 'forecastsitelist.json')
TEXTSITELIST = os.path.join(DATA_FOLDER, 'textsitelist.json')
GEOIP = os.path.join(DATA_FOLDER, 'ip-api.json')
EMPTY_FILE = os.path.join(DATA_FOLDER, 'empty.json')
GOOGLE_SURFACE_IMAGE = os.path.join(DATA_FOLDER, 'google_surface.png')
GOOGLE_MARKER_IMAGE = os.path.join(DATA_FOLDER, 'google_marker.png')
PRECIPITATION_LAYER_IMAGE = os.path.join(RESULTS_FOLDER, 'precipitation_layer.png')

PRECIPITATION_LAYER_HOUR0_URL = ('http://datapoint.metoffice.gov.uk/'
                                 'public/data/layer/wxfcs/Precipitation_Rate/png'
                                 '?RUN=2014-03-19T09:00:00Z&FORECAST=0&key=12345')
PRECIPITATION_LAYER_HOUR36_URL = ('http://datapoint.metoffice.gov.uk/'
                                  'public/data/layer/wxfcs/Precipitation_Rate/png'
                                  '?RUN=2014-03-19T09:00:00Z&FORECAST=36&key=12345')
OBSERVATION_LAYER0_URL = ('http://datapoint.metoffice.gov.uk/'
                          'public/data/layer/wxobs/RADAR_UK_Composite_Highres/png'
                          '?TIME=2014-04-01T16:30:00Z&key=12345')
OBSERVATION_LAYER1_URL = ('http://datapoint.metoffice.gov.uk/'
                          'public/data/layer/wxobs/RADAR_UK_Composite_Highres/png'
                          '?TIME=2014-04-01T13:30:00Z&key=12345')


class TestProperties(XBMCTestCase):
    def setUp(self):
        super(TestProperties, self).setUp()
        self.xbmcvfs.translatePath.side_effect = lambda x: x

        self.settings = {'ApiKey': '12345',
                         'GeoLocation': 'true',
                         'GeoIPProvider': '0',
                         'ForecastLocation': 'CAMBRIDGE NIAB',
                         'ForecastLocationID': '99123',
                         'ForecastLocationLatitude': '52.245',
                         'ForecastLocationLongitude': '0.103',
                         'ObservationLocation': 'BEDFORD',
                         'ObservationLocationID': '3560',
                         'RegionalLocation': 'Wales',
                         'RegionalLocationID': '516'
                         }

        self.window_properties = {'ForecastMap.LayerSelection': 'Rainfall',
                                  'ObservationMap.LayerSelection': 'Rainfall',
                                  'ForecastMap.Slider': '0',
                                  'ObservationMap.Slider': '0',
                                  'Weather.CurrentView': 'Doesnt matter'}

        addon = self.xbmcaddon.Addon.return_value
        addon.getSetting.side_effect = self.mock_getSetting
        addon.setSetting.side_effect = self.mock_setSetting

        window = self.xbmcgui.Window.return_value
        window.getProperty.side_effect = self.mock_getProperty
        window.setProperty.side_effect = self.mock_setProperty

        from metoffice import constants
        self.constants = constants

        # create a disposable area for testing
        try:
            os.mkdir(RESULTS_FOLDER)
        except OSError:
            pass

        shutil.copy(os.path.join(DATA_FOLDER, 'precipitation_layer.png'),
                    os.path.join(RESULTS_FOLDER, 'precipitation_layer.png'))

    def mock_getSetting(self, key):
        return self.settings[key]

    def mock_setSetting(self, key, value):
        self.settings[key] = value

    def mock_getProperty(self, key):
        return self.window_properties[key]

    def mock_setProperty(self, key, value):
        self.window_properties[key] = value

    def mock_get(self, url, expiry_callback, resource_callback=None):
        return {
            self.constants.FORECAST_SITELIST_URL: FORECASTSITELIST,
            self.constants.DAILY_LOCATION_FORECAST_URL: FORECASTDAILY,
            self.constants.THREEHOURLY_LOCATION_FORECAST_URL: FORECAST3HOURLY,
            self.constants.FORECAST_LAYER_CAPABILITIES_URL: FORECASTLAYERCAPABILITIES,
            self.constants.OBSERVATION_LAYER_CAPABILITIES_URL: OBSERVATIONLAYERCAPABILITIES,
            self.constants.TEXT_FORECAST_URL: FORECASTTEXT,
            self.constants.HOURLY_LOCATION_OBSERVATION_URL: OBSERVATIONHOURLY,
            self.constants.GEOIP_PROVIDER['url']: GEOIP,
            self.constants.GOOGLE_SURFACE: GOOGLE_SURFACE_IMAGE,
            self.constants.GOOGLE_MARKER: GOOGLE_MARKER_IMAGE,
            PRECIPITATION_LAYER_HOUR0_URL: PRECIPITATION_LAYER_IMAGE,
            PRECIPITATION_LAYER_HOUR36_URL: PRECIPITATION_LAYER_IMAGE,
            OBSERVATION_LAYER0_URL: PRECIPITATION_LAYER_IMAGE,
            OBSERVATION_LAYER1_URL: PRECIPITATION_LAYER_IMAGE,
        }[url]

    def mock_panelbusy(self, pane):
        def decorate(f):
            def wrapper(*args, **kwargs):
                return f(*args, **kwargs)
            return wrapper
        return decorate

    @patch('metoffice.utilities.panelbusy')
    @patch('metoffice.urlcache.URLCache')
    def test_observation(self, mock_cache, mock_panelbusy):
        mock_panelbusy.side_effect = self.mock_panelbusy
        mock_cache.return_value.__enter__.return_value.get = Mock(side_effect=self.mock_get)
        from metoffice import properties
        properties.observation()
        self.assertIn('HourlyObservation.IssuedAt', self.window_properties)
        self.assertEqual(self.window_properties['HourlyObservation.IssuedAt'], '17:00 Thu 06 Mar 2014')
        self.assertIn('Current.Condition', self.window_properties)
        self.assertEqual(self.window_properties['Current.Condition'], 'Cloudy')
        self.assertIn('Current.Visibility', self.window_properties)
        self.assertEqual(self.window_properties['Current.Visibility'], '45000')
        self.assertIn('Current.Pressure', self.window_properties)
        self.assertEqual(self.window_properties['Current.Pressure'], '1021')
        self.assertIn('Current.Temperature', self.window_properties)
        self.assertEqual(self.window_properties['Current.Temperature'], '10')
        self.assertIn('Current.Wind', self.window_properties)
        self.assertEqual(self.window_properties['Current.Wind'], '23.0')
        self.assertIn('Current.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Current.WindDirection'], 'SW')
        self.assertIn('Current.WindGust', self.window_properties)
        self.assertEqual(self.window_properties['Current.WindGust'], 'n/a')
        self.assertIn('Current.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Current.OutlookIcon'], '26.png')
        self.assertIn('Current.FanartCode', self.window_properties)
        self.assertEqual(self.window_properties['Current.FanartCode'], '26.png')
        self.assertIn('Current.DewPoint', self.window_properties)
        self.assertEqual(self.window_properties['Current.DewPoint'], '6')
        self.assertIn('Current.Humidity', self.window_properties)
        self.assertEqual(self.window_properties['Current.Humidity'], '79')

        # Test exceptions when reports don't contain list items.
        mock_cache.return_value.__enter__.return_value.get = Mock(return_value=OBSERVATIONHOURLY2)
        properties.observation()
        self.assertIn('HourlyObservation.IssuedAt', self.window_properties)
        self.assertEqual(self.window_properties['HourlyObservation.IssuedAt'], '17:00 Thu 06 Mar 2014')
        self.assertIn('Current.Condition', self.window_properties)
        self.assertEqual(self.window_properties['Current.Condition'], 'Sunny')
        self.assertIn('Current.Visibility', self.window_properties)
        self.assertEqual(self.window_properties['Current.Visibility'], '45000')
        self.assertIn('Current.Pressure', self.window_properties)
        self.assertEqual(self.window_properties['Current.Pressure'], '1021')
        self.assertIn('Current.Temperature', self.window_properties)
        self.assertEqual(self.window_properties['Current.Temperature'], '10')
        self.assertIn('Current.Wind', self.window_properties)
        self.assertEqual(self.window_properties['Current.Wind'], '16.0')
        self.assertIn('Current.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Current.WindDirection'], 'WSW')
        self.assertIn('Current.WindGust', self.window_properties)
        self.assertEqual(self.window_properties['Current.WindGust'], 'n/a')
        self.assertIn('Current.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Current.OutlookIcon'], '32.png')
        self.assertIn('Current.FanartCode', self.window_properties)
        self.assertEqual(self.window_properties['Current.FanartCode'], '32.png')
        self.assertIn('Current.DewPoint', self.window_properties)
        self.assertEqual(self.window_properties['Current.DewPoint'], '4')
        self.assertIn('Current.Humidity', self.window_properties)
        self.assertEqual(self.window_properties['Current.Humidity'], '66')

        # Test exception handling when given json without proper keys
        mock_cache.return_value.__enter__.return_value.get = Mock(return_value=EMPTY_FILE)
        with self.assertRaises(KeyError) as cm:
            properties.observation()
        self.assertEqual(('Key Error in JSON File',
                          "Key 'SiteRep' not found while processing file from url:",
                          self.constants.HOURLY_LOCATION_OBSERVATION_URL), cm.exception.args)

    @patch('metoffice.utilities.panelbusy')
    @patch('metoffice.urlcache.URLCache')
    def test_daily(self, mock_cache, mock_panelbusy):
        mock_panelbusy.side_effect = self.mock_panelbusy
        mock_cache.return_value.__enter__.return_value.get = Mock(side_effect=self.mock_get)
        from metoffice import properties
        properties.daily()
        self.assertIn('DailyForecast.IssuedAt', self.window_properties)
        self.assertEqual(self.window_properties['DailyForecast.IssuedAt'], '14:00 Mon 24 Feb 2014')
        self.assertIn('Day0.Title', self.window_properties)
        self.assertEqual(self.window_properties['Day0.Title'], 'Mon')
        self.assertIn('Day0.HighTemp', self.window_properties)
        self.assertEqual(self.window_properties['Day0.HighTemp'], '13')
        self.assertIn('Day0.LowTemp', self.window_properties)
        self.assertEqual(self.window_properties['Day0.LowTemp'], '7')
        self.assertIn('Day0.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Day0.WindSpeed'], '13')
        self.assertIn('Day0.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Day0.WindDirection'], 'ssw')
        self.assertIn('Day0.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Day0.Outlook'], 'Light Rain')
        self.assertIn('Day0.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Day0.OutlookIcon'], '11.png')

        self.assertIn('Day1.Title', self.window_properties)
        self.assertEqual(self.window_properties['Day1.Title'], 'Tue')
        self.assertIn('Day1.HighTemp', self.window_properties)
        self.assertEqual(self.window_properties['Day1.HighTemp'], '12')
        self.assertIn('Day1.LowTemp', self.window_properties)
        self.assertEqual(self.window_properties['Day1.LowTemp'], '3')
        self.assertIn('Day1.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Day1.WindSpeed'], '18')
        self.assertIn('Day1.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Day1.WindDirection'], 'ssw')
        self.assertIn('Day1.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Day1.Outlook'], 'Sunny')
        self.assertIn('Day1.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Day1.OutlookIcon'], '32.png')

        self.assertIn('Day2.Title', self.window_properties)
        self.assertEqual(self.window_properties['Day2.Title'], 'Wed')
        self.assertIn('Day2.HighTemp', self.window_properties)
        self.assertEqual(self.window_properties['Day2.HighTemp'], '11')
        self.assertIn('Day2.LowTemp', self.window_properties)
        self.assertEqual(self.window_properties['Day2.LowTemp'], '4')
        self.assertIn('Day2.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Day2.WindSpeed'], '13')
        self.assertIn('Day2.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Day2.WindDirection'], 'wsw')
        self.assertIn('Day2.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Day2.Outlook'], 'Sunny')
        self.assertIn('Day2.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Day2.OutlookIcon'], '32.png')

        self.assertIn('Day3.Title', self.window_properties)
        self.assertEqual(self.window_properties['Day3.Title'], 'Thu')
        self.assertIn('Day3.HighTemp', self.window_properties)
        self.assertEqual(self.window_properties['Day3.HighTemp'], '11')
        self.assertIn('Day3.LowTemp', self.window_properties)
        self.assertEqual(self.window_properties['Day3.LowTemp'], '3')
        self.assertIn('Day3.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Day3.WindSpeed'], '16')
        self.assertIn('Day3.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Day3.WindDirection'], 'wsw')
        self.assertIn('Day3.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Day3.Outlook'], 'Heavy Rain')
        self.assertIn('Day3.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Day3.OutlookIcon'], '40.png')

        self.assertIn('Day4.Title', self.window_properties)
        self.assertEqual(self.window_properties['Day4.Title'], 'Fri')
        self.assertIn('Day4.HighTemp', self.window_properties)
        self.assertEqual(self.window_properties['Day4.HighTemp'], '9')
        self.assertIn('Day4.LowTemp', self.window_properties)
        self.assertEqual(self.window_properties['Day4.LowTemp'], '2')
        self.assertIn('Day4.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Day4.WindSpeed'], '11')
        self.assertIn('Day4.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Day4.WindDirection'], 'sw')
        self.assertIn('Day4.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Day4.Outlook'], 'Light Rain')
        self.assertIn('Day4.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Day4.OutlookIcon'], '11.png')

        # Test exception handling when given json without proper keys
        mock_cache.return_value.__enter__.return_value.get = Mock(return_value=EMPTY_FILE)
        with self.assertRaises(KeyError) as cm:
            properties.daily()
        self.assertEqual(('Key Error in JSON File',
                          "Key 'SiteRep' not found while processing file from url:",
                          self.constants.DAILY_LOCATION_FORECAST_URL), cm.exception.args)

    @patch('metoffice.utilities.panelbusy')
    @patch('metoffice.urlcache.URLCache')
    def test_threehourly(self, mock_cache, mock_panelbusy):
        mock_panelbusy.side_effect = self.mock_panelbusy
        mock_cache.return_value.__enter__.return_value.get = Mock(side_effect=self.mock_get)
        from metoffice import properties
        properties.threehourly()
        self.assertIn('3HourlyForecast.IssuedAt', self.window_properties)
        self.assertEqual(self.window_properties['3HourlyForecast.IssuedAt'], '16:00 Sat 01 Mar 2014')

        self.assertIn('Hourly.1.Time', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.1.Time'], '12:00')
        self.assertIn('Hourly.1.Temperature', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.1.Temperature'], '6' + self.constants.TEMPERATUREUNITS)
        self.assertIn('Hourly.1.FeelsLikeTemp', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.1.FeelsLikeTemp'], '4')
        self.assertIn('Hourly.1.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.1.WindSpeed'], '4')
        self.assertIn('Hourly.1.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.1.WindDirection'], 'nnw')
        self.assertIn('Hourly.1.GustSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.1.GustSpeed'], '7')
        self.assertIn('Hourly.1.UVIndex', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.1.UVIndex'], '1')
        self.assertIn('Hourly.1.Precipitation', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.1.Precipitation'], '6%')
        self.assertIn('Hourly.1.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.1.Outlook'], 'Cloudy')
        self.assertIn('Hourly.1.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.1.OutlookIcon'], '26.png')

        self.assertIn('Hourly.2.Time', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.2.Time'], '15:00')
        self.assertIn('Hourly.2.Temperature', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.2.Temperature'], '8' + self.constants.TEMPERATUREUNITS)
        self.assertIn('Hourly.2.FeelsLikeTemp', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.2.FeelsLikeTemp'], '6')
        self.assertIn('Hourly.2.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.2.WindSpeed'], '7')
        self.assertIn('Hourly.2.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.2.WindDirection'], 'wsw')
        self.assertIn('Hourly.2.GustSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.2.GustSpeed'], '11')
        self.assertIn('Hourly.2.UVIndex', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.2.UVIndex'], '1')
        self.assertIn('Hourly.2.Precipitation', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.2.Precipitation'], '6%')
        self.assertIn('Hourly.2.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.2.Outlook'], 'Cloudy')
        self.assertIn('Hourly.2.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.2.OutlookIcon'], '26.png')

        self.assertIn('Hourly.3.Time', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.3.Time'], '18:00')
        self.assertIn('Hourly.3.Temperature', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.3.Temperature'], '6' + self.constants.TEMPERATUREUNITS)
        self.assertIn('Hourly.3.FeelsLikeTemp', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.3.FeelsLikeTemp'], '5')
        self.assertIn('Hourly.3.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.3.WindSpeed'], '2')
        self.assertIn('Hourly.3.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.3.WindDirection'], 'wsw')
        self.assertIn('Hourly.3.GustSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.3.GustSpeed'], '7')
        self.assertIn('Hourly.3.UVIndex', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.3.UVIndex'], '0')
        self.assertIn('Hourly.3.Precipitation', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.3.Precipitation'], '5%')
        self.assertIn('Hourly.3.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.3.Outlook'], 'Cloudy')
        self.assertIn('Hourly.3.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.3.OutlookIcon'], '26.png')

        self.assertIn('Hourly.4.Time', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.4.Time'], '21:00')
        self.assertIn('Hourly.4.Temperature', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.4.Temperature'], '5' + self.constants.TEMPERATUREUNITS)
        self.assertIn('Hourly.4.FeelsLikeTemp', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.4.FeelsLikeTemp'], '3')
        self.assertIn('Hourly.4.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.4.WindSpeed'], '4')
        self.assertIn('Hourly.4.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.4.WindDirection'], 'ssw')
        self.assertIn('Hourly.4.GustSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.4.GustSpeed'], '9')
        self.assertIn('Hourly.4.UVIndex', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.4.UVIndex'], '0')
        self.assertIn('Hourly.4.Precipitation', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.4.Precipitation'], '0%')
        self.assertIn('Hourly.4.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.4.Outlook'], 'Clear')
        self.assertIn('Hourly.4.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.4.OutlookIcon'], '31.png')

        self.assertIn('Hourly.5.Time', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.5.Time'], '00:00')
        self.assertIn('Hourly.5.Temperature', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.5.Temperature'], '3' + self.constants.TEMPERATUREUNITS)
        self.assertIn('Hourly.5.FeelsLikeTemp', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.5.FeelsLikeTemp'], '1')
        self.assertIn('Hourly.5.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.5.WindSpeed'], '7')
        self.assertIn('Hourly.5.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.5.WindDirection'], 'ssw')
        self.assertIn('Hourly.5.GustSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.5.GustSpeed'], '16')
        self.assertIn('Hourly.5.UVIndex', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.5.UVIndex'], '0')
        self.assertIn('Hourly.5.Precipitation', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.5.Precipitation'], '3%')
        self.assertIn('Hourly.5.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.5.Outlook'], 'Clear')
        self.assertIn('Hourly.5.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.5.OutlookIcon'], '31.png')

        self.assertIn('Hourly.6.Time', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.6.Time'], '03:00')
        self.assertIn('Hourly.6.Temperature', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.6.Temperature'], '3' + self.constants.TEMPERATUREUNITS)
        self.assertIn('Hourly.6.FeelsLikeTemp', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.6.FeelsLikeTemp'], '0')
        self.assertIn('Hourly.6.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.6.WindSpeed'], '9')
        self.assertIn('Hourly.6.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.6.WindDirection'], 'ssw')
        self.assertIn('Hourly.6.GustSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.6.GustSpeed'], '20')
        self.assertIn('Hourly.6.UVIndex', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.6.UVIndex'], '0')
        self.assertIn('Hourly.6.Precipitation', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.6.Precipitation'], '5%')
        self.assertIn('Hourly.6.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.6.Outlook'], 'Clear')
        self.assertIn('Hourly.6.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.6.OutlookIcon'], '31.png')

        self.assertIn('Hourly.7.Time', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.7.Time'], '06:00')
        self.assertIn('Hourly.7.Temperature', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.7.Temperature'], '4' + self.constants.TEMPERATUREUNITS)
        self.assertIn('Hourly.7.FeelsLikeTemp', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.7.FeelsLikeTemp'], '0')
        self.assertIn('Hourly.7.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.7.WindSpeed'], '11')
        self.assertIn('Hourly.7.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.7.WindDirection'], 'ssw')
        self.assertIn('Hourly.7.GustSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.7.GustSpeed'], '25')
        self.assertIn('Hourly.7.UVIndex', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.7.UVIndex'], '0')
        self.assertIn('Hourly.7.Precipitation', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.7.Precipitation'], '8%')
        self.assertIn('Hourly.7.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.7.Outlook'], 'Cloudy')
        self.assertIn('Hourly.7.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.7.OutlookIcon'], '26.png')

        self.assertIn('Hourly.8.Time', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.8.Time'], '09:00')
        self.assertIn('Hourly.8.Temperature', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.8.Temperature'], '6' + self.constants.TEMPERATUREUNITS)
        self.assertIn('Hourly.8.FeelsLikeTemp', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.8.FeelsLikeTemp'], '3')
        self.assertIn('Hourly.8.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.8.WindSpeed'], '13')
        self.assertIn('Hourly.8.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.8.WindDirection'], 'ssw')
        self.assertIn('Hourly.8.GustSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.8.GustSpeed'], '25')
        self.assertIn('Hourly.8.UVIndex', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.8.UVIndex'], '1')
        self.assertIn('Hourly.8.Precipitation', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.8.Precipitation'], '5%')
        self.assertIn('Hourly.8.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.8.Outlook'], 'Cloudy')
        self.assertIn('Hourly.8.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.8.OutlookIcon'], '26.png')

        self.assertIn('Hourly.9.Time', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.9.Time'], '12:00')
        self.assertIn('Hourly.9.Temperature', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.9.Temperature'], '9' + self.constants.TEMPERATUREUNITS)
        self.assertIn('Hourly.9.FeelsLikeTemp', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.9.FeelsLikeTemp'], '5')
        self.assertIn('Hourly.9.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.9.WindSpeed'], '18')
        self.assertIn('Hourly.9.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.9.WindDirection'], 's')
        self.assertIn('Hourly.9.GustSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.9.GustSpeed'], '31')
        self.assertIn('Hourly.9.UVIndex', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.9.UVIndex'], '1')
        self.assertIn('Hourly.9.Precipitation', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.9.Precipitation'], '5%')
        self.assertIn('Hourly.9.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.9.Outlook'], 'Cloudy')
        self.assertIn('Hourly.9.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.9.OutlookIcon'], '26.png')

        self.assertIn('Hourly.10.Time', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.10.Time'], '15:00')
        self.assertIn('Hourly.10.Temperature', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.10.Temperature'], '9' + self.constants.TEMPERATUREUNITS)
        self.assertIn('Hourly.10.FeelsLikeTemp', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.10.FeelsLikeTemp'], '5')
        self.assertIn('Hourly.10.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.10.WindSpeed'], '20')
        self.assertIn('Hourly.10.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.10.WindDirection'], 's')
        self.assertIn('Hourly.10.GustSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.10.GustSpeed'], '36')
        self.assertIn('Hourly.10.UVIndex', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.10.UVIndex'], '1')
        self.assertIn('Hourly.10.Precipitation', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.10.Precipitation'], '31%')
        self.assertIn('Hourly.10.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.10.Outlook'], 'Cloudy')
        self.assertIn('Hourly.10.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.10.OutlookIcon'], '26.png')

        self.assertIn('Hourly.11.Time', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.11.Time'], '18:00')
        self.assertIn('Hourly.11.Temperature', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.11.Temperature'], '8' + self.constants.TEMPERATUREUNITS)
        self.assertIn('Hourly.11.FeelsLikeTemp', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.11.FeelsLikeTemp'], '3')
        self.assertIn('Hourly.11.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.11.WindSpeed'], '20')
        self.assertIn('Hourly.11.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.11.WindDirection'], 's')
        self.assertIn('Hourly.11.GustSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.11.GustSpeed'], '38')
        self.assertIn('Hourly.11.UVIndex', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.11.UVIndex'], '0')
        self.assertIn('Hourly.11.Precipitation', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.11.Precipitation'], '95%')
        self.assertIn('Hourly.11.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.11.Outlook'], 'Heavy Rain')
        self.assertIn('Hourly.11.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.11.OutlookIcon'], '40.png')

        self.assertIn('Hourly.12.Time', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.12.Time'], '21:00')
        self.assertIn('Hourly.12.Temperature', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.12.Temperature'], '7' + self.constants.TEMPERATUREUNITS)
        self.assertIn('Hourly.12.FeelsLikeTemp', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.12.FeelsLikeTemp'], '3')
        self.assertIn('Hourly.12.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.12.WindSpeed'], '16')
        self.assertIn('Hourly.12.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.12.WindDirection'], 's')
        self.assertIn('Hourly.12.GustSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.12.GustSpeed'], '29')
        self.assertIn('Hourly.12.UVIndex', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.12.UVIndex'], '0')
        self.assertIn('Hourly.12.Precipitation', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.12.Precipitation'], '96%')
        self.assertIn('Hourly.12.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.12.Outlook'], 'Heavy Rain')
        self.assertIn('Hourly.12.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.12.OutlookIcon'], '40.png')

        self.assertIn('Hourly.13.Time', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.13.Time'], '00:00')
        self.assertIn('Hourly.13.Temperature', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.13.Temperature'], '5' + self.constants.TEMPERATUREUNITS)
        self.assertIn('Hourly.13.FeelsLikeTemp', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.13.FeelsLikeTemp'], '1')
        self.assertIn('Hourly.13.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.13.WindSpeed'], '13')
        self.assertIn('Hourly.13.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.13.WindDirection'], 'wsw')
        self.assertIn('Hourly.13.GustSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.13.GustSpeed'], '22')
        self.assertIn('Hourly.13.UVIndex', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.13.UVIndex'], '0')
        self.assertIn('Hourly.13.Precipitation', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.13.Precipitation'], '54%')
        self.assertIn('Hourly.13.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.13.Outlook'], 'Light Rain')
        self.assertIn('Hourly.13.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.13.OutlookIcon'], '11.png')

        self.assertIn('Hourly.14.Time', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.14.Time'], '03:00')
        self.assertIn('Hourly.14.Temperature', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.14.Temperature'], '3' + self.constants.TEMPERATUREUNITS)
        self.assertIn('Hourly.14.FeelsLikeTemp', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.14.FeelsLikeTemp'], '-1')
        self.assertIn('Hourly.14.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.14.WindSpeed'], '11')
        self.assertIn('Hourly.14.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.14.WindDirection'], 'ssw')
        self.assertIn('Hourly.14.GustSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.14.GustSpeed'], '18')
        self.assertIn('Hourly.14.UVIndex', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.14.UVIndex'], '0')
        self.assertIn('Hourly.14.Precipitation', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.14.Precipitation'], '13%')
        self.assertIn('Hourly.14.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.14.Outlook'], 'Clear')
        self.assertIn('Hourly.14.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.14.OutlookIcon'], '31.png')

        self.assertIn('Hourly.15.Time', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.15.Time'], '06:00')
        self.assertIn('Hourly.15.Temperature', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.15.Temperature'], '2' + self.constants.TEMPERATUREUNITS)
        self.assertIn('Hourly.15.FeelsLikeTemp', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.15.FeelsLikeTemp'], '-2')
        self.assertIn('Hourly.15.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.15.WindSpeed'], '11')
        self.assertIn('Hourly.15.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.15.WindDirection'], 's')
        self.assertIn('Hourly.15.GustSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.15.GustSpeed'], '20')
        self.assertIn('Hourly.15.UVIndex', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.15.UVIndex'], '0')
        self.assertIn('Hourly.15.Precipitation', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.15.Precipitation'], '5%')
        self.assertIn('Hourly.15.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.15.Outlook'], 'Cloudy')
        self.assertIn('Hourly.15.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.15.OutlookIcon'], '26.png')

        self.assertIn('Hourly.16.Time', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.16.Time'], '09:00')
        self.assertIn('Hourly.16.Temperature', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.16.Temperature'], '5' + self.constants.TEMPERATUREUNITS)
        self.assertIn('Hourly.16.FeelsLikeTemp', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.16.FeelsLikeTemp'], '1')
        self.assertIn('Hourly.16.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.16.WindSpeed'], '11')
        self.assertIn('Hourly.16.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.16.WindDirection'], 's')
        self.assertIn('Hourly.16.GustSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.16.GustSpeed'], '22')
        self.assertIn('Hourly.16.UVIndex', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.16.UVIndex'], '1')
        self.assertIn('Hourly.16.Precipitation', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.16.Precipitation'], '33%')
        self.assertIn('Hourly.16.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.16.Outlook'], 'Light Rain')
        self.assertIn('Hourly.16.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.16.OutlookIcon'], '11.png')

        self.assertIn('Hourly.17.Time', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.17.Time'], '12:00')
        self.assertIn('Hourly.17.Temperature', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.17.Temperature'], '7' + self.constants.TEMPERATUREUNITS)
        self.assertIn('Hourly.17.FeelsLikeTemp', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.17.FeelsLikeTemp'], '4')
        self.assertIn('Hourly.17.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.17.WindSpeed'], '11')
        self.assertIn('Hourly.17.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.17.WindDirection'], 's')
        self.assertIn('Hourly.17.GustSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.17.GustSpeed'], '22')
        self.assertIn('Hourly.17.UVIndex', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.17.UVIndex'], '1')
        self.assertIn('Hourly.17.Precipitation', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.17.Precipitation'], '65%')
        self.assertIn('Hourly.17.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.17.Outlook'], 'Heavy Rain')
        self.assertIn('Hourly.17.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.17.OutlookIcon'], '40.png')

        self.assertIn('Hourly.18.Time', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.18.Time'], '15:00')
        self.assertIn('Hourly.18.Temperature', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.18.Temperature'], '7' + self.constants.TEMPERATUREUNITS)
        self.assertIn('Hourly.18.FeelsLikeTemp', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.18.FeelsLikeTemp'], '4')
        self.assertIn('Hourly.18.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.18.WindSpeed'], '7')
        self.assertIn('Hourly.18.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.18.WindDirection'], 'ssw')
        self.assertIn('Hourly.18.GustSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.18.GustSpeed'], '16')
        self.assertIn('Hourly.18.UVIndex', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.18.UVIndex'], '1')
        self.assertIn('Hourly.18.Precipitation', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.18.Precipitation'], '48%')
        self.assertIn('Hourly.18.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.18.Outlook'], 'Light Rain')
        self.assertIn('Hourly.18.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.18.OutlookIcon'], '11.png')

        self.assertIn('Hourly.19.Time', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.19.Time'], '18:00')
        self.assertIn('Hourly.19.Temperature', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.19.Temperature'], '5' + self.constants.TEMPERATUREUNITS)
        self.assertIn('Hourly.19.FeelsLikeTemp', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.19.FeelsLikeTemp'], '3')
        self.assertIn('Hourly.19.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.19.WindSpeed'], '7')
        self.assertIn('Hourly.19.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.19.WindDirection'], 'wsw')
        self.assertIn('Hourly.19.GustSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.19.GustSpeed'], '11')
        self.assertIn('Hourly.19.UVIndex', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.19.UVIndex'], '0')
        self.assertIn('Hourly.19.Precipitation', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.19.Precipitation'], '46%')
        self.assertIn('Hourly.19.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.19.Outlook'], 'Light Rain')
        self.assertIn('Hourly.19.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.19.OutlookIcon'], '45.png')

        self.assertIn('Hourly.20.Time', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.20.Time'], '21:00')
        self.assertIn('Hourly.20.Temperature', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.20.Temperature'], '4' + self.constants.TEMPERATUREUNITS)
        self.assertIn('Hourly.20.FeelsLikeTemp', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.20.FeelsLikeTemp'], '1')
        self.assertIn('Hourly.20.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.20.WindSpeed'], '9')
        self.assertIn('Hourly.20.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.20.WindDirection'], 'w')
        self.assertIn('Hourly.20.GustSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.20.GustSpeed'], '13')
        self.assertIn('Hourly.20.UVIndex', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.20.UVIndex'], '0')
        self.assertIn('Hourly.20.Precipitation', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.20.Precipitation'], '13%')
        self.assertIn('Hourly.20.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.20.Outlook'], 'Cloudy')
        self.assertIn('Hourly.20.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.20.OutlookIcon'], '26.png')

        self.assertIn('Hourly.21.Time', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.21.Time'], '00:00')
        self.assertIn('Hourly.21.Temperature', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.21.Temperature'], '3' + self.constants.TEMPERATUREUNITS)
        self.assertIn('Hourly.21.FeelsLikeTemp', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.21.FeelsLikeTemp'], '0')
        self.assertIn('Hourly.21.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.21.WindSpeed'], '9')
        self.assertIn('Hourly.21.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.21.WindDirection'], 'wnw')
        self.assertIn('Hourly.21.GustSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.21.GustSpeed'], '18')
        self.assertIn('Hourly.21.UVIndex', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.21.UVIndex'], '0')
        self.assertIn('Hourly.21.Precipitation', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.21.Precipitation'], '2%')
        self.assertIn('Hourly.21.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.21.Outlook'], 'Partly Cloudy')
        self.assertIn('Hourly.21.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.21.OutlookIcon'], '29.png')

        self.assertIn('Hourly.22.Time', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.22.Time'], '03:00')
        self.assertIn('Hourly.22.Temperature', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.22.Temperature'], '3' + self.constants.TEMPERATUREUNITS)
        self.assertIn('Hourly.22.FeelsLikeTemp', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.22.FeelsLikeTemp'], '-1')
        self.assertIn('Hourly.22.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.22.WindSpeed'], '9')
        self.assertIn('Hourly.22.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.22.WindDirection'], 'wnw')
        self.assertIn('Hourly.22.GustSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.22.GustSpeed'], '18')
        self.assertIn('Hourly.22.UVIndex', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.22.UVIndex'], '0')
        self.assertIn('Hourly.22.Precipitation', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.22.Precipitation'], '2%')
        self.assertIn('Hourly.22.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.22.Outlook'], 'Partly Cloudy')
        self.assertIn('Hourly.22.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.22.OutlookIcon'], '29.png')

        self.assertIn('Hourly.23.Time', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.23.Time'], '06:00')
        self.assertIn('Hourly.23.Temperature', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.23.Temperature'], '2' + self.constants.TEMPERATUREUNITS)
        self.assertIn('Hourly.23.FeelsLikeTemp', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.23.FeelsLikeTemp'], '-1')
        self.assertIn('Hourly.23.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.23.WindSpeed'], '9')
        self.assertIn('Hourly.23.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.23.WindDirection'], 'w')
        self.assertIn('Hourly.23.GustSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.23.GustSpeed'], '16')
        self.assertIn('Hourly.23.UVIndex', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.23.UVIndex'], '0')
        self.assertIn('Hourly.23.Precipitation', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.23.Precipitation'], '2%')
        self.assertIn('Hourly.23.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.23.Outlook'], 'Partly Cloudy')
        self.assertIn('Hourly.23.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.23.OutlookIcon'], '29.png')

        self.assertIn('Hourly.24.Time', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.24.Time'], '09:00')
        self.assertIn('Hourly.24.Temperature', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.24.Temperature'], '5' + self.constants.TEMPERATUREUNITS)
        self.assertIn('Hourly.24.FeelsLikeTemp', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.24.FeelsLikeTemp'], '2')
        self.assertIn('Hourly.24.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.24.WindSpeed'], '11')
        self.assertIn('Hourly.24.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.24.WindDirection'], 'w')
        self.assertIn('Hourly.24.GustSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.24.GustSpeed'], '20')
        self.assertIn('Hourly.24.UVIndex', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.24.UVIndex'], '1')
        self.assertIn('Hourly.24.Precipitation', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.24.Precipitation'], '6%')
        self.assertIn('Hourly.24.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.24.Outlook'], 'Partly Cloudy')
        self.assertIn('Hourly.24.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.24.OutlookIcon'], '30.png')

        self.assertIn('Hourly.25.Time', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.25.Time'], '12:00')
        self.assertIn('Hourly.25.Temperature', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.25.Temperature'], '8' + self.constants.TEMPERATUREUNITS)
        self.assertIn('Hourly.25.FeelsLikeTemp', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.25.FeelsLikeTemp'], '5')
        self.assertIn('Hourly.25.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.25.WindSpeed'], '11')
        self.assertIn('Hourly.25.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.25.WindDirection'], 'w')
        self.assertIn('Hourly.25.GustSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.25.GustSpeed'], '22')
        self.assertIn('Hourly.25.UVIndex', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.25.UVIndex'], '1')
        self.assertIn('Hourly.25.Precipitation', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.25.Precipitation'], '7%')
        self.assertIn('Hourly.25.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.25.Outlook'], 'Partly Cloudy')
        self.assertIn('Hourly.25.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.25.OutlookIcon'], '30.png')

        self.assertIn('Hourly.26.Time', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.26.Time'], '15:00')
        self.assertIn('Hourly.26.Temperature', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.26.Temperature'], '8' + self.constants.TEMPERATUREUNITS)
        self.assertIn('Hourly.26.FeelsLikeTemp', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.26.FeelsLikeTemp'], '6')
        self.assertIn('Hourly.26.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.26.WindSpeed'], '11')
        self.assertIn('Hourly.26.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.26.WindDirection'], 'w')
        self.assertIn('Hourly.26.GustSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.26.GustSpeed'], '18')
        self.assertIn('Hourly.26.UVIndex', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.26.UVIndex'], '1')
        self.assertIn('Hourly.26.Precipitation', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.26.Precipitation'], '10%')
        self.assertIn('Hourly.26.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.26.Outlook'], 'Sunny')
        self.assertIn('Hourly.26.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.26.OutlookIcon'], '32.png')

        self.assertIn('Hourly.27.Time', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.27.Time'], '18:00')
        self.assertIn('Hourly.27.Temperature', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.27.Temperature'], '6' + self.constants.TEMPERATUREUNITS)
        self.assertIn('Hourly.27.FeelsLikeTemp', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.27.FeelsLikeTemp'], '4')
        self.assertIn('Hourly.27.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.27.WindSpeed'], '7')
        self.assertIn('Hourly.27.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.27.WindDirection'], 'wsw')
        self.assertIn('Hourly.27.GustSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.27.GustSpeed'], '11')
        self.assertIn('Hourly.27.UVIndex', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.27.UVIndex'], '0')
        self.assertIn('Hourly.27.Precipitation', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.27.Precipitation'], '8%')
        self.assertIn('Hourly.27.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.27.Outlook'], 'Clear')
        self.assertIn('Hourly.27.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.27.OutlookIcon'], '31.png')

        self.assertIn('Hourly.28.Time', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.28.Time'], '21:00')
        self.assertIn('Hourly.28.Temperature', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.28.Temperature'], '5' + self.constants.TEMPERATUREUNITS)
        self.assertIn('Hourly.28.FeelsLikeTemp', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.28.FeelsLikeTemp'], '2')
        self.assertIn('Hourly.28.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.28.WindSpeed'], '7')
        self.assertIn('Hourly.28.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.28.WindDirection'], 'sw')
        self.assertIn('Hourly.28.GustSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.28.GustSpeed'], '13')
        self.assertIn('Hourly.28.UVIndex', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.28.UVIndex'], '0')
        self.assertIn('Hourly.28.Precipitation', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.28.Precipitation'], '11%')
        self.assertIn('Hourly.28.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.28.Outlook'], 'Partly Cloudy')
        self.assertIn('Hourly.28.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.28.OutlookIcon'], '29.png')

        self.assertIn('Hourly.29.Time', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.29.Time'], '00:00')
        self.assertIn('Hourly.29.Temperature', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.29.Temperature'], '4' + self.constants.TEMPERATUREUNITS)
        self.assertIn('Hourly.29.FeelsLikeTemp', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.29.FeelsLikeTemp'], '1')
        self.assertIn('Hourly.29.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.29.WindSpeed'], '9')
        self.assertIn('Hourly.29.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.29.WindDirection'], 'sw')
        self.assertIn('Hourly.29.GustSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.29.GustSpeed'], '16')
        self.assertIn('Hourly.29.UVIndex', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.29.UVIndex'], '0')
        self.assertIn('Hourly.29.Precipitation', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.29.Precipitation'], '16%')
        self.assertIn('Hourly.29.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.29.Outlook'], 'Cloudy')
        self.assertIn('Hourly.29.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.29.OutlookIcon'], '26.png')

        self.assertIn('Hourly.30.Time', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.30.Time'], '03:00')
        self.assertIn('Hourly.30.Temperature', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.30.Temperature'], '4' + self.constants.TEMPERATUREUNITS)
        self.assertIn('Hourly.30.FeelsLikeTemp', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.30.FeelsLikeTemp'], '1')
        self.assertIn('Hourly.30.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.30.WindSpeed'], '9')
        self.assertIn('Hourly.30.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.30.WindDirection'], 'sw')
        self.assertIn('Hourly.30.GustSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.30.GustSpeed'], '16')
        self.assertIn('Hourly.30.UVIndex', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.30.UVIndex'], '0')
        self.assertIn('Hourly.30.Precipitation', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.30.Precipitation'], '23%')
        self.assertIn('Hourly.30.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.30.Outlook'], 'Cloudy')
        self.assertIn('Hourly.30.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.30.OutlookIcon'], '26.png')

        self.assertIn('Hourly.31.Time', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.31.Time'], '06:00')
        self.assertIn('Hourly.31.Temperature', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.31.Temperature'], '4' + self.constants.TEMPERATUREUNITS)
        self.assertIn('Hourly.31.FeelsLikeTemp', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.31.FeelsLikeTemp'], '1')
        self.assertIn('Hourly.31.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.31.WindSpeed'], '11')
        self.assertIn('Hourly.31.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.31.WindDirection'], 'sw')
        self.assertIn('Hourly.31.GustSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.31.GustSpeed'], '20')
        self.assertIn('Hourly.31.UVIndex', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.31.UVIndex'], '0')
        self.assertIn('Hourly.31.Precipitation', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.31.Precipitation'], '24%')
        self.assertIn('Hourly.31.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.31.Outlook'], 'Overcast')
        self.assertIn('Hourly.31.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.31.OutlookIcon'], '26.png')

        self.assertIn('Hourly.32.Time', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.32.Time'], '09:00')
        self.assertIn('Hourly.32.Temperature', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.32.Temperature'], '6' + self.constants.TEMPERATUREUNITS)
        self.assertIn('Hourly.32.FeelsLikeTemp', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.32.FeelsLikeTemp'], '2')
        self.assertIn('Hourly.32.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.32.WindSpeed'], '13')
        self.assertIn('Hourly.32.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.32.WindDirection'], 'wsw')
        self.assertIn('Hourly.32.GustSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.32.GustSpeed'], '29')
        self.assertIn('Hourly.32.UVIndex', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.32.UVIndex'], '1')
        self.assertIn('Hourly.32.Precipitation', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.32.Precipitation'], '55%')
        self.assertIn('Hourly.32.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.32.Outlook'], 'Light Rain')
        self.assertIn('Hourly.32.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.32.OutlookIcon'], '11.png')

        self.assertIn('Hourly.33.Time', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.33.Time'], '12:00')
        self.assertIn('Hourly.33.Temperature', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.33.Temperature'], '8' + self.constants.TEMPERATUREUNITS)
        self.assertIn('Hourly.33.FeelsLikeTemp', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.33.FeelsLikeTemp'], '3')
        self.assertIn('Hourly.33.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.33.WindSpeed'], '18')
        self.assertIn('Hourly.33.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.33.WindDirection'], 'w')
        self.assertIn('Hourly.33.GustSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.33.GustSpeed'], '38')
        self.assertIn('Hourly.33.UVIndex', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.33.UVIndex'], '1')
        self.assertIn('Hourly.33.Precipitation', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.33.Precipitation'], '37%')
        self.assertIn('Hourly.33.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.33.Outlook'], 'Light Rain')
        self.assertIn('Hourly.33.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.33.OutlookIcon'], '11.png')

        self.assertIn('Hourly.34.Time', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.34.Time'], '15:00')
        self.assertIn('Hourly.34.Temperature', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.34.Temperature'], '8' + self.constants.TEMPERATUREUNITS)
        self.assertIn('Hourly.34.FeelsLikeTemp', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.34.FeelsLikeTemp'], '3')
        self.assertIn('Hourly.34.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.34.WindSpeed'], '18')
        self.assertIn('Hourly.34.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.34.WindDirection'], 'w')
        self.assertIn('Hourly.34.GustSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.34.GustSpeed'], '36')
        self.assertIn('Hourly.34.UVIndex', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.34.UVIndex'], '1')
        self.assertIn('Hourly.34.Precipitation', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.34.Precipitation'], '14%')
        self.assertIn('Hourly.34.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.34.Outlook'], 'Partly Cloudy')
        self.assertIn('Hourly.34.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.34.OutlookIcon'], '30.png')

        self.assertIn('Hourly.35.Time', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.35.Time'], '18:00')
        self.assertIn('Hourly.35.Temperature', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.35.Temperature'], '7' + self.constants.TEMPERATUREUNITS)
        self.assertIn('Hourly.35.FeelsLikeTemp', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.35.FeelsLikeTemp'], '2')
        self.assertIn('Hourly.35.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.35.WindSpeed'], '13')
        self.assertIn('Hourly.35.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.35.WindDirection'], 'w')
        self.assertIn('Hourly.35.GustSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.35.GustSpeed'], '27')
        self.assertIn('Hourly.35.UVIndex', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.35.UVIndex'], '0')
        self.assertIn('Hourly.35.Precipitation', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.35.Precipitation'], '6%')
        self.assertIn('Hourly.35.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.35.Outlook'], 'Partly Cloudy')
        self.assertIn('Hourly.35.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.35.OutlookIcon'], '29.png')

        self.assertIn('Hourly.36.Time', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.36.Time'], '21:00')
        self.assertIn('Hourly.36.Temperature', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.36.Temperature'], '5' + self.constants.TEMPERATUREUNITS)
        self.assertIn('Hourly.36.FeelsLikeTemp', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.36.FeelsLikeTemp'], '1')
        self.assertIn('Hourly.36.WindSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.36.WindSpeed'], '13')
        self.assertIn('Hourly.36.WindDirection', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.36.WindDirection'], 'wsw')
        self.assertIn('Hourly.36.GustSpeed', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.36.GustSpeed'], '25')
        self.assertIn('Hourly.36.UVIndex', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.36.UVIndex'], '0')
        self.assertIn('Hourly.36.Precipitation', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.36.Precipitation'], '7%')
        self.assertIn('Hourly.36.Outlook', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.36.Outlook'], 'Partly Cloudy')
        self.assertIn('Hourly.36.OutlookIcon', self.window_properties)
        self.assertEqual(self.window_properties['Hourly.36.OutlookIcon'], '29.png')

        # Test exception handling when given json without proper keys
        mock_cache.return_value.__enter__.return_value.get = Mock(return_value=EMPTY_FILE)
        with self.assertRaises(KeyError) as cm:
            properties.threehourly()
        self.assertEqual(('Key Error in JSON File',
                          "Key 'SiteRep' not found while processing file from url:",
                          self.constants.THREEHOURLY_LOCATION_FORECAST_URL), cm.exception.args)

    def test_sunrise(self):
        # Set a dummy latitude, longitude
        from metoffice import properties
        properties.sunrisesunset()
        self.assertIn('Today.Sunrise', self.window_properties)
        self.assertTrue(re.match(r'\d\d:\d\d', self.window_properties['Today.Sunrise']))
        self.assertIn('Today.Sunset', self.window_properties)
        self.assertTrue(re.match(r'\d\d:\d\d', self.window_properties['Today.Sunset']))

    @patch('metoffice.utilities.panelbusy')
    @patch('metoffice.urlcache.URLCache')
    def test_text(self, mock_cache, mock_panelbusy):
        mock_panelbusy.side_effect = self.mock_panelbusy
        mock_cache.return_value.__enter__.return_value.get = Mock(side_effect=self.mock_get)
        from metoffice import properties
        properties.text()
        self.assertIn('TextForecast.IssuedAt', self.window_properties)
        self.assertEqual(self.window_properties['TextForecast.IssuedAt'], '16:00 Mon 24 Feb 2014')

        self.assertIn('Text.Paragraph0.Title', self.window_properties)
        self.assertEqual(self.window_properties['Text.Paragraph0.Title'], 'Headline')
        self.assertIn('Text.Paragraph0.Content', self.window_properties)
        self.assertEqual(self.window_properties['Text.Paragraph0.Content'],
                         'Rain clearing eastwards, showers following, with increasing winds.')
        self.assertIn('Text.Paragraph1.Title', self.window_properties)
        self.assertEqual(self.window_properties['Text.Paragraph1.Title'], 'This Evening and Tonight')
        self.assertIn('Text.Paragraph1.Content', self.window_properties)
        self.assertEqual(self.window_properties['Text.Paragraph1.Content'],
                         ('Rain arriving in the far west around dusk will clear eastwards overnight, '
                          'this heaviest in the west and over high ground, where winds will also become '
                          'strong. Mild, with clear spells and scattered showers following. Minimum '
                          'Temperature 5C.'))
        self.assertIn('Text.Paragraph2.Title', self.window_properties)
        self.assertEqual(self.window_properties['Text.Paragraph2.Title'], 'Tuesday')
        self.assertIn('Text.Paragraph2.Content', self.window_properties)
        self.assertEqual(self.window_properties['Text.Paragraph2.Content'],
                         ('Some dry and bright weather is likely at times but also scattered blustery, '
                          'heavy showers. Remaining windy, especially around exposed coasts and hills '
                          'where gales are likely. Maximum Temperature 9C.'))
        self.assertIn('Text.Paragraph3.Title', self.window_properties)
        self.assertEqual(self.window_properties['Text.Paragraph3.Title'], 'Wednesday to Friday')
        self.assertIn('Text.Paragraph3.Content', self.window_properties)
        self.assertEqual(self.window_properties['Text.Paragraph3.Content'],
                         ('Sunny spells and lighter winds on Wednesday, some showers along the coast. '
                          'Wet and windy overnight, turning showery on Thursday and Friday, becoming '
                          'wintry over hills.'))
        self.assertIn('Text.Paragraph4.Title', self.window_properties)
        self.assertEqual(self.window_properties['Text.Paragraph4.Title'], 'Saturday 1 Mar 2014 to Monday 10 Mar 2014')
        self.assertIn('Text.Paragraph4.Content', self.window_properties)
        self.assertEqual(self.window_properties['Text.Paragraph4.Content'],
                         ('The weekend will start unsettled with showers or longer spells of rain, with '
                          'some heavier bursts at first. This will be most persistent in the far southeast '
                          'and far north, with a risk of hill snow in the north. There will be some drier '
                          'slots too, especially on Sunday with a risk of local frost and icy surfaces. '
                          'Temperatures near normal. Through the next week it will remain unsettled in '
                          'northern parts, with further rain or showers, and some hill snow. It will be '
                          'mainly dry but fairly cloudy towards the south with isolated patchy frost. '
                          'During the middle part of the week rain may spread southwards for a time, '
                          'before turning wet and windy in the northwest again later, with a risk of gales.'))
        self.assertIn('Text.Paragraph5.Title', self.window_properties)
        self.assertEqual(self.window_properties['Text.Paragraph5.Title'], 'Tuesday 11 Mar 2014 to Tuesday 25 Mar 2014')
        self.assertIn('Text.Paragraph5.Content', self.window_properties)
        self.assertEqual(self.window_properties['Text.Paragraph5.Content'],
                         ('Current indications suggest a more typically unsettled pattern across the '
                          'United Kingdom through much of March. Through this period we can expect to '
                          'see fairly average conditions, which would mean spells of wet and windy '
                          'weather, mostly in the north and west, but still some decent sunny spells '
                          'in between. The best of the drier, brighter conditions is most likely in the '
                          'south and east of the UK. Temperatures are likely to be around average, which '
                          'may lead to more frequent incidences of frost compared to recent weeks.'))

        # Test exception handling when given json without proper keys
        mock_cache.return_value.__enter__.return_value.get = Mock(return_value=EMPTY_FILE)
        with self.assertRaises(KeyError) as cm:
            properties.text()
        self.assertEqual(('Key Error in JSON File',
                          "Key 'RegionalFcst' not found while processing file from url:",
                          self.constants.TEXT_FORECAST_URL), cm.exception.args)

    @patch('metoffice.utilities.panelbusy')
    @patch('metoffice.urlcache.URLCache')
    def test_forecastlayer(self, mock_cache, mock_panelbusy):
        mock_panelbusy.side_effect = self.mock_panelbusy
        mock_cache.return_value.__enter__.return_value.get = Mock(side_effect=self.mock_get)

        from metoffice import properties
        properties.forecastlayer()
        self.assertIn('ForecastMap.Surface', self.window_properties)
        self.assertEqual(self.window_properties['ForecastMap.Surface'], GOOGLE_SURFACE_IMAGE)
        self.assertIn('ForecastMap.Marker', self.window_properties)
        self.assertEqual(self.window_properties['ForecastMap.Marker'], GOOGLE_MARKER_IMAGE)
        self.assertIn('ForecastMap.Slider', self.window_properties)
        self.assertEqual(self.window_properties['ForecastMap.Slider'], '0')
        self.assertIn('ForecastMap.IssuedAt', self.window_properties)
        self.assertEqual(self.window_properties['ForecastMap.IssuedAt'], '09:00 Wed 19 Mar 2014')
        self.assertIn('ForecastMap.MapTime', self.window_properties)
        self.assertEqual(self.window_properties['ForecastMap.MapTime'], '0900 Wed')
        self.assertIn('ForecastMap.Layer', self.window_properties)
        self.assertEqual(self.window_properties['ForecastMap.Layer'], PRECIPITATION_LAYER_IMAGE)
        self.assertIn('ForecastMap.IsFetched', self.window_properties)
        self.assertEqual(self.window_properties['ForecastMap.IsFetched'], 'true')

        # Test exception handling when given json without proper keys
        mock_cache.return_value.__enter__.return_value.get = Mock(return_value=EMPTY_FILE)
        with self.assertRaises(KeyError) as cm:
            properties.forecastlayer()
        self.assertEqual(('Key Error in JSON File',
                          "Key 'Layers' not found while processing file from url:",
                          self.constants.FORECAST_LAYER_CAPABILITIES_URL), cm.exception.args)

        # Test exception handling when given corrupt BaseURL in json
        # (We have provide partially valid json so execution can drop to the exception under test.)
        mock_cache.return_value.__enter__.return_value.get = Mock(return_value=CORRUPTFORECASTLAYERCAPABILITIES)
        with self.assertRaises(KeyError) as cm:
            properties.forecastlayer()
        self.assertEqual(('Key Error in JSON File',
                          "Key '$' not found while processing file from url:",
                          self.constants.FORECAST_LAYER_CAPABILITIES_URL), cm.exception.args)

        mock_cache.return_value.__enter__.return_value.get = Mock(side_effect=self.mock_get)
        mock_cache.reset_mock()

        # Test valid url is used when requesting with an invalid slider position
        properties.FORECASTMAP_SLIDER = '-9'
        properties.forecastlayer()
        self.assertEqual(PRECIPITATION_LAYER_HOUR0_URL,
                         mock_cache.return_value.__enter__.return_value.get.call_args_list[3][0][0])

        mock_cache.reset_mock()
        properties.FORECASTMAP_SLIDER = '45'
        properties.forecastlayer()
        self.assertEqual(PRECIPITATION_LAYER_HOUR36_URL,
                         mock_cache.return_value.__enter__.return_value.get.call_args_list[3][0][0])

        # Test response when given unknown layer name
        properties.FORECASTMAP_LAYER_SELECTION = 'Unknown'
        with self.assertRaises(Exception) as cm:
            properties.forecastlayer()
        self.assertEqual(('Error', "Couldn't find layer 'Unknown'"), cm.exception.args)

    @patch('metoffice.utilities.panelbusy')
    @patch('metoffice.urlcache.URLCache')
    def test_observationlayer(self, mock_cache, mock_panelbusy):
        mock_panelbusy.side_effect = self.mock_panelbusy
        mock_cache.return_value.__enter__.return_value.get = Mock(side_effect=self.mock_get)

        from metoffice import properties
        properties.observationlayer()
        self.assertIn('ObservationMap.Surface', self.window_properties)
        self.assertEqual(self.window_properties['ObservationMap.Surface'], GOOGLE_SURFACE_IMAGE)
        self.assertIn('ObservationMap.Marker', self.window_properties)
        self.assertEqual(self.window_properties['ObservationMap.Marker'], GOOGLE_MARKER_IMAGE)
        self.assertIn('ObservationMap.Slider', self.window_properties)
        self.assertEqual(self.window_properties['ObservationMap.Slider'], '0')
        self.assertIn('ObservationMap.IssuedAt', self.window_properties)
        self.assertEqual(self.window_properties['ObservationMap.IssuedAt'], '17:30 Tue 01 Apr 2014')
        self.assertIn('ObservationMap.MapTime', self.window_properties)
        self.assertEqual(self.window_properties['ObservationMap.MapTime'], '1730 Tue')
        self.assertIn('ObservationMap.Layer', self.window_properties)
        self.assertEqual(self.window_properties['ObservationMap.Layer'], PRECIPITATION_LAYER_IMAGE)
        self.assertIn('ObservationMap.IsFetched', self.window_properties)
        self.assertEqual(self.window_properties['ObservationMap.IsFetched'], 'true')

        # Test exception handling when given json without proper keys
        mock_cache.return_value.__enter__.return_value.get = Mock(return_value=EMPTY_FILE)
        with self.assertRaises(KeyError) as cm:
            properties.observationlayer()
        self.assertEqual(('Key Error in JSON File',
                          "Key 'Layers' not found while processing file from url:",
                          self.constants.OBSERVATION_LAYER_CAPABILITIES_URL), cm.exception.args)

        # Test exception handling when given corrupt BaseURL in json
        # (We have provide partially valid json so execution can drop to the exception under test.)
        mock_cache.return_value.__enter__.return_value.get = Mock(return_value=CORRUPTOBSERVATIONLAYERCAPABILITIES)
        with self.assertRaises(KeyError) as cm:
            properties.observationlayer()
        self.assertEqual(('Key Error in JSON File',
                          "Key '$' not found while processing file from url:",
                          self.constants.OBSERVATION_LAYER_CAPABILITIES_URL), cm.exception.args)

        mock_cache.return_value.__enter__.return_value.get = Mock(side_effect=self.mock_get)
        mock_cache.reset_mock()

        # Test valid url is used when requesting with an invalid slider position
        properties.OBSERVATIONMAP_SLIDER = '-9'
        properties.observationlayer()
        self.assertEqual(OBSERVATION_LAYER0_URL,
                         mock_cache.return_value.__enter__.return_value.get.call_args_list[3][0][0])

        mock_cache.reset_mock()
        properties.OBSERVATIONMAP_SLIDER = '45'
        properties.observationlayer()
        self.assertEqual(OBSERVATION_LAYER1_URL,
                         mock_cache.return_value.__enter__.return_value.get.call_args_list[3][0][0])

        # Test response when given unknown layer name
        properties.OBSERVATIONMAP_LAYER_SELECTION = 'Unknown'
        with self.assertRaises(Exception) as cm:
            properties.observationlayer()
        self.assertEqual(('Error', "Couldn't find layer 'Unknown'"), cm.exception.args)

    @patch('metoffice.utilities.panelbusy')
    @patch('metoffice.urlcache.URLCache')
    def test_daily_expiry(self, mock_cache, mock_panelbusy):
        mock_panelbusy.side_effect = self.mock_panelbusy
        mock_cache.return_value.__enter__.return_value.get = Mock(side_effect=self.mock_get)
        from metoffice import properties
        result = properties.daily_expiry(FORECASTDAILY)
        self.assertEqual(datetime.datetime(2014, 2, 24, 15, 30), result)

    @patch('metoffice.utilities.panelbusy')
    @patch('metoffice.urlcache.URLCache')
    def test_threehourly_expiry(self, mock_cache, mock_panelbusy):
        mock_panelbusy.side_effect = self.mock_panelbusy
        mock_cache.return_value.__enter__.return_value.get = Mock(side_effect=self.mock_get)
        from metoffice import properties
        result = properties.threehourly_expiry(FORECAST3HOURLY)
        self.assertEqual(datetime.datetime(2014, 3, 1, 17, 30), result)

    @patch('metoffice.utilities.panelbusy')
    @patch('metoffice.urlcache.URLCache')
    def test_text_expiry(self, mock_cache, mock_panelbusy):
        mock_panelbusy.side_effect = self.mock_panelbusy
        mock_cache.return_value.__enter__.return_value.get = Mock(side_effect=self.mock_get)
        from metoffice import properties
        result = properties.text_expiry(FORECASTTEXT)
        self.assertEqual(datetime.datetime(2014, 2, 25, 4, 0), result)

    @patch('metoffice.utilities.panelbusy')
    @patch('metoffice.urlcache.URLCache')
    def test_observation_expiry(self, mock_cache, mock_panelbusy):
        mock_panelbusy.side_effect = self.mock_panelbusy
        mock_cache.return_value.__enter__.return_value.get = Mock(side_effect=self.mock_get)
        from metoffice import properties
        result = properties.observation_expiry(OBSERVATIONHOURLY)
        self.assertEqual(datetime.datetime(2014, 3, 6, 18, 30), result)

    @patch('metoffice.utilities.panelbusy')
    @patch('metoffice.urlcache.URLCache')
    def test_forecastlayer_capabilities_expiry(self, mock_cache, mock_panelbusy):
        mock_panelbusy.side_effect = self.mock_panelbusy
        mock_cache.return_value.__enter__.return_value.get = Mock(side_effect=self.mock_get)
        from metoffice import properties
        result = properties.forecastlayer_capabilities_expiry(FORECASTLAYERCAPABILITIES)
        self.assertEqual(datetime.datetime(2014, 3, 19, 18, 0), result)

    @patch('metoffice.utilities.panelbusy')
    @patch('metoffice.urlcache.URLCache')
    def test_observationlayer_capabilities_expiry(self, mock_cache, mock_panelbusy):
        mock_panelbusy.side_effect = self.mock_panelbusy
        mock_cache.return_value.__enter__.return_value.get = Mock(side_effect=self.mock_get)
        from metoffice import properties
        result = properties.observationlayer_capabilities_expiry(OBSERVATIONLAYERCAPABILITIES)
        self.assertEqual(datetime.datetime(2014, 4, 1, 17, 0), result)

    @patch('metoffice.utilities.panelbusy')
    @patch('metoffice.urlcache.URLCache')
    def test_layer_image_resize_callback(self, mock_cache, mock_panelbusy):
        mock_panelbusy.side_effect = self.mock_panelbusy
        mock_cache.return_value.__enter__.return_value.get = Mock(side_effect=self.mock_get)

        # Assert that the pretend image in cache has not been resized
        with Image.open(PRECIPITATION_LAYER_IMAGE) as img:
            (width, height) = img.size
        self.assertEqual(500, width)
        self.assertEqual(500, height)

        from metoffice import properties
        properties.image_resize(PRECIPITATION_LAYER_IMAGE)
        with Image.open(PRECIPITATION_LAYER_IMAGE) as img:
            (width, height) = img.size
        self.assertEqual(420, width)
        self.assertEqual(460, height)

    def tearDown(self):
        super(TestProperties, self).tearDown()
        shutil.rmtree(RESULTS_FOLDER)
