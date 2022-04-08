import os
import re
import shutil
import datetime
from PIL import Image
from unittest.mock import Mock, patch
from unittest import TestCase

import xbmc

from metoffice import constants, properties

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


def mock_get_region(id):
    region_settings = {
        'tempunit': 'C'
    }
    return region_settings[id]


class Addon():
    # Move to a dedicated mocks package.
    def __init__(self, settings):
        if settings is None:
            settings = {}
        self._settings = settings

    def getSetting(self, key):
        return self._settings[key]

    def setSetting(self, key, value):
        self._settings[key] = value


class Window():
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

        window = Window({
            'ForecastMap.LayerSelection': 'Rainfall',
            'ObservationMap.LayerSelection': 'Rainfall',
            'ForecastMap.Slider': '0',
            'ObservationMap.Slider': '0',
            'Weather.CurrentView': 'Doesnt matter'
        })
        window_patcher = patch('metoffice.properties.WINDOW', new=window)
        self.addCleanup(window_patcher.stop)
        window_patcher.start()

        addon = Addon({
            'ApiKey': '12345',
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
        })
        addon_patcher = patch('metoffice.constants.ADDON', new=addon)
        self.addCleanup(addon_patcher.stop)
        addon_patcher.start()

        xbmc.getRegion = Mock(side_effect=mock_get_region)

        # create a disposable area for testing
        try:
            os.mkdir(RESULTS_FOLDER)
        except OSError:
            pass

        shutil.copy(os.path.join(DATA_FOLDER, 'precipitation_layer.png'),
                    os.path.join(RESULTS_FOLDER, 'precipitation_layer.png'))

    def mock_get(self, url, expiry_callback, resource_callback=None):
        cache = {
            constants.FORECAST_SITELIST_URL: FORECASTSITELIST,
            constants.DAILY_LOCATION_FORECAST_URL: FORECASTDAILY,
            constants.THREEHOURLY_LOCATION_FORECAST_URL: FORECAST3HOURLY,
            constants.FORECAST_LAYER_CAPABILITIES_URL: FORECASTLAYERCAPABILITIES,
            constants.OBSERVATION_LAYER_CAPABILITIES_URL: OBSERVATIONLAYERCAPABILITIES,
            constants.TEXT_FORECAST_URL: FORECASTTEXT,
            constants.HOURLY_LOCATION_OBSERVATION_URL: OBSERVATIONHOURLY,
            constants.GEOIP_PROVIDER['url']: GEOIP,
            constants.GOOGLE_SURFACE: GOOGLE_SURFACE_IMAGE,
            constants.GOOGLE_MARKER: GOOGLE_MARKER_IMAGE,
            PRECIPITATION_LAYER_HOUR0_URL: PRECIPITATION_LAYER_IMAGE,
            PRECIPITATION_LAYER_HOUR36_URL: PRECIPITATION_LAYER_IMAGE,
            OBSERVATION_LAYER0_URL: PRECIPITATION_LAYER_IMAGE,
            OBSERVATION_LAYER1_URL: PRECIPITATION_LAYER_IMAGE,
        }
        return cache[url]

    @patch('metoffice.urlcache.URLCache')
    def test_observation(self, mock_cache):
        mock_cache.return_value.__enter__.return_value.get = Mock(side_effect=self.mock_get)

        properties.observation()
        issued_at = properties.WINDOW.getProperty('HourlyObservation.IssuedAt')
        self.assertEqual(issued_at, '17:00 Thu 06 Mar 2014')
        condition = properties.WINDOW.getProperty('Current.Condition')
        self.assertEqual(condition, 'Cloudy')
        visibility = properties.WINDOW.getProperty('Current.Visibility')
        self.assertEqual(visibility, '45000')
        pressure = properties.WINDOW.getProperty('Current.Pressure')
        self.assertEqual(pressure, '1021')
        temperature = properties.WINDOW.getProperty('Current.Temperature')
        self.assertEqual(temperature, '10')
        wind = properties.WINDOW.getProperty('Current.Wind')
        self.assertEqual(wind, '23.0')
        direction = properties.WINDOW.getProperty('Current.WindDirection')
        self.assertEqual(direction, 'SW')
        gust = properties.WINDOW.getProperty('Current.WindGust')
        self.assertEqual(gust, 'n/a')
        outlook_icon = properties.WINDOW.getProperty('Current.OutlookIcon')
        self.assertEqual(outlook_icon, '26.png')
        fanart_Code = properties.WINDOW.getProperty('Current.OutlookIcon')
        self.assertEqual(fanart_Code, '26.png')
        dew_point = properties.WINDOW.getProperty('Current.DewPoint')
        self.assertEqual(dew_point, '6')
        humidity = properties.WINDOW.getProperty('Current.Humidity')
        self.assertEqual(humidity, '79')

    @patch('metoffice.urlcache.URLCache')
    def test_observation_missing(self, mock_cache):
        # Test the cases when reports don't contain list items.
        mock_cache.return_value.__enter__.return_value.get = Mock(return_value=OBSERVATIONHOURLY2)

        properties.observation()
        issued_at = properties.WINDOW.getProperty('HourlyObservation.IssuedAt')
        self.assertEqual(issued_at, '17:00 Thu 06 Mar 2014')
        condition = properties.WINDOW.getProperty('Current.Condition')
        self.assertEqual(condition, 'Sunny')
        visibility = properties.WINDOW.getProperty('Current.Visibility')
        self.assertEqual(visibility, '45000')
        pressure = properties.WINDOW.getProperty('Current.Pressure')
        self.assertEqual(pressure, '1021')
        temperature = properties.WINDOW.getProperty('Current.Temperature')
        self.assertEqual(temperature, '10')
        wind = properties.WINDOW.getProperty('Current.Wind')
        self.assertEqual(wind, '16.0')
        wind_direction = properties.WINDOW.getProperty('Current.WindDirection')
        self.assertEqual(wind_direction, 'WSW')
        wind_gust = properties.WINDOW.getProperty('Current.WindGust')
        self.assertEqual(wind_gust, 'n/a')
        outlook_icon = properties.WINDOW.getProperty('Current.OutlookIcon')
        self.assertEqual(outlook_icon, '32.png')
        fanart_code = properties.WINDOW.getProperty('Current.FanartCode')
        self.assertEqual(fanart_code, '32.png')
        dew_point = properties.WINDOW.getProperty('Current.DewPoint')
        self.assertEqual(dew_point, '4')
        humidity = properties.WINDOW.getProperty('Current.Humidity')
        self.assertEqual(humidity, '66')

        # Test exception handling when given json without proper keys
        mock_cache.return_value.__enter__.return_value.get = Mock(return_value=EMPTY_FILE)
        with self.assertRaises(KeyError) as cm:
            properties.observation()
        self.assertEqual(('Key Error in JSON File',
                          "Key 'SiteRep' not found while processing file from url:",
                          constants.HOURLY_LOCATION_OBSERVATION_URL), cm.exception.args)

    @patch('metoffice.urlcache.URLCache')
    @patch('metoffice.utilities.TEMPERATUREUNITS', 'C')
    def test_daily(self, mock_cache):
        mock_cache.return_value.__enter__.return_value.get = Mock(side_effect=self.mock_get)

        properties.daily()
        issued_at = properties.WINDOW.getProperty('DailyForecast.IssuedAt')
        self.assertEqual(issued_at, '14:00 Mon 24 Feb 2014')

        day0_title = properties.WINDOW.getProperty('Day0.Title')
        self.assertEqual(day0_title, 'Mon')
        day0_high_temp = properties.WINDOW.getProperty('Day0.HighTemp')
        self.assertEqual(day0_high_temp, '13')
        day0_low_temp = properties.WINDOW.getProperty('Day0.LowTemp')
        self.assertEqual(day0_low_temp, '7')
        day0_wind_speed = properties.WINDOW.getProperty('Day0.WindSpeed')
        self.assertEqual(day0_wind_speed, '13')
        day0_wind_direction = properties.WINDOW.getProperty('Day0.WindDirection')
        self.assertEqual(day0_wind_direction, 'ssw')
        day0_outlook = properties.WINDOW.getProperty('Day0.Outlook')
        self.assertEqual(day0_outlook, 'Light Rain')
        day0_outlook_icon = properties.WINDOW.getProperty('Day0.OutlookIcon')
        self.assertEqual(day0_outlook_icon, '11.png')

        day1_title = properties.WINDOW.getProperty('Day1.Title')
        self.assertEqual(day1_title, 'Tue')
        day1_high_temp = properties.WINDOW.getProperty('Day1.HighTemp')
        self.assertEqual(day1_high_temp, '12')
        day1_low_temp = properties.WINDOW.getProperty('Day1.LowTemp')
        self.assertEqual(day1_low_temp, '3')
        day1_wind_speed = properties.WINDOW.getProperty('Day1.WindSpeed')
        self.assertEqual(day1_wind_speed, '18')
        day1_wind_direction = properties.WINDOW.getProperty('Day1.WindDirection')
        self.assertEqual(day1_wind_direction, 'ssw')
        day1_outlook = properties.WINDOW.getProperty('Day1.Outlook')
        self.assertEqual(day1_outlook, 'Sunny')
        day1_outlook_icon = properties.WINDOW.getProperty('Day1.OutlookIcon')
        self.assertEqual(day1_outlook_icon, '32.png')

        day2_title = properties.WINDOW.getProperty('Day2.Title')
        self.assertEqual(day2_title, 'Wed')
        day2_high_temp = properties.WINDOW.getProperty('Day2.HighTemp')
        self.assertEqual(day2_high_temp, '11')
        day2_low_temp = properties.WINDOW.getProperty('Day2.LowTemp')
        self.assertEqual(day2_low_temp, '4')
        day2_wind_speed = properties.WINDOW.getProperty('Day2.WindSpeed')
        self.assertEqual(day2_wind_speed, '13')
        day2_wind_direction = properties.WINDOW.getProperty('Day2.WindDirection')
        self.assertEqual(day2_wind_direction, 'wsw')
        day2_outlook = properties.WINDOW.getProperty('Day2.Outlook')
        self.assertEqual(day2_outlook, 'Sunny')
        day2_outlook_icon = properties.WINDOW.getProperty('Day2.OutlookIcon')
        self.assertEqual(day2_outlook_icon, '32.png')

        day3_title = properties.WINDOW.getProperty('Day3.Title')
        self.assertEqual(day3_title, 'Thu')
        day3_high_temp = properties.WINDOW.getProperty('Day3.HighTemp')
        self.assertEqual(day3_high_temp, '11')
        day3_low_temp = properties.WINDOW.getProperty('Day3.LowTemp')
        self.assertEqual(day3_low_temp, '3')
        day3_wind_speed = properties.WINDOW.getProperty('Day3.WindSpeed')
        self.assertEqual(day3_wind_speed, '16')
        day3_wind_direction = properties.WINDOW.getProperty('Day3.WindDirection')
        self.assertEqual(day3_wind_direction, 'wsw')
        day3_outlook = properties.WINDOW.getProperty('Day3.Outlook')
        self.assertEqual(day3_outlook, 'Heavy Rain')
        day3_outlook_icon = properties.WINDOW.getProperty('Day3.OutlookIcon')
        self.assertEqual(day3_outlook_icon, '40.png')

        day4_title = properties.WINDOW.getProperty('Day4.Title')
        self.assertEqual(day4_title, 'Fri')
        day4_high_temp = properties.WINDOW.getProperty('Day4.HighTemp')
        self.assertEqual(day4_high_temp, '9')
        day4_low_temp = properties.WINDOW.getProperty('Day4.LowTemp')
        self.assertEqual(day4_low_temp, '2')
        day4_wind_speed = properties.WINDOW.getProperty('Day4.WindSpeed')
        self.assertEqual(day4_wind_speed, '11')
        day4_wind_direction = properties.WINDOW.getProperty('Day4.WindDirection')
        self.assertEqual(day4_wind_direction, 'sw')
        day4_outlook = properties.WINDOW.getProperty('Day4.Outlook')
        self.assertEqual(day4_outlook, 'Light Rain')
        day4_outlook_icon = properties.WINDOW.getProperty('Day4.OutlookIcon')
        self.assertEqual(day4_outlook_icon, '11.png')

        # Test exception handling when given json without proper keys
        mock_cache.return_value.__enter__.return_value.get = Mock(return_value=EMPTY_FILE)
        with self.assertRaises(KeyError) as cm:
            properties.daily()
        self.assertEqual(('Key Error in JSON File',
                          "Key 'SiteRep' not found while processing file from url:",
                          constants.DAILY_LOCATION_FORECAST_URL), cm.exception.args)

    @patch('metoffice.urlcache.URLCache')
    @patch('metoffice.utilities.TEMPERATUREUNITS', 'C')
    def test_threehourly(self, mock_cache):
        # This test is a bit long and cumbersome. TODO: Figure out how to cut it down.
        mock_cache.return_value.__enter__.return_value.get = Mock(side_effect=self.mock_get)

        properties.threehourly()
        issued_at = properties.WINDOW.getProperty('3HourlyForecast.IssuedAt')
        self.assertEqual(issued_at, '16:00 Sat 01 Mar 2014')
        time = properties.WINDOW.getProperty('Hourly.1.Time')
        self.assertEqual(time, '12:00')
        temperature = properties.WINDOW.getProperty('Hourly.1.Temperature')
        self.assertEqual(temperature, '6' + constants.TEMPERATUREUNITS)
        feelslike = properties.WINDOW.getProperty('Hourly.1.FeelsLikeTemp')
        self.assertEqual(feelslike, '4')
        windspeed = properties.WINDOW.getProperty('Hourly.1.WindSpeed')
        self.assertEqual(windspeed, '4')
        direction = properties.WINDOW.getProperty('Hourly.1.WindDirection')
        self.assertEqual(direction, 'nnw')
        gust = properties.WINDOW.getProperty('Hourly.1.GustSpeed')
        self.assertEqual(gust, '7')
        uvindex = properties.WINDOW.getProperty('Hourly.1.UVIndex')
        self.assertEqual(uvindex, '1')
        precipitation = properties.WINDOW.getProperty('Hourly.1.Precipitation')
        self.assertEqual(precipitation, '6%')
        outlook = properties.WINDOW.getProperty('Hourly.1.Outlook')
        self.assertEqual(outlook, 'Cloudy')
        icon = properties.WINDOW.getProperty('Hourly.1.OutlookIcon')
        self.assertEqual(icon, '26.png')

        time = properties.WINDOW.getProperty('Hourly.2.Time')
        self.assertEqual(time, '15:00')
        temperature = properties.WINDOW.getProperty('Hourly.2.Temperature')
        self.assertEqual(temperature, '8' + constants.TEMPERATUREUNITS)
        feelsliketemp = properties.WINDOW.getProperty('Hourly.2.FeelsLikeTemp')
        self.assertEqual(feelsliketemp, '6')
        windspeed = properties.WINDOW.getProperty('Hourly.2.WindSpeed')
        self.assertEqual(windspeed, '7')
        winddirection = properties.WINDOW.getProperty('Hourly.2.WindDirection')
        self.assertEqual(winddirection, 'wsw')
        gustspeed = properties.WINDOW.getProperty('Hourly.2.GustSpeed')
        self.assertEqual(gustspeed, '11')
        uvindex = properties.WINDOW.getProperty('Hourly.2.UVIndex')
        self.assertEqual(uvindex, '1')
        precipitation = properties.WINDOW.getProperty('Hourly.2.Precipitation')
        self.assertEqual(precipitation, '6%')
        outlook = properties.WINDOW.getProperty('Hourly.2.Outlook')
        self.assertEqual(outlook, 'Cloudy')
        outlookicon = properties.WINDOW.getProperty('Hourly.2.OutlookIcon')
        self.assertEqual(outlookicon, '26.png')

        time = properties.WINDOW.getProperty('Hourly.3.Time')
        self.assertEqual(time, '18:00')
        temperature = properties.WINDOW.getProperty('Hourly.3.Temperature')
        self.assertEqual(temperature, '6' + constants.TEMPERATUREUNITS)
        feelsliketemp = properties.WINDOW.getProperty('Hourly.3.FeelsLikeTemp')
        self.assertEqual(feelsliketemp, '5')
        windspeed = properties.WINDOW.getProperty('Hourly.3.WindSpeed')
        self.assertEqual(windspeed, '2')
        winddirection = properties.WINDOW.getProperty('Hourly.3.WindDirection')
        self.assertEqual(winddirection, 'wsw')
        gustspeed = properties.WINDOW.getProperty('Hourly.3.GustSpeed')
        self.assertEqual(gustspeed, '7')
        uvindex = properties.WINDOW.getProperty('Hourly.3.UVIndex')
        self.assertEqual(uvindex, '0')
        precipitation = properties.WINDOW.getProperty('Hourly.3.Precipitation')
        self.assertEqual(precipitation, '5%')
        outlook = properties.WINDOW.getProperty('Hourly.3.Outlook')
        self.assertEqual(outlook, 'Cloudy')
        outlookicon = properties.WINDOW.getProperty('Hourly.3.OutlookIcon')
        self.assertEqual(outlookicon, '26.png')

        time = properties.WINDOW.getProperty('Hourly.4.Time')
        self.assertEqual(time, '21:00')
        temperature = properties.WINDOW.getProperty('Hourly.4.Temperature')
        self.assertEqual(temperature, '5' + constants.TEMPERATUREUNITS)
        feelsliketemp = properties.WINDOW.getProperty('Hourly.4.FeelsLikeTemp')
        self.assertEqual(feelsliketemp, '3')
        windspeed = properties.WINDOW.getProperty('Hourly.4.WindSpeed')
        self.assertEqual(windspeed, '4')
        winddirection = properties.WINDOW.getProperty('Hourly.4.WindDirection')
        self.assertEqual(winddirection, 'ssw')
        gustspeed = properties.WINDOW.getProperty('Hourly.4.GustSpeed')
        self.assertEqual(gustspeed, '9')
        uvindex = properties.WINDOW.getProperty('Hourly.4.UVIndex')
        self.assertEqual(uvindex, '0')
        precipitation = properties.WINDOW.getProperty('Hourly.4.Precipitation')
        self.assertEqual(precipitation, '0%')
        outlook = properties.WINDOW.getProperty('Hourly.4.Outlook')
        self.assertEqual(outlook, 'Clear')
        outlookicon = properties.WINDOW.getProperty('Hourly.4.OutlookIcon')
        self.assertEqual(outlookicon, '31.png')

        time = properties.WINDOW.getProperty('Hourly.5.Time')
        self.assertEqual(time, '00:00')
        temperature = properties.WINDOW.getProperty('Hourly.5.Temperature')
        self.assertEqual(temperature, '3' + constants.TEMPERATUREUNITS)
        feelsliketemp = properties.WINDOW.getProperty('Hourly.5.FeelsLikeTemp')
        self.assertEqual(feelsliketemp, '1')
        windspeed = properties.WINDOW.getProperty('Hourly.5.WindSpeed')
        self.assertEqual(windspeed, '7')
        winddirection = properties.WINDOW.getProperty('Hourly.5.WindDirection')
        self.assertEqual(winddirection, 'ssw')
        gustspeed = properties.WINDOW.getProperty('Hourly.5.GustSpeed')
        self.assertEqual(gustspeed, '16')
        uvindex = properties.WINDOW.getProperty('Hourly.5.UVIndex')
        self.assertEqual(uvindex, '0')
        precipitation = properties.WINDOW.getProperty('Hourly.5.Precipitation')
        self.assertEqual(precipitation, '3%')
        outlook = properties.WINDOW.getProperty('Hourly.5.Outlook')
        self.assertEqual(outlook, 'Clear')
        outlookicon = properties.WINDOW.getProperty('Hourly.5.OutlookIcon')
        self.assertEqual(outlookicon, '31.png')

        time = properties.WINDOW.getProperty('Hourly.6.Time')
        self.assertEqual(time, '03:00')
        temperature = properties.WINDOW.getProperty('Hourly.6.Temperature')
        self.assertEqual(temperature, '3' + constants.TEMPERATUREUNITS)
        feelsliketemp = properties.WINDOW.getProperty('Hourly.6.FeelsLikeTemp')
        self.assertEqual(feelsliketemp, '0')
        windspeed = properties.WINDOW.getProperty('Hourly.6.WindSpeed')
        self.assertEqual(windspeed, '9')
        winddirection = properties.WINDOW.getProperty('Hourly.6.WindDirection')
        self.assertEqual(winddirection, 'ssw')
        gustspeed = properties.WINDOW.getProperty('Hourly.6.GustSpeed')
        self.assertEqual(gustspeed, '20')
        uvindex = properties.WINDOW.getProperty('Hourly.6.UVIndex')
        self.assertEqual(uvindex, '0')
        precipitation = properties.WINDOW.getProperty('Hourly.6.Precipitation')
        self.assertEqual(precipitation, '5%')
        outlook = properties.WINDOW.getProperty('Hourly.6.Outlook')
        self.assertEqual(outlook, 'Clear')
        outlookicon = properties.WINDOW.getProperty('Hourly.6.OutlookIcon')
        self.assertEqual(outlookicon, '31.png')

        time = properties.WINDOW.getProperty('Hourly.7.Time')
        self.assertEqual(time, '06:00')
        temperature = properties.WINDOW.getProperty('Hourly.7.Temperature')
        self.assertEqual(temperature, '4' + constants.TEMPERATUREUNITS)
        feelsliketemp = properties.WINDOW.getProperty('Hourly.7.FeelsLikeTemp')
        self.assertEqual(feelsliketemp, '0')
        windspeed = properties.WINDOW.getProperty('Hourly.7.WindSpeed')
        self.assertEqual(windspeed, '11')
        winddirection = properties.WINDOW.getProperty('Hourly.7.WindDirection')
        self.assertEqual(winddirection, 'ssw')
        gustspeed = properties.WINDOW.getProperty('Hourly.7.GustSpeed')
        self.assertEqual(gustspeed, '25')
        uvindex = properties.WINDOW.getProperty('Hourly.7.UVIndex')
        self.assertEqual(uvindex, '0')
        precipitation = properties.WINDOW.getProperty('Hourly.7.Precipitation')
        self.assertEqual(precipitation, '8%')
        outlook = properties.WINDOW.getProperty('Hourly.7.Outlook')
        self.assertEqual(outlook, 'Cloudy')
        outlookicon = properties.WINDOW.getProperty('Hourly.7.OutlookIcon')
        self.assertEqual(outlookicon, '26.png')

        time = properties.WINDOW.getProperty('Hourly.8.Time')
        self.assertEqual(time, '09:00')
        temperature = properties.WINDOW.getProperty('Hourly.8.Temperature')
        self.assertEqual(temperature, '6' + constants.TEMPERATUREUNITS)
        feelsliketemp = properties.WINDOW.getProperty('Hourly.8.FeelsLikeTemp')
        self.assertEqual(feelsliketemp, '3')
        windspeed = properties.WINDOW.getProperty('Hourly.8.WindSpeed')
        self.assertEqual(windspeed, '13')
        winddirection = properties.WINDOW.getProperty('Hourly.8.WindDirection')
        self.assertEqual(winddirection, 'ssw')
        gustspeed = properties.WINDOW.getProperty('Hourly.8.GustSpeed')
        self.assertEqual(gustspeed, '25')
        uvindex = properties.WINDOW.getProperty('Hourly.8.UVIndex')
        self.assertEqual(uvindex, '1')
        precipitation = properties.WINDOW.getProperty('Hourly.8.Precipitation')
        self.assertEqual(precipitation, '5%')
        outlook = properties.WINDOW.getProperty('Hourly.8.Outlook')
        self.assertEqual(outlook, 'Cloudy')
        outlookicon = properties.WINDOW.getProperty('Hourly.8.OutlookIcon')
        self.assertEqual(outlookicon, '26.png')

        time = properties.WINDOW.getProperty('Hourly.9.Time')
        self.assertEqual(time, '12:00')
        temperature = properties.WINDOW.getProperty('Hourly.9.Temperature')
        self.assertEqual(temperature, '9' + constants.TEMPERATUREUNITS)
        feelsliketemp = properties.WINDOW.getProperty('Hourly.9.FeelsLikeTemp')
        self.assertEqual(feelsliketemp, '5')
        windspeed = properties.WINDOW.getProperty('Hourly.9.WindSpeed')
        self.assertEqual(windspeed, '18')
        winddirection = properties.WINDOW.getProperty('Hourly.9.WindDirection')
        self.assertEqual(winddirection, 's')
        gustspeed = properties.WINDOW.getProperty('Hourly.9.GustSpeed')
        self.assertEqual(gustspeed, '31')
        uvindex = properties.WINDOW.getProperty('Hourly.9.UVIndex')
        self.assertEqual(uvindex, '1')
        precipitation = properties.WINDOW.getProperty('Hourly.9.Precipitation')
        self.assertEqual(precipitation, '5%')
        outlook = properties.WINDOW.getProperty('Hourly.9.Outlook')
        self.assertEqual(outlook, 'Cloudy')
        outlookicon = properties.WINDOW.getProperty('Hourly.9.OutlookIcon')
        self.assertEqual(outlookicon, '26.png')

        time = properties.WINDOW.getProperty('Hourly.10.Time')
        self.assertEqual(time, '15:00')
        temperature = properties.WINDOW.getProperty('Hourly.10.Temperature')
        self.assertEqual(temperature, '9' + constants.TEMPERATUREUNITS)
        feelsliketemp = properties.WINDOW.getProperty('Hourly.10.FeelsLikeTemp')
        self.assertEqual(feelsliketemp, '5')
        windspeed = properties.WINDOW.getProperty('Hourly.10.WindSpeed')
        self.assertEqual(windspeed, '20')
        winddirection = properties.WINDOW.getProperty('Hourly.10.WindDirection')
        self.assertEqual(winddirection, 's')
        gustspeed = properties.WINDOW.getProperty('Hourly.10.GustSpeed')
        self.assertEqual(gustspeed, '36')
        uvindex = properties.WINDOW.getProperty('Hourly.10.UVIndex')
        self.assertEqual(uvindex, '1')
        precipitation = properties.WINDOW.getProperty('Hourly.10.Precipitation')
        self.assertEqual(precipitation, '31%')
        outlook = properties.WINDOW.getProperty('Hourly.10.Outlook')
        self.assertEqual(outlook, 'Cloudy')
        outlookicon = properties.WINDOW.getProperty('Hourly.10.OutlookIcon')
        self.assertEqual(outlookicon, '26.png')

        time = properties.WINDOW.getProperty('Hourly.11.Time')
        self.assertEqual(time, '18:00')
        temperature = properties.WINDOW.getProperty('Hourly.11.Temperature')
        self.assertEqual(temperature, '8' + constants.TEMPERATUREUNITS)
        feelsliketemp = properties.WINDOW.getProperty('Hourly.11.FeelsLikeTemp')
        self.assertEqual(feelsliketemp, '3')
        windspeed = properties.WINDOW.getProperty('Hourly.11.WindSpeed')
        self.assertEqual(windspeed, '20')
        winddirection = properties.WINDOW.getProperty('Hourly.11.WindDirection')
        self.assertEqual(winddirection, 's')
        gustspeed = properties.WINDOW.getProperty('Hourly.11.GustSpeed')
        self.assertEqual(gustspeed, '38')
        uvindex = properties.WINDOW.getProperty('Hourly.11.UVIndex')
        self.assertEqual(uvindex, '0')
        precipitation = properties.WINDOW.getProperty('Hourly.11.Precipitation')
        self.assertEqual(precipitation, '95%')
        outlook = properties.WINDOW.getProperty('Hourly.11.Outlook')
        self.assertEqual(outlook, 'Heavy Rain')
        outlookicon = properties.WINDOW.getProperty('Hourly.11.OutlookIcon')
        self.assertEqual(outlookicon, '40.png')

        time = properties.WINDOW.getProperty('Hourly.12.Time')
        self.assertEqual(time, '21:00')
        temperature = properties.WINDOW.getProperty('Hourly.12.Temperature')
        self.assertEqual(temperature, '7' + constants.TEMPERATUREUNITS)
        feelsliketemp = properties.WINDOW.getProperty('Hourly.12.FeelsLikeTemp')
        self.assertEqual(feelsliketemp, '3')
        windspeed = properties.WINDOW.getProperty('Hourly.12.WindSpeed')
        self.assertEqual(windspeed, '16')
        winddirection = properties.WINDOW.getProperty('Hourly.12.WindDirection')
        self.assertEqual(winddirection, 's')
        gustspeed = properties.WINDOW.getProperty('Hourly.12.GustSpeed')
        self.assertEqual(gustspeed, '29')
        uvindex = properties.WINDOW.getProperty('Hourly.12.UVIndex')
        self.assertEqual(uvindex, '0')
        precipitation = properties.WINDOW.getProperty('Hourly.12.Precipitation')
        self.assertEqual(precipitation, '96%')
        outlook = properties.WINDOW.getProperty('Hourly.12.Outlook')
        self.assertEqual(outlook, 'Heavy Rain')
        outlookicon = properties.WINDOW.getProperty('Hourly.12.OutlookIcon')
        self.assertEqual(outlookicon, '40.png')

        time = properties.WINDOW.getProperty('Hourly.13.Time')
        self.assertEqual(time, '00:00')
        temperature = properties.WINDOW.getProperty('Hourly.13.Temperature')
        self.assertEqual(temperature, '5' + constants.TEMPERATUREUNITS)
        feelsliketemp = properties.WINDOW.getProperty('Hourly.13.FeelsLikeTemp')
        self.assertEqual(feelsliketemp, '1')
        windspeed = properties.WINDOW.getProperty('Hourly.13.WindSpeed')
        self.assertEqual(windspeed, '13')
        winddirection = properties.WINDOW.getProperty('Hourly.13.WindDirection')
        self.assertEqual(winddirection, 'wsw')
        gustspeed = properties.WINDOW.getProperty('Hourly.13.GustSpeed')
        self.assertEqual(gustspeed, '22')
        uvindex = properties.WINDOW.getProperty('Hourly.13.UVIndex')
        self.assertEqual(uvindex, '0')
        precipitation = properties.WINDOW.getProperty('Hourly.13.Precipitation')
        self.assertEqual(precipitation, '54%')
        outlook = properties.WINDOW.getProperty('Hourly.13.Outlook')
        self.assertEqual(outlook, 'Light Rain')
        outlookicon = properties.WINDOW.getProperty('Hourly.13.OutlookIcon')
        self.assertEqual(outlookicon, '11.png')

        time = properties.WINDOW.getProperty('Hourly.14.Time')
        self.assertEqual(time, '03:00')
        temperature = properties.WINDOW.getProperty('Hourly.14.Temperature')
        self.assertEqual(temperature, '3' + constants.TEMPERATUREUNITS)
        feelsliketemp = properties.WINDOW.getProperty('Hourly.14.FeelsLikeTemp')
        self.assertEqual(feelsliketemp, '-1')
        windspeed = properties.WINDOW.getProperty('Hourly.14.WindSpeed')
        self.assertEqual(windspeed, '11')
        winddirection = properties.WINDOW.getProperty('Hourly.14.WindDirection')
        self.assertEqual(winddirection, 'ssw')
        gustspeed = properties.WINDOW.getProperty('Hourly.14.GustSpeed')
        self.assertEqual(gustspeed, '18')
        uvindex = properties.WINDOW.getProperty('Hourly.14.UVIndex')
        self.assertEqual(uvindex, '0')
        precipitation = properties.WINDOW.getProperty('Hourly.14.Precipitation')
        self.assertEqual(precipitation, '13%')
        outlook = properties.WINDOW.getProperty('Hourly.14.Outlook')
        self.assertEqual(outlook, 'Clear')
        outlookicon = properties.WINDOW.getProperty('Hourly.14.OutlookIcon')
        self.assertEqual(outlookicon, '31.png')

        time = properties.WINDOW.getProperty('Hourly.15.Time')
        self.assertEqual(time, '06:00')
        temperature = properties.WINDOW.getProperty('Hourly.15.Temperature')
        self.assertEqual(temperature, '2' + constants.TEMPERATUREUNITS)
        feelsliketemp = properties.WINDOW.getProperty('Hourly.15.FeelsLikeTemp')
        self.assertEqual(feelsliketemp, '-2')
        windspeed = properties.WINDOW.getProperty('Hourly.15.WindSpeed')
        self.assertEqual(windspeed, '11')
        winddirection = properties.WINDOW.getProperty('Hourly.15.WindDirection')
        self.assertEqual(winddirection, 's')
        gustspeed = properties.WINDOW.getProperty('Hourly.15.GustSpeed')
        self.assertEqual(gustspeed, '20')
        uvindex = properties.WINDOW.getProperty('Hourly.15.UVIndex')
        self.assertEqual(uvindex, '0')
        precipitation = properties.WINDOW.getProperty('Hourly.15.Precipitation')
        self.assertEqual(precipitation, '5%')
        outlook = properties.WINDOW.getProperty('Hourly.15.Outlook')
        self.assertEqual(outlook, 'Cloudy')
        outlookicon = properties.WINDOW.getProperty('Hourly.15.OutlookIcon')
        self.assertEqual(outlookicon, '26.png')

        time = properties.WINDOW.getProperty('Hourly.16.Time')
        self.assertEqual(time, '09:00')
        temperature = properties.WINDOW.getProperty('Hourly.16.Temperature')
        self.assertEqual(temperature, '5' + constants.TEMPERATUREUNITS)
        feelsliketemp = properties.WINDOW.getProperty('Hourly.16.FeelsLikeTemp')
        self.assertEqual(feelsliketemp, '1')
        windspeed = properties.WINDOW.getProperty('Hourly.16.WindSpeed')
        self.assertEqual(windspeed, '11')
        winddirection = properties.WINDOW.getProperty('Hourly.16.WindDirection')
        self.assertEqual(winddirection, 's')
        gustspeed = properties.WINDOW.getProperty('Hourly.16.GustSpeed')
        self.assertEqual(gustspeed, '22')
        uvindex = properties.WINDOW.getProperty('Hourly.16.UVIndex')
        self.assertEqual(uvindex, '1')
        precipitation = properties.WINDOW.getProperty('Hourly.16.Precipitation')
        self.assertEqual(precipitation, '33%')
        outlook = properties.WINDOW.getProperty('Hourly.16.Outlook')
        self.assertEqual(outlook, 'Light Rain')
        outlookicon = properties.WINDOW.getProperty('Hourly.16.OutlookIcon')
        self.assertEqual(outlookicon, '11.png')

        time = properties.WINDOW.getProperty('Hourly.17.Time')
        self.assertEqual(time, '12:00')
        temperature = properties.WINDOW.getProperty('Hourly.17.Temperature')
        self.assertEqual(temperature, '7' + constants.TEMPERATUREUNITS)
        feelsliketemp = properties.WINDOW.getProperty('Hourly.17.FeelsLikeTemp')
        self.assertEqual(feelsliketemp, '4')
        windspeed = properties.WINDOW.getProperty('Hourly.17.WindSpeed')
        self.assertEqual(windspeed, '11')
        winddirection = properties.WINDOW.getProperty('Hourly.17.WindDirection')
        self.assertEqual(winddirection, 's')
        gustspeed = properties.WINDOW.getProperty('Hourly.17.GustSpeed')
        self.assertEqual(gustspeed, '22')
        uvindex = properties.WINDOW.getProperty('Hourly.17.UVIndex')
        self.assertEqual(uvindex, '1')
        precipitation = properties.WINDOW.getProperty('Hourly.17.Precipitation')
        self.assertEqual(precipitation, '65%')
        outlook = properties.WINDOW.getProperty('Hourly.17.Outlook')
        self.assertEqual(outlook, 'Heavy Rain')
        outlookicon = properties.WINDOW.getProperty('Hourly.17.OutlookIcon')
        self.assertEqual(outlookicon, '40.png')

        time = properties.WINDOW.getProperty('Hourly.18.Time')
        self.assertEqual(time, '15:00')
        temperature = properties.WINDOW.getProperty('Hourly.18.Temperature')
        self.assertEqual(temperature, '7' + constants.TEMPERATUREUNITS)
        feelsliketemp = properties.WINDOW.getProperty('Hourly.18.FeelsLikeTemp')
        self.assertEqual(feelsliketemp, '4')
        windspeed = properties.WINDOW.getProperty('Hourly.18.WindSpeed')
        self.assertEqual(windspeed, '7')
        winddirection = properties.WINDOW.getProperty('Hourly.18.WindDirection')
        self.assertEqual(winddirection, 'ssw')
        gustspeed = properties.WINDOW.getProperty('Hourly.18.GustSpeed')
        self.assertEqual(gustspeed, '16')
        uvindex = properties.WINDOW.getProperty('Hourly.18.UVIndex')
        self.assertEqual(uvindex, '1')
        precipitation = properties.WINDOW.getProperty('Hourly.18.Precipitation')
        self.assertEqual(precipitation, '48%')
        outlook = properties.WINDOW.getProperty('Hourly.18.Outlook')
        self.assertEqual(outlook, 'Light Rain')
        outlookicon = properties.WINDOW.getProperty('Hourly.18.OutlookIcon')
        self.assertEqual(outlookicon, '11.png')

        time = properties.WINDOW.getProperty('Hourly.19.Time')
        self.assertEqual(time, '18:00')
        temperature = properties.WINDOW.getProperty('Hourly.19.Temperature')
        self.assertEqual(temperature, '5' + constants.TEMPERATUREUNITS)
        feelsliketemp = properties.WINDOW.getProperty('Hourly.19.FeelsLikeTemp')
        self.assertEqual(feelsliketemp, '3')
        windspeed = properties.WINDOW.getProperty('Hourly.19.WindSpeed')
        self.assertEqual(windspeed, '7')
        winddirection = properties.WINDOW.getProperty('Hourly.19.WindDirection')
        self.assertEqual(winddirection, 'wsw')
        gustspeed = properties.WINDOW.getProperty('Hourly.19.GustSpeed')
        self.assertEqual(gustspeed, '11')
        uvindex = properties.WINDOW.getProperty('Hourly.19.UVIndex')
        self.assertEqual(uvindex, '0')
        precipitation = properties.WINDOW.getProperty('Hourly.19.Precipitation')
        self.assertEqual(precipitation, '46%')
        outlook = properties.WINDOW.getProperty('Hourly.19.Outlook')
        self.assertEqual(outlook, 'Light Rain')
        outlookicon = properties.WINDOW.getProperty('Hourly.19.OutlookIcon')
        self.assertEqual(outlookicon, '45.png')

        time = properties.WINDOW.getProperty('Hourly.20.Time')
        self.assertEqual(time, '21:00')
        temperature = properties.WINDOW.getProperty('Hourly.20.Temperature')
        self.assertEqual(temperature, '4' + constants.TEMPERATUREUNITS)
        feelsliketemp = properties.WINDOW.getProperty('Hourly.20.FeelsLikeTemp')
        self.assertEqual(feelsliketemp, '1')
        windspeed = properties.WINDOW.getProperty('Hourly.20.WindSpeed')
        self.assertEqual(windspeed, '9')
        winddirection = properties.WINDOW.getProperty('Hourly.20.WindDirection')
        self.assertEqual(winddirection, 'w')
        gustspeed = properties.WINDOW.getProperty('Hourly.20.GustSpeed')
        self.assertEqual(gustspeed, '13')
        uvindex = properties.WINDOW.getProperty('Hourly.20.UVIndex')
        self.assertEqual(uvindex, '0')
        precipitation = properties.WINDOW.getProperty('Hourly.20.Precipitation')
        self.assertEqual(precipitation, '13%')
        outlook = properties.WINDOW.getProperty('Hourly.20.Outlook')
        self.assertEqual(outlook, 'Cloudy')
        outlookicon = properties.WINDOW.getProperty('Hourly.20.OutlookIcon')
        self.assertEqual(outlookicon, '26.png')

        time = properties.WINDOW.getProperty('Hourly.21.Time')
        self.assertEqual(time, '00:00')
        temperature = properties.WINDOW.getProperty('Hourly.21.Temperature')
        self.assertEqual(temperature, '3' + constants.TEMPERATUREUNITS)
        feelsliketemp = properties.WINDOW.getProperty('Hourly.21.FeelsLikeTemp')
        self.assertEqual(feelsliketemp, '0')
        windspeed = properties.WINDOW.getProperty('Hourly.21.WindSpeed')
        self.assertEqual(windspeed, '9')
        winddirection = properties.WINDOW.getProperty('Hourly.21.WindDirection')
        self.assertEqual(winddirection, 'wnw')
        gustspeed = properties.WINDOW.getProperty('Hourly.21.GustSpeed')
        self.assertEqual(gustspeed, '18')
        uvindex = properties.WINDOW.getProperty('Hourly.21.UVIndex')
        self.assertEqual(uvindex, '0')
        precipitation = properties.WINDOW.getProperty('Hourly.21.Precipitation')
        self.assertEqual(precipitation, '2%')
        outlook = properties.WINDOW.getProperty('Hourly.21.Outlook')
        self.assertEqual(outlook, 'Partly Cloudy')
        outlookicon = properties.WINDOW.getProperty('Hourly.21.OutlookIcon')
        self.assertEqual(outlookicon, '29.png')

        time = properties.WINDOW.getProperty('Hourly.22.Time')
        self.assertEqual(time, '03:00')
        temperature = properties.WINDOW.getProperty('Hourly.22.Temperature')
        self.assertEqual(temperature, '3' + constants.TEMPERATUREUNITS)
        feelsliketemp = properties.WINDOW.getProperty('Hourly.22.FeelsLikeTemp')
        self.assertEqual(feelsliketemp, '-1')
        windspeed = properties.WINDOW.getProperty('Hourly.22.WindSpeed')
        self.assertEqual(windspeed, '9')
        winddirection = properties.WINDOW.getProperty('Hourly.22.WindDirection')
        self.assertEqual(winddirection, 'wnw')
        gustspeed = properties.WINDOW.getProperty('Hourly.22.GustSpeed')
        self.assertEqual(gustspeed, '18')
        uvindex = properties.WINDOW.getProperty('Hourly.22.UVIndex')
        self.assertEqual(uvindex, '0')
        precipitation = properties.WINDOW.getProperty('Hourly.22.Precipitation')
        self.assertEqual(precipitation, '2%')
        outlook = properties.WINDOW.getProperty('Hourly.22.Outlook')
        self.assertEqual(outlook, 'Partly Cloudy')
        outlookicon = properties.WINDOW.getProperty('Hourly.22.OutlookIcon')
        self.assertEqual(outlookicon, '29.png')

        time = properties.WINDOW.getProperty('Hourly.23.Time')
        self.assertEqual(time, '06:00')
        temperature = properties.WINDOW.getProperty('Hourly.23.Temperature')
        self.assertEqual(temperature, '2' + constants.TEMPERATUREUNITS)
        feelsliketemp = properties.WINDOW.getProperty('Hourly.23.FeelsLikeTemp')
        self.assertEqual(feelsliketemp, '-1')
        windspeed = properties.WINDOW.getProperty('Hourly.23.WindSpeed')
        self.assertEqual(windspeed, '9')
        winddirection = properties.WINDOW.getProperty('Hourly.23.WindDirection')
        self.assertEqual(winddirection, 'w')
        gustspeed = properties.WINDOW.getProperty('Hourly.23.GustSpeed')
        self.assertEqual(gustspeed, '16')
        uvindex = properties.WINDOW.getProperty('Hourly.23.UVIndex')
        self.assertEqual(uvindex, '0')
        precipitation = properties.WINDOW.getProperty('Hourly.23.Precipitation')
        self.assertEqual(precipitation, '2%')
        outlook = properties.WINDOW.getProperty('Hourly.23.Outlook')
        self.assertEqual(outlook, 'Partly Cloudy')
        outlookicon = properties.WINDOW.getProperty('Hourly.23.OutlookIcon')
        self.assertEqual(outlookicon, '29.png')

        time = properties.WINDOW.getProperty('Hourly.24.Time')
        self.assertEqual(time, '09:00')
        temperature = properties.WINDOW.getProperty('Hourly.24.Temperature')
        self.assertEqual(temperature, '5' + constants.TEMPERATUREUNITS)
        feelsliketemp = properties.WINDOW.getProperty('Hourly.24.FeelsLikeTemp')
        self.assertEqual(feelsliketemp, '2')
        windspeed = properties.WINDOW.getProperty('Hourly.24.WindSpeed')
        self.assertEqual(windspeed, '11')
        winddirection = properties.WINDOW.getProperty('Hourly.24.WindDirection')
        self.assertEqual(winddirection, 'w')
        gustspeed = properties.WINDOW.getProperty('Hourly.24.GustSpeed')
        self.assertEqual(gustspeed, '20')
        uvindex = properties.WINDOW.getProperty('Hourly.24.UVIndex')
        self.assertEqual(uvindex, '1')
        precipitation = properties.WINDOW.getProperty('Hourly.24.Precipitation')
        self.assertEqual(precipitation, '6%')
        outlook = properties.WINDOW.getProperty('Hourly.24.Outlook')
        self.assertEqual(outlook, 'Partly Cloudy')
        outlookicon = properties.WINDOW.getProperty('Hourly.24.OutlookIcon')
        self.assertEqual(outlookicon, '30.png')

        time = properties.WINDOW.getProperty('Hourly.25.Time')
        self.assertEqual(time, '12:00')
        temperature = properties.WINDOW.getProperty('Hourly.25.Temperature')
        self.assertEqual(temperature, '8' + constants.TEMPERATUREUNITS)
        feelsliketemp = properties.WINDOW.getProperty('Hourly.25.FeelsLikeTemp')
        self.assertEqual(feelsliketemp, '5')
        windspeed = properties.WINDOW.getProperty('Hourly.25.WindSpeed')
        self.assertEqual(windspeed, '11')
        winddirection = properties.WINDOW.getProperty('Hourly.25.WindDirection')
        self.assertEqual(winddirection, 'w')
        gustspeed = properties.WINDOW.getProperty('Hourly.25.GustSpeed')
        self.assertEqual(gustspeed, '22')
        uvindex = properties.WINDOW.getProperty('Hourly.25.UVIndex')
        self.assertEqual(uvindex, '1')
        precipitation = properties.WINDOW.getProperty('Hourly.25.Precipitation')
        self.assertEqual(precipitation, '7%')
        outlook = properties.WINDOW.getProperty('Hourly.25.Outlook')
        self.assertEqual(outlook, 'Partly Cloudy')
        outlookicon = properties.WINDOW.getProperty('Hourly.25.OutlookIcon')
        self.assertEqual(outlookicon, '30.png')

        time = properties.WINDOW.getProperty('Hourly.26.Time')
        self.assertEqual(time, '15:00')
        temperature = properties.WINDOW.getProperty('Hourly.26.Temperature')
        self.assertEqual(temperature, '8' + constants.TEMPERATUREUNITS)
        feelsliketemp = properties.WINDOW.getProperty('Hourly.26.FeelsLikeTemp')
        self.assertEqual(feelsliketemp, '6')
        windspeed = properties.WINDOW.getProperty('Hourly.26.WindSpeed')
        self.assertEqual(windspeed, '11')
        winddirection = properties.WINDOW.getProperty('Hourly.26.WindDirection')
        self.assertEqual(winddirection, 'w')
        gustspeed = properties.WINDOW.getProperty('Hourly.26.GustSpeed')
        self.assertEqual(gustspeed, '18')
        uvindex = properties.WINDOW.getProperty('Hourly.26.UVIndex')
        self.assertEqual(uvindex, '1')
        precipitation = properties.WINDOW.getProperty('Hourly.26.Precipitation')
        self.assertEqual(precipitation, '10%')
        outlook = properties.WINDOW.getProperty('Hourly.26.Outlook')
        self.assertEqual(outlook, 'Sunny')
        outlookicon = properties.WINDOW.getProperty('Hourly.26.OutlookIcon')
        self.assertEqual(outlookicon, '32.png')

        time = properties.WINDOW.getProperty('Hourly.27.Time')
        self.assertEqual(time, '18:00')
        temperature = properties.WINDOW.getProperty('Hourly.27.Temperature')
        self.assertEqual(temperature, '6' + constants.TEMPERATUREUNITS)
        feelsliketemp = properties.WINDOW.getProperty('Hourly.27.FeelsLikeTemp')
        self.assertEqual(feelsliketemp, '4')
        windspeed = properties.WINDOW.getProperty('Hourly.27.WindSpeed')
        self.assertEqual(windspeed, '7')
        winddirection = properties.WINDOW.getProperty('Hourly.27.WindDirection')
        self.assertEqual(winddirection, 'wsw')
        gustspeed = properties.WINDOW.getProperty('Hourly.27.GustSpeed')
        self.assertEqual(gustspeed, '11')
        uvindex = properties.WINDOW.getProperty('Hourly.27.UVIndex')
        self.assertEqual(uvindex, '0')
        precipitation = properties.WINDOW.getProperty('Hourly.27.Precipitation')
        self.assertEqual(precipitation, '8%')
        outlook = properties.WINDOW.getProperty('Hourly.27.Outlook')
        self.assertEqual(outlook, 'Clear')
        outlookicon = properties.WINDOW.getProperty('Hourly.27.OutlookIcon')
        self.assertEqual(outlookicon, '31.png')

        time = properties.WINDOW.getProperty('Hourly.28.Time')
        self.assertEqual(time, '21:00')
        temperature = properties.WINDOW.getProperty('Hourly.28.Temperature')
        self.assertEqual(temperature, '5' + constants.TEMPERATUREUNITS)
        feelsliketemp = properties.WINDOW.getProperty('Hourly.28.FeelsLikeTemp')
        self.assertEqual(feelsliketemp, '2')
        windspeed = properties.WINDOW.getProperty('Hourly.28.WindSpeed')
        self.assertEqual(windspeed, '7')
        winddirection = properties.WINDOW.getProperty('Hourly.28.WindDirection')
        self.assertEqual(winddirection, 'sw')
        gustspeed = properties.WINDOW.getProperty('Hourly.28.GustSpeed')
        self.assertEqual(gustspeed, '13')
        uvindex = properties.WINDOW.getProperty('Hourly.28.UVIndex')
        self.assertEqual(uvindex, '0')
        precipitation = properties.WINDOW.getProperty('Hourly.28.Precipitation')
        self.assertEqual(precipitation, '11%')
        outlook = properties.WINDOW.getProperty('Hourly.28.Outlook')
        self.assertEqual(outlook, 'Partly Cloudy')
        outlookicon = properties.WINDOW.getProperty('Hourly.28.OutlookIcon')
        self.assertEqual(outlookicon, '29.png')

        time = properties.WINDOW.getProperty('Hourly.29.Time')
        self.assertEqual(time, '00:00')
        temperature = properties.WINDOW.getProperty('Hourly.29.Temperature')
        self.assertEqual(temperature, '4' + constants.TEMPERATUREUNITS)
        feelsliketemp = properties.WINDOW.getProperty('Hourly.29.FeelsLikeTemp')
        self.assertEqual(feelsliketemp, '1')
        windspeed = properties.WINDOW.getProperty('Hourly.29.WindSpeed')
        self.assertEqual(windspeed, '9')
        winddirection = properties.WINDOW.getProperty('Hourly.29.WindDirection')
        self.assertEqual(winddirection, 'sw')
        gustspeed = properties.WINDOW.getProperty('Hourly.29.GustSpeed')
        self.assertEqual(gustspeed, '16')
        uvindex = properties.WINDOW.getProperty('Hourly.29.UVIndex')
        self.assertEqual(uvindex, '0')
        precipitation = properties.WINDOW.getProperty('Hourly.29.Precipitation')
        self.assertEqual(precipitation, '16%')
        outlook = properties.WINDOW.getProperty('Hourly.29.Outlook')
        self.assertEqual(outlook, 'Cloudy')
        outlookicon = properties.WINDOW.getProperty('Hourly.29.OutlookIcon')
        self.assertEqual(outlookicon, '26.png')

        time = properties.WINDOW.getProperty('Hourly.30.Time')
        self.assertEqual(time, '03:00')
        temperature = properties.WINDOW.getProperty('Hourly.30.Temperature')
        self.assertEqual(temperature, '4' + constants.TEMPERATUREUNITS)
        feelsliketemp = properties.WINDOW.getProperty('Hourly.30.FeelsLikeTemp')
        self.assertEqual(feelsliketemp, '1')
        windspeed = properties.WINDOW.getProperty('Hourly.30.WindSpeed')
        self.assertEqual(windspeed, '9')
        winddirection = properties.WINDOW.getProperty('Hourly.30.WindDirection')
        self.assertEqual(winddirection, 'sw')
        gustspeed = properties.WINDOW.getProperty('Hourly.30.GustSpeed')
        self.assertEqual(gustspeed, '16')
        uvindex = properties.WINDOW.getProperty('Hourly.30.UVIndex')
        self.assertEqual(uvindex, '0')
        precipitation = properties.WINDOW.getProperty('Hourly.30.Precipitation')
        self.assertEqual(precipitation, '23%')
        outlook = properties.WINDOW.getProperty('Hourly.30.Outlook')
        self.assertEqual(outlook, 'Cloudy')
        outlookicon = properties.WINDOW.getProperty('Hourly.30.OutlookIcon')
        self.assertEqual(outlookicon, '26.png')

        time = properties.WINDOW.getProperty('Hourly.31.Time')
        self.assertEqual(time, '06:00')
        temperature = properties.WINDOW.getProperty('Hourly.31.Temperature')
        self.assertEqual(temperature, '4' + constants.TEMPERATUREUNITS)
        feelsliketemp = properties.WINDOW.getProperty('Hourly.31.FeelsLikeTemp')
        self.assertEqual(feelsliketemp, '1')
        windspeed = properties.WINDOW.getProperty('Hourly.31.WindSpeed')
        self.assertEqual(windspeed, '11')
        winddirection = properties.WINDOW.getProperty('Hourly.31.WindDirection')
        self.assertEqual(winddirection, 'sw')
        gustspeed = properties.WINDOW.getProperty('Hourly.31.GustSpeed')
        self.assertEqual(gustspeed, '20')
        uvindex = properties.WINDOW.getProperty('Hourly.31.UVIndex')
        self.assertEqual(uvindex, '0')
        precipitation = properties.WINDOW.getProperty('Hourly.31.Precipitation')
        self.assertEqual(precipitation, '24%')
        outlook = properties.WINDOW.getProperty('Hourly.31.Outlook')
        self.assertEqual(outlook, 'Overcast')
        outlookicon = properties.WINDOW.getProperty('Hourly.31.OutlookIcon')
        self.assertEqual(outlookicon, '26.png')

        time = properties.WINDOW.getProperty('Hourly.32.Time')
        self.assertEqual(time, '09:00')
        temperature = properties.WINDOW.getProperty('Hourly.32.Temperature')
        self.assertEqual(temperature, '6' + constants.TEMPERATUREUNITS)
        feelsliketemp = properties.WINDOW.getProperty('Hourly.32.FeelsLikeTemp')
        self.assertEqual(feelsliketemp, '2')
        windspeed = properties.WINDOW.getProperty('Hourly.32.WindSpeed')
        self.assertEqual(windspeed, '13')
        winddirection = properties.WINDOW.getProperty('Hourly.32.WindDirection')
        self.assertEqual(winddirection, 'wsw')
        gustspeed = properties.WINDOW.getProperty('Hourly.32.GustSpeed')
        self.assertEqual(gustspeed, '29')
        uvindex = properties.WINDOW.getProperty('Hourly.32.UVIndex')
        self.assertEqual(uvindex, '1')
        precipitation = properties.WINDOW.getProperty('Hourly.32.Precipitation')
        self.assertEqual(precipitation, '55%')
        outlook = properties.WINDOW.getProperty('Hourly.32.Outlook')
        self.assertEqual(outlook, 'Light Rain')
        outlookicon = properties.WINDOW.getProperty('Hourly.32.OutlookIcon')
        self.assertEqual(outlookicon, '11.png')

        time = properties.WINDOW.getProperty('Hourly.33.Time')
        self.assertEqual(time, '12:00')
        temperature = properties.WINDOW.getProperty('Hourly.33.Temperature')
        self.assertEqual(temperature, '8' + constants.TEMPERATUREUNITS)
        feelsliketemp = properties.WINDOW.getProperty('Hourly.33.FeelsLikeTemp')
        self.assertEqual(feelsliketemp, '3')
        windspeed = properties.WINDOW.getProperty('Hourly.33.WindSpeed')
        self.assertEqual(windspeed, '18')
        winddirection = properties.WINDOW.getProperty('Hourly.33.WindDirection')
        self.assertEqual(winddirection, 'w')
        gustspeed = properties.WINDOW.getProperty('Hourly.33.GustSpeed')
        self.assertEqual(gustspeed, '38')
        uvindex = properties.WINDOW.getProperty('Hourly.33.UVIndex')
        self.assertEqual(uvindex, '1')
        precipitation = properties.WINDOW.getProperty('Hourly.33.Precipitation')
        self.assertEqual(precipitation, '37%')
        outlook = properties.WINDOW.getProperty('Hourly.33.Outlook')
        self.assertEqual(outlook, 'Light Rain')
        outlookicon = properties.WINDOW.getProperty('Hourly.33.OutlookIcon')
        self.assertEqual(outlookicon, '11.png')

        time = properties.WINDOW.getProperty('Hourly.34.Time')
        self.assertEqual(time, '15:00')
        temperature = properties.WINDOW.getProperty('Hourly.34.Temperature')
        self.assertEqual(temperature, '8' + constants.TEMPERATUREUNITS)
        feelsliketemp = properties.WINDOW.getProperty('Hourly.34.FeelsLikeTemp')
        self.assertEqual(feelsliketemp, '3')
        windspeed = properties.WINDOW.getProperty('Hourly.34.WindSpeed')
        self.assertEqual(windspeed, '18')
        winddirection = properties.WINDOW.getProperty('Hourly.34.WindDirection')
        self.assertEqual(winddirection, 'w')
        gustspeed = properties.WINDOW.getProperty('Hourly.34.GustSpeed')
        self.assertEqual(gustspeed, '36')
        uvindex = properties.WINDOW.getProperty('Hourly.34.UVIndex')
        self.assertEqual(uvindex, '1')
        precipitation = properties.WINDOW.getProperty('Hourly.34.Precipitation')
        self.assertEqual(precipitation, '14%')
        outlook = properties.WINDOW.getProperty('Hourly.34.Outlook')
        self.assertEqual(outlook, 'Partly Cloudy')
        outlookicon = properties.WINDOW.getProperty('Hourly.34.OutlookIcon')
        self.assertEqual(outlookicon, '30.png')

        time = properties.WINDOW.getProperty('Hourly.35.Time')
        self.assertEqual(time, '18:00')
        temperature = properties.WINDOW.getProperty('Hourly.35.Temperature')
        self.assertEqual(temperature, '7' + constants.TEMPERATUREUNITS)
        feelsliketemp = properties.WINDOW.getProperty('Hourly.35.FeelsLikeTemp')
        self.assertEqual(feelsliketemp, '2')
        windspeed = properties.WINDOW.getProperty('Hourly.35.WindSpeed')
        self.assertEqual(windspeed, '13')
        winddirection = properties.WINDOW.getProperty('Hourly.35.WindDirection')
        self.assertEqual(winddirection, 'w')
        gustspeed = properties.WINDOW.getProperty('Hourly.35.GustSpeed')
        self.assertEqual(gustspeed, '27')
        uvindex = properties.WINDOW.getProperty('Hourly.35.UVIndex')
        self.assertEqual(uvindex, '0')
        precipitation = properties.WINDOW.getProperty('Hourly.35.Precipitation')
        self.assertEqual(precipitation, '6%')
        outlook = properties.WINDOW.getProperty('Hourly.35.Outlook')
        self.assertEqual(outlook, 'Partly Cloudy')
        outlookicon = properties.WINDOW.getProperty('Hourly.35.OutlookIcon')
        self.assertEqual(outlookicon, '29.png')

        time = properties.WINDOW.getProperty('Hourly.36.Time')
        self.assertEqual(time, '21:00')
        temperature = properties.WINDOW.getProperty('Hourly.36.Temperature')
        self.assertEqual(temperature, '5' + constants.TEMPERATUREUNITS)
        feelsliketemp = properties.WINDOW.getProperty('Hourly.36.FeelsLikeTemp')
        self.assertEqual(feelsliketemp, '1')
        windspeed = properties.WINDOW.getProperty('Hourly.36.WindSpeed')
        self.assertEqual(windspeed, '13')
        winddirection = properties.WINDOW.getProperty('Hourly.36.WindDirection')
        self.assertEqual(winddirection, 'wsw')
        gustspeed = properties.WINDOW.getProperty('Hourly.36.GustSpeed')
        self.assertEqual(gustspeed, '25')
        uvindex = properties.WINDOW.getProperty('Hourly.36.UVIndex')
        self.assertEqual(uvindex, '0')
        precipitation = properties.WINDOW.getProperty('Hourly.36.Precipitation')
        self.assertEqual(precipitation, '7%')
        outlook = properties.WINDOW.getProperty('Hourly.36.Outlook')
        self.assertEqual(outlook, 'Partly Cloudy')
        outlookicon = properties.WINDOW.getProperty('Hourly.36.OutlookIcon')
        self.assertEqual(outlookicon, '29.png')

        # Test exception handling when given json without proper keys
        mock_cache.return_value.__enter__.return_value.get = Mock(return_value=EMPTY_FILE)
        with self.assertRaises(KeyError) as cm:
            properties.threehourly()
        self.assertEqual(('Key Error in JSON File',
                          "Key 'SiteRep' not found while processing file from url:",
                          constants.THREEHOURLY_LOCATION_FORECAST_URL), cm.exception.args)

    @patch('metoffice.properties.LATITUDE', '52.245')
    @patch('metoffice.properties.LONGITUDE', '0.103')
    def test_sunrise(self):
        # We should change this (and all other tests) to just
        # verify the call to getProperty, not the behaviour
        # of getProperty, which is what we're doing.
        properties.sunrisesunset()
        sunrise = properties.WINDOW.getProperty('Today.Sunrise')
        # We get something back that looks like a digital time. Eg 06:26.
        self.assertTrue(re.match(r'\d\d:\d\d', sunrise))
        sunset = properties.WINDOW.getProperty('Today.Sunset')
        self.assertTrue(re.match(r'\d\d:\d\d', sunset))

    @patch('metoffice.properties.urlcache.URLCache')
    def test_text(self, mock_cache):
        mock_cache.return_value.__enter__.return_value.get = Mock(side_effect=self.mock_get)

        properties.text()
        issued_at = properties.WINDOW.getProperty('TextForecast.IssuedAt')
        self.assertEqual(issued_at, '16:00 Mon 24 Feb 2014')

        title = properties.WINDOW.getProperty('Text.Paragraph0.Title')
        self.assertEqual(title, 'Headline')
        content = properties.WINDOW.getProperty('Text.Paragraph0.Content')
        self.assertEqual(content,
                         'Rain clearing eastwards, showers following, with increasing winds.')
        title = properties.WINDOW.getProperty('Text.Paragraph1.Title')
        self.assertEqual(title, 'This Evening and Tonight')
        content = properties.WINDOW.getProperty('Text.Paragraph1.Content')
        self.assertEqual(content,
                         ('Rain arriving in the far west around dusk will clear eastwards overnight, '
                          'this heaviest in the west and over high ground, where winds will also become '
                          'strong. Mild, with clear spells and scattered showers following. Minimum '
                          'Temperature 5C.'))
        title = properties.WINDOW.getProperty('Text.Paragraph2.Title')
        self.assertEqual(title, 'Tuesday')
        content = properties.WINDOW.getProperty('Text.Paragraph2.Content')
        self.assertEqual(content,
                         ('Some dry and bright weather is likely at times but also scattered blustery, '
                          'heavy showers. Remaining windy, especially around exposed coasts and hills '
                          'where gales are likely. Maximum Temperature 9C.'))
        title = properties.WINDOW.getProperty('Text.Paragraph3.Title')
        self.assertEqual(title, 'Wednesday to Friday')
        content = properties.WINDOW.getProperty('Text.Paragraph3.Content')
        self.assertEqual(content,
                         ('Sunny spells and lighter winds on Wednesday, some showers along the coast. '
                          'Wet and windy overnight, turning showery on Thursday and Friday, becoming '
                          'wintry over hills.'))
        title = properties.WINDOW.getProperty('Text.Paragraph4.Title')
        self.assertEqual(title, 'Saturday 1 Mar 2014 to Monday 10 Mar 2014')
        content = properties.WINDOW.getProperty('Text.Paragraph4.Content')
        self.assertEqual(content,
                         ('The weekend will start unsettled with showers or longer spells of rain, with '
                          'some heavier bursts at first. This will be most persistent in the far southeast '
                          'and far north, with a risk of hill snow in the north. There will be some drier '
                          'slots too, especially on Sunday with a risk of local frost and icy surfaces. '
                          'Temperatures near normal. Through the next week it will remain unsettled in '
                          'northern parts, with further rain or showers, and some hill snow. It will be '
                          'mainly dry but fairly cloudy towards the south with isolated patchy frost. '
                          'During the middle part of the week rain may spread southwards for a time, '
                          'before turning wet and windy in the northwest again later, with a risk of gales.'))
        title = properties.WINDOW.getProperty('Text.Paragraph5.Title')
        self.assertEqual(title, 'Tuesday 11 Mar 2014 to Tuesday 25 Mar 2014')
        content = properties.WINDOW.getProperty('Text.Paragraph5.Content')
        self.assertEqual(content,
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
                          constants.TEXT_FORECAST_URL), cm.exception.args)

    @patch('metoffice.urlcache.URLCache')
    @patch('metoffice.properties.API_KEY', '12345')
    def test_forecastlayer(self, mock_cache):
        mock_cache.return_value.__enter__.return_value.get = Mock(side_effect=self.mock_get)

        properties.forecastlayer()
        surface = properties.WINDOW.getProperty('ForecastMap.Surface')
        self.assertEqual(surface, GOOGLE_SURFACE_IMAGE)
        marker = properties.WINDOW.getProperty('ForecastMap.Marker')
        self.assertEqual(marker, GOOGLE_MARKER_IMAGE)
        slider = properties.WINDOW.getProperty('ForecastMap.Slider')
        self.assertEqual(slider, '0')
        issued_at = properties.WINDOW.getProperty('ForecastMap.IssuedAt')
        self.assertEqual(issued_at, '09:00 Wed 19 Mar 2014')
        map_time = properties.WINDOW.getProperty('ForecastMap.MapTime')
        self.assertEqual(map_time, '0900 Wed')
        layer = properties.WINDOW.getProperty('ForecastMap.Layer')
        self.assertEqual(layer, PRECIPITATION_LAYER_IMAGE)
        is_fetched = properties.WINDOW.getProperty('ForecastMap.IsFetched')
        self.assertEqual(is_fetched, 'true')

        # Test exception handling when given json without proper keys
        mock_cache.return_value.__enter__.return_value.get = Mock(return_value=EMPTY_FILE)
        with self.assertRaises(KeyError) as cm:
            properties.forecastlayer()
        self.assertEqual(('Key Error in JSON File',
                          "Key 'Layers' not found while processing file from url:",
                          constants.FORECAST_LAYER_CAPABILITIES_URL), cm.exception.args)

        # Test exception handling when given corrupt BaseURL in json
        # (We have provide partially valid json so execution can drop to the exception under test.)
        mock_cache.return_value.__enter__.return_value.get = Mock(return_value=CORRUPTFORECASTLAYERCAPABILITIES)
        with self.assertRaises(KeyError) as cm:
            properties.forecastlayer()
        self.assertEqual(('Key Error in JSON File',
                          "Key '$' not found while processing file from url:",
                          constants.FORECAST_LAYER_CAPABILITIES_URL), cm.exception.args)

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

    @patch('metoffice.urlcache.URLCache')
    @patch('metoffice.properties.API_KEY', '12345')
    def test_observationlayer(self, mock_cache):
        mock_cache.return_value.__enter__.return_value.get = Mock(side_effect=self.mock_get)

        properties.observationlayer()
        surface = properties.WINDOW.getProperty('ObservationMap.Surface')
        self.assertEqual(surface, GOOGLE_SURFACE_IMAGE)
        marker = properties.WINDOW.getProperty('ObservationMap.Marker')
        self.assertEqual(marker, GOOGLE_MARKER_IMAGE)
        slider = properties.WINDOW.getProperty('ObservationMap.Slider')
        self.assertEqual(slider, '0')
        issuedat = properties.WINDOW.getProperty('ObservationMap.IssuedAt')
        self.assertEqual(issuedat, '17:30 Tue 01 Apr 2014')
        maptime = properties.WINDOW.getProperty('ObservationMap.MapTime')
        self.assertEqual(maptime, '1730 Tue')
        layer = properties.WINDOW.getProperty('ObservationMap.Layer')
        self.assertEqual(layer, PRECIPITATION_LAYER_IMAGE)
        isfetched = properties.WINDOW.getProperty('ObservationMap.IsFetched')
        self.assertEqual(isfetched, 'true')

        # Test exception handling when given json without proper keys
        mock_cache.return_value.__enter__.return_value.get = Mock(return_value=EMPTY_FILE)
        with self.assertRaises(KeyError) as cm:
            properties.observationlayer()
        self.assertEqual(('Key Error in JSON File',
                          "Key 'Layers' not found while processing file from url:",
                          constants.OBSERVATION_LAYER_CAPABILITIES_URL), cm.exception.args)

        # Test exception handling when given corrupt BaseURL in json
        # (We have provide partially valid json so execution can drop to the exception under test.)
        mock_cache.return_value.__enter__.return_value.get = Mock(return_value=CORRUPTOBSERVATIONLAYERCAPABILITIES)
        with self.assertRaises(KeyError) as cm:
            properties.observationlayer()
        self.assertEqual(('Key Error in JSON File',
                          "Key '$' not found while processing file from url:",
                          constants.OBSERVATION_LAYER_CAPABILITIES_URL), cm.exception.args)

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

    @patch('metoffice.urlcache.URLCache')
    def test_daily_expiry(self, mock_cache):
        mock_cache.return_value.__enter__.return_value.get = Mock(side_effect=self.mock_get)

        result = properties.daily_expiry(FORECASTDAILY)
        self.assertEqual(datetime.datetime(2014, 2, 24, 15, 30), result)

    @patch('metoffice.urlcache.URLCache')
    def test_threehourly_expiry(self, mock_cache):
        mock_cache.return_value.__enter__.return_value.get = Mock(side_effect=self.mock_get)

        result = properties.threehourly_expiry(FORECAST3HOURLY)
        self.assertEqual(datetime.datetime(2014, 3, 1, 17, 30), result)

    @patch('metoffice.urlcache.URLCache')
    def test_text_expiry(self, mock_cache):
        mock_cache.return_value.__enter__.return_value.get = Mock(side_effect=self.mock_get)

        result = properties.text_expiry(FORECASTTEXT)
        self.assertEqual(datetime.datetime(2014, 2, 25, 4, 0), result)

    @patch('metoffice.urlcache.URLCache')
    def test_observation_expiry(self, mock_cache):
        mock_cache.return_value.__enter__.return_value.get = Mock(side_effect=self.mock_get)

        result = properties.observation_expiry(OBSERVATIONHOURLY)
        self.assertEqual(datetime.datetime(2014, 3, 6, 18, 30), result)

    @patch('metoffice.urlcache.URLCache')
    def test_forecastlayer_capabilities_expiry(self, mock_cache):
        mock_cache.return_value.__enter__.return_value.get = Mock(side_effect=self.mock_get)

        result = properties.forecastlayer_capabilities_expiry(FORECASTLAYERCAPABILITIES)
        self.assertEqual(datetime.datetime(2014, 3, 19, 18, 0), result)

    @patch('metoffice.urlcache.URLCache')
    def test_observationlayer_capabilities_expiry(self, mock_cache):
        mock_cache.return_value.__enter__.return_value.get = Mock(side_effect=self.mock_get)

        result = properties.observationlayer_capabilities_expiry(OBSERVATIONLAYERCAPABILITIES)
        self.assertEqual(datetime.datetime(2014, 4, 1, 17, 0), result)

    @patch('metoffice.urlcache.URLCache')
    def test_layer_image_resize_callback(self, mock_cache):
        mock_cache.return_value.__enter__.return_value.get = Mock(side_effect=self.mock_get)

        # Assert that the pretend image in cache has not been resized
        with Image.open(PRECIPITATION_LAYER_IMAGE) as img:
            (width, height) = img.size
        self.assertEqual(500, width)
        self.assertEqual(500, height)

        properties.image_resize(PRECIPITATION_LAYER_IMAGE)
        with Image.open(PRECIPITATION_LAYER_IMAGE) as img:
            (width, height) = img.size
        self.assertEqual(420, width)
        self.assertEqual(460, height)

    def tearDown(self):
        super(TestProperties, self).tearDown()
        shutil.rmtree(RESULTS_FOLDER)
