import os
import json
from xbmctestcase import XBMCTestCase

TEST_FOLDER = os.path.dirname(__file__)
RESULTS_FOLDER = os.path.join(TEST_FOLDER, 'results')
DATA_FOLDER = os.path.join(TEST_FOLDER, 'data')
OBSERVATIONREPORT = os.path.join(DATA_FOLDER, 'observationhourly.json')
OBSERVATIONREPORT2 = os.path.join(DATA_FOLDER, 'observationhourly2.json')
FORECASTDAILY = os.path.join(DATA_FOLDER, 'forecastdaily.json')
FORECAST3HOURLY = os.path.join(DATA_FOLDER, 'forecast3hourly.json')
FORECASTTEXT = os.path.join(DATA_FOLDER, 'forecasttext.json')

class TestJsonParser(XBMCTestCase):
    def setUp(self):
        super(TestJsonParser, self).setUp()
        self.xbmc.translatePath.side_effect = lambda x : x

        from metoffice.utils import jsonparser
        self.jsonparser = jsonparser

    def test_observation(self):
        observation_data = json.load(open(OBSERVATIONREPORT))
        result = self.jsonparser.observation(observation_data)
        self.assertEqual('17:00 Thu 06 Mar 2014', result['HourlyObservation.IssuedAt'])
        self.assertEqual('Cloudy', result['Current.Condition'])
        self.assertEqual('45000', result['Current.Visibility'])
        self.assertEqual('1021', result['Current.Pressure'])
        self.assertEqual('10', result['Current.Temperature'])
        self.assertEqual('14', result['Current.Wind'])
        self.assertEqual('SW', result['Current.WindDirection'])
        self.assertEqual('n/a', result['Current.WindGust'])
        self.assertEqual('26.png', result['Current.OutlookIcon'])
        self.assertEqual('26.png', result['Current.FanartCode'])

        #Test exceptions when reports don't contain list items.
        observation_data = json.load(open(OBSERVATIONREPORT2))
        result = self.jsonparser.observation(observation_data)
        self.assertEqual('17:00 Thu 06 Mar 2014', result['HourlyObservation.IssuedAt'])
        self.assertEqual('Sunny', result['Current.Condition'])
        self.assertEqual('45000', result['Current.Visibility'])
        self.assertEqual('1021', result['Current.Pressure'])
        self.assertEqual('10', result['Current.Temperature'])
        self.assertEqual('10', result['Current.Wind'])
        self.assertEqual('WSW', result['Current.WindDirection'])
        self.assertEqual('n/a', result['Current.WindGust'])
        self.assertEqual('32.png', result['Current.OutlookIcon'])
        self.assertEqual('32.png', result['Current.FanartCode'])
        
    def test_daily(self):
        forecast_data = json.load(open(FORECASTDAILY))
        result = self.jsonparser.daily(forecast_data)
        self.assertEqual('14:00 Mon 24 Feb 2014', result['DailyForecast.IssuedAt'])
        self.assertEqual('Mon', result['Day0.Title'])
        self.assertEqual('13', result['Day0.HighTemp'])
        self.assertEqual('7', result['Day0.LowTemp'])
        self.assertEqual('13', result['Day0.WindSpeed'])
        self.assertEqual('ssw', result['Day0.WindDirection'])
        self.assertEqual('Light Rain', result['Day0.Outlook'])
        self.assertEqual('special://temp/weather/11.png', result['Day0.OutlookIcon'])

        self.assertEqual('Tue', result['Day1.Title'])
        self.assertEqual('12', result['Day1.HighTemp'])
        self.assertEqual('3', result['Day1.LowTemp'])
        self.assertEqual('18', result['Day1.WindSpeed'])
        self.assertEqual('ssw', result['Day1.WindDirection'])
        self.assertEqual('Sunny', result['Day1.Outlook'])
        self.assertEqual('special://temp/weather/32.png', result['Day1.OutlookIcon'])

        self.assertEqual('Wed', result['Day2.Title'])
        self.assertEqual('11', result['Day2.HighTemp'])
        self.assertEqual('4', result['Day2.LowTemp'])
        self.assertEqual('13', result['Day2.WindSpeed'])
        self.assertEqual('wsw', result['Day2.WindDirection'])
        self.assertEqual('Sunny', result['Day2.Outlook'])
        self.assertEqual('special://temp/weather/32.png', result['Day2.OutlookIcon'])

        self.assertEqual('Thu', result['Day3.Title'])
        self.assertEqual('11', result['Day3.HighTemp'])
        self.assertEqual('3', result['Day3.LowTemp'])
        self.assertEqual('16', result['Day3.WindSpeed'])
        self.assertEqual('wsw', result['Day3.WindDirection'])
        self.assertEqual('Heavy Rain', result['Day3.Outlook'])
        self.assertEqual('special://temp/weather/40.png', result['Day3.OutlookIcon'])

        self.assertEqual('Fri', result['Day4.Title'])
        self.assertEqual('9', result['Day4.HighTemp'])
        self.assertEqual('2', result['Day4.LowTemp'])
        self.assertEqual('11', result['Day4.WindSpeed'])
        self.assertEqual('sw', result['Day4.WindDirection'])
        self.assertEqual('Light Rain', result['Day4.Outlook'])
        self.assertEqual('special://temp/weather/11.png', result['Day4.OutlookIcon'])
        
    def test_threehourly(self):
        forecast_data = json.load(open(FORECAST3HOURLY))
        result = self.jsonparser.threehourly(forecast_data)
        self.assertEqual('16:00 Sat 01 Mar 2014', result['3HourlyForecast.IssuedAt'])

        self.assertEqual('Sat', result['3Hourly0.Day'])
        self.assertEqual('12:00', result['3Hourly0.Time'])
        self.assertEqual('2014-03-01Z', result['3Hourly0.Date'])
        self.assertEqual('6', result['3Hourly0.ActualTemp'])
        self.assertEqual('4', result['3Hourly0.FeelsLikeTemp'])
        self.assertEqual('4', result['3Hourly0.WindSpeed'])
        self.assertEqual('nnw', result['3Hourly0.WindDirection'])
        self.assertEqual('7', result['3Hourly0.GustSpeed'])
        self.assertEqual('1', result['3Hourly0.UVIndex'])
        self.assertEqual('6', result['3Hourly0.Precipitation'])
        self.assertEqual('Cloudy', result['3Hourly0.Outlook'])
        self.assertEqual('special://temp/weather/26.png', result['3Hourly0.OutlookIcon'])

        self.assertEqual('Sat', result['3Hourly1.Day'])
        self.assertEqual('15:00', result['3Hourly1.Time'])
        self.assertEqual('2014-03-01Z', result['3Hourly1.Date'])
        self.assertEqual('8', result['3Hourly1.ActualTemp'])
        self.assertEqual('6', result['3Hourly1.FeelsLikeTemp'])
        self.assertEqual('7', result['3Hourly1.WindSpeed'])
        self.assertEqual('wsw', result['3Hourly1.WindDirection'])
        self.assertEqual('11', result['3Hourly1.GustSpeed'])
        self.assertEqual('1', result['3Hourly1.UVIndex'])
        self.assertEqual('6', result['3Hourly1.Precipitation'])
        self.assertEqual('Cloudy', result['3Hourly1.Outlook'])
        self.assertEqual('special://temp/weather/26.png', result['3Hourly1.OutlookIcon'])

        self.assertEqual('Sat', result['3Hourly2.Day'])
        self.assertEqual('18:00', result['3Hourly2.Time'])
        self.assertEqual('2014-03-01Z', result['3Hourly2.Date'])
        self.assertEqual('6', result['3Hourly2.ActualTemp'])
        self.assertEqual('5', result['3Hourly2.FeelsLikeTemp'])
        self.assertEqual('2', result['3Hourly2.WindSpeed'])
        self.assertEqual('wsw', result['3Hourly2.WindDirection'])
        self.assertEqual('7', result['3Hourly2.GustSpeed'])
        self.assertEqual('0', result['3Hourly2.UVIndex'])
        self.assertEqual('5', result['3Hourly2.Precipitation'])
        self.assertEqual('Cloudy', result['3Hourly2.Outlook'])
        self.assertEqual('special://temp/weather/26.png', result['3Hourly2.OutlookIcon'])

        self.assertEqual('Sat', result['3Hourly3.Day'])
        self.assertEqual('21:00', result['3Hourly3.Time'])
        self.assertEqual('2014-03-01Z', result['3Hourly3.Date'])
        self.assertEqual('5', result['3Hourly3.ActualTemp'])
        self.assertEqual('3', result['3Hourly3.FeelsLikeTemp'])
        self.assertEqual('4', result['3Hourly3.WindSpeed'])
        self.assertEqual('ssw', result['3Hourly3.WindDirection'])
        self.assertEqual('9', result['3Hourly3.GustSpeed'])
        self.assertEqual('0', result['3Hourly3.UVIndex'])
        self.assertEqual('0', result['3Hourly3.Precipitation'])
        self.assertEqual('Clear', result['3Hourly3.Outlook'])
        self.assertEqual('special://temp/weather/31.png', result['3Hourly3.OutlookIcon'])

        self.assertEqual('Sun', result['3Hourly4.Day'])
        self.assertEqual('00:00', result['3Hourly4.Time'])
        self.assertEqual('2014-03-02Z', result['3Hourly4.Date'])
        self.assertEqual('3', result['3Hourly4.ActualTemp'])
        self.assertEqual('1', result['3Hourly4.FeelsLikeTemp'])
        self.assertEqual('7', result['3Hourly4.WindSpeed'])
        self.assertEqual('ssw', result['3Hourly4.WindDirection'])
        self.assertEqual('16', result['3Hourly4.GustSpeed'])
        self.assertEqual('0', result['3Hourly4.UVIndex'])
        self.assertEqual('3', result['3Hourly4.Precipitation'])
        self.assertEqual('Clear', result['3Hourly4.Outlook'])
        self.assertEqual('special://temp/weather/31.png', result['3Hourly4.OutlookIcon'])

        self.assertEqual('Sun', result['3Hourly5.Day'])
        self.assertEqual('03:00', result['3Hourly5.Time'])
        self.assertEqual('2014-03-02Z', result['3Hourly5.Date'])
        self.assertEqual('3', result['3Hourly5.ActualTemp'])
        self.assertEqual('0', result['3Hourly5.FeelsLikeTemp'])
        self.assertEqual('9', result['3Hourly5.WindSpeed'])
        self.assertEqual('ssw', result['3Hourly5.WindDirection'])
        self.assertEqual('20', result['3Hourly5.GustSpeed'])
        self.assertEqual('0', result['3Hourly5.UVIndex'])
        self.assertEqual('5', result['3Hourly5.Precipitation'])
        self.assertEqual('Clear', result['3Hourly5.Outlook'])
        self.assertEqual('special://temp/weather/31.png', result['3Hourly5.OutlookIcon'])

        self.assertEqual('Sun', result['3Hourly6.Day'])
        self.assertEqual('06:00', result['3Hourly6.Time'])
        self.assertEqual('2014-03-02Z', result['3Hourly6.Date'])
        self.assertEqual('4', result['3Hourly6.ActualTemp'])
        self.assertEqual('0', result['3Hourly6.FeelsLikeTemp'])
        self.assertEqual('11', result['3Hourly6.WindSpeed'])
        self.assertEqual('ssw', result['3Hourly6.WindDirection'])
        self.assertEqual('25', result['3Hourly6.GustSpeed'])
        self.assertEqual('0', result['3Hourly6.UVIndex'])
        self.assertEqual('8', result['3Hourly6.Precipitation'])
        self.assertEqual('Cloudy', result['3Hourly6.Outlook'])
        self.assertEqual('special://temp/weather/26.png', result['3Hourly6.OutlookIcon'])

        self.assertEqual('Sun', result['3Hourly7.Day'])
        self.assertEqual('09:00', result['3Hourly7.Time'])
        self.assertEqual('2014-03-02Z', result['3Hourly7.Date'])
        self.assertEqual('6', result['3Hourly7.ActualTemp'])
        self.assertEqual('3', result['3Hourly7.FeelsLikeTemp'])
        self.assertEqual('13', result['3Hourly7.WindSpeed'])
        self.assertEqual('ssw', result['3Hourly7.WindDirection'])
        self.assertEqual('25', result['3Hourly7.GustSpeed'])
        self.assertEqual('1', result['3Hourly7.UVIndex'])
        self.assertEqual('5', result['3Hourly7.Precipitation'])
        self.assertEqual('Cloudy', result['3Hourly7.Outlook'])
        self.assertEqual('special://temp/weather/26.png', result['3Hourly7.OutlookIcon'])

        self.assertEqual('Sun', result['3Hourly8.Day'])
        self.assertEqual('12:00', result['3Hourly8.Time'])
        self.assertEqual('2014-03-02Z', result['3Hourly8.Date'])
        self.assertEqual('9', result['3Hourly8.ActualTemp'])
        self.assertEqual('5', result['3Hourly8.FeelsLikeTemp'])
        self.assertEqual('18', result['3Hourly8.WindSpeed'])
        self.assertEqual('s', result['3Hourly8.WindDirection'])
        self.assertEqual('31', result['3Hourly8.GustSpeed'])
        self.assertEqual('1', result['3Hourly8.UVIndex'])
        self.assertEqual('5', result['3Hourly8.Precipitation'])
        self.assertEqual('Cloudy', result['3Hourly8.Outlook'])
        self.assertEqual('special://temp/weather/26.png', result['3Hourly8.OutlookIcon'])

        self.assertEqual('Sun', result['3Hourly9.Day'])
        self.assertEqual('15:00', result['3Hourly9.Time'])
        self.assertEqual('2014-03-02Z', result['3Hourly9.Date'])
        self.assertEqual('9', result['3Hourly9.ActualTemp'])
        self.assertEqual('5', result['3Hourly9.FeelsLikeTemp'])
        self.assertEqual('20', result['3Hourly9.WindSpeed'])
        self.assertEqual('s', result['3Hourly9.WindDirection'])
        self.assertEqual('36', result['3Hourly9.GustSpeed'])
        self.assertEqual('1', result['3Hourly9.UVIndex'])
        self.assertEqual('31', result['3Hourly9.Precipitation'])
        self.assertEqual('Cloudy', result['3Hourly9.Outlook'])
        self.assertEqual('special://temp/weather/26.png', result['3Hourly9.OutlookIcon'])

        self.assertEqual('Sun', result['3Hourly10.Day'])
        self.assertEqual('18:00', result['3Hourly10.Time'])
        self.assertEqual('2014-03-02Z', result['3Hourly10.Date'])
        self.assertEqual('8', result['3Hourly10.ActualTemp'])
        self.assertEqual('3', result['3Hourly10.FeelsLikeTemp'])
        self.assertEqual('20', result['3Hourly10.WindSpeed'])
        self.assertEqual('s', result['3Hourly10.WindDirection'])
        self.assertEqual('38', result['3Hourly10.GustSpeed'])
        self.assertEqual('0', result['3Hourly10.UVIndex'])
        self.assertEqual('95', result['3Hourly10.Precipitation'])
        self.assertEqual('Heavy Rain', result['3Hourly10.Outlook'])
        self.assertEqual('special://temp/weather/40.png', result['3Hourly10.OutlookIcon'])

        self.assertEqual('Sun', result['3Hourly11.Day'])
        self.assertEqual('21:00', result['3Hourly11.Time'])
        self.assertEqual('2014-03-02Z', result['3Hourly11.Date'])
        self.assertEqual('7', result['3Hourly11.ActualTemp'])
        self.assertEqual('3', result['3Hourly11.FeelsLikeTemp'])
        self.assertEqual('16', result['3Hourly11.WindSpeed'])
        self.assertEqual('s', result['3Hourly11.WindDirection'])
        self.assertEqual('29', result['3Hourly11.GustSpeed'])
        self.assertEqual('0', result['3Hourly11.UVIndex'])
        self.assertEqual('96', result['3Hourly11.Precipitation'])
        self.assertEqual('Heavy Rain', result['3Hourly11.Outlook'])
        self.assertEqual('special://temp/weather/40.png', result['3Hourly11.OutlookIcon'])

        self.assertEqual('Mon', result['3Hourly12.Day'])
        self.assertEqual('00:00', result['3Hourly12.Time'])
        self.assertEqual('2014-03-03Z', result['3Hourly12.Date'])
        self.assertEqual('5', result['3Hourly12.ActualTemp'])
        self.assertEqual('1', result['3Hourly12.FeelsLikeTemp'])
        self.assertEqual('13', result['3Hourly12.WindSpeed'])
        self.assertEqual('wsw', result['3Hourly12.WindDirection'])
        self.assertEqual('22', result['3Hourly12.GustSpeed'])
        self.assertEqual('0', result['3Hourly12.UVIndex'])
        self.assertEqual('54', result['3Hourly12.Precipitation'])
        self.assertEqual('Light Rain', result['3Hourly12.Outlook'])
        self.assertEqual('special://temp/weather/11.png', result['3Hourly12.OutlookIcon'])

        self.assertEqual('Mon', result['3Hourly13.Day'])
        self.assertEqual('03:00', result['3Hourly13.Time'])
        self.assertEqual('2014-03-03Z', result['3Hourly13.Date'])
        self.assertEqual('3', result['3Hourly13.ActualTemp'])
        self.assertEqual('-1', result['3Hourly13.FeelsLikeTemp'])
        self.assertEqual('11', result['3Hourly13.WindSpeed'])
        self.assertEqual('ssw', result['3Hourly13.WindDirection'])
        self.assertEqual('18', result['3Hourly13.GustSpeed'])
        self.assertEqual('0', result['3Hourly13.UVIndex'])
        self.assertEqual('13', result['3Hourly13.Precipitation'])
        self.assertEqual('Clear', result['3Hourly13.Outlook'])
        self.assertEqual('special://temp/weather/31.png', result['3Hourly13.OutlookIcon'])

        self.assertEqual('Mon', result['3Hourly14.Day'])
        self.assertEqual('06:00', result['3Hourly14.Time'])
        self.assertEqual('2014-03-03Z', result['3Hourly14.Date'])
        self.assertEqual('2', result['3Hourly14.ActualTemp'])
        self.assertEqual('-2', result['3Hourly14.FeelsLikeTemp'])
        self.assertEqual('11', result['3Hourly14.WindSpeed'])
        self.assertEqual('s', result['3Hourly14.WindDirection'])
        self.assertEqual('20', result['3Hourly14.GustSpeed'])
        self.assertEqual('0', result['3Hourly14.UVIndex'])
        self.assertEqual('5', result['3Hourly14.Precipitation'])
        self.assertEqual('Cloudy', result['3Hourly14.Outlook'])
        self.assertEqual('special://temp/weather/26.png', result['3Hourly14.OutlookIcon'])

        self.assertEqual('Mon', result['3Hourly15.Day'])
        self.assertEqual('09:00', result['3Hourly15.Time'])
        self.assertEqual('2014-03-03Z', result['3Hourly15.Date'])
        self.assertEqual('5', result['3Hourly15.ActualTemp'])
        self.assertEqual('1', result['3Hourly15.FeelsLikeTemp'])
        self.assertEqual('11', result['3Hourly15.WindSpeed'])
        self.assertEqual('s', result['3Hourly15.WindDirection'])
        self.assertEqual('22', result['3Hourly15.GustSpeed'])
        self.assertEqual('1', result['3Hourly15.UVIndex'])
        self.assertEqual('33', result['3Hourly15.Precipitation'])
        self.assertEqual('Light Rain', result['3Hourly15.Outlook'])
        self.assertEqual('special://temp/weather/11.png', result['3Hourly15.OutlookIcon'])

        self.assertEqual('Mon', result['3Hourly16.Day'])
        self.assertEqual('12:00', result['3Hourly16.Time'])
        self.assertEqual('2014-03-03Z', result['3Hourly16.Date'])
        self.assertEqual('7', result['3Hourly16.ActualTemp'])
        self.assertEqual('4', result['3Hourly16.FeelsLikeTemp'])
        self.assertEqual('11', result['3Hourly16.WindSpeed'])
        self.assertEqual('s', result['3Hourly16.WindDirection'])
        self.assertEqual('22', result['3Hourly16.GustSpeed'])
        self.assertEqual('1', result['3Hourly16.UVIndex'])
        self.assertEqual('65', result['3Hourly16.Precipitation'])
        self.assertEqual('Heavy Rain', result['3Hourly16.Outlook'])
        self.assertEqual('special://temp/weather/40.png', result['3Hourly16.OutlookIcon'])

        self.assertEqual('Mon', result['3Hourly17.Day'])
        self.assertEqual('15:00', result['3Hourly17.Time'])
        self.assertEqual('2014-03-03Z', result['3Hourly17.Date'])
        self.assertEqual('7', result['3Hourly17.ActualTemp'])
        self.assertEqual('4', result['3Hourly17.FeelsLikeTemp'])
        self.assertEqual('7', result['3Hourly17.WindSpeed'])
        self.assertEqual('ssw', result['3Hourly17.WindDirection'])
        self.assertEqual('16', result['3Hourly17.GustSpeed'])
        self.assertEqual('1', result['3Hourly17.UVIndex'])
        self.assertEqual('48', result['3Hourly17.Precipitation'])
        self.assertEqual('Light Rain', result['3Hourly17.Outlook'])
        self.assertEqual('special://temp/weather/11.png', result['3Hourly17.OutlookIcon'])

        self.assertEqual('Mon', result['3Hourly18.Day'])
        self.assertEqual('18:00', result['3Hourly18.Time'])
        self.assertEqual('2014-03-03Z', result['3Hourly18.Date'])
        self.assertEqual('5', result['3Hourly18.ActualTemp'])
        self.assertEqual('3', result['3Hourly18.FeelsLikeTemp'])
        self.assertEqual('7', result['3Hourly18.WindSpeed'])
        self.assertEqual('wsw', result['3Hourly18.WindDirection'])
        self.assertEqual('11', result['3Hourly18.GustSpeed'])
        self.assertEqual('0', result['3Hourly18.UVIndex'])
        self.assertEqual('46', result['3Hourly18.Precipitation'])
        self.assertEqual('Light Rain', result['3Hourly18.Outlook'])
        self.assertEqual('special://temp/weather/45.png', result['3Hourly18.OutlookIcon'])

        self.assertEqual('Mon', result['3Hourly19.Day'])
        self.assertEqual('21:00', result['3Hourly19.Time'])
        self.assertEqual('2014-03-03Z', result['3Hourly19.Date'])
        self.assertEqual('4', result['3Hourly19.ActualTemp'])
        self.assertEqual('1', result['3Hourly19.FeelsLikeTemp'])
        self.assertEqual('9', result['3Hourly19.WindSpeed'])
        self.assertEqual('w', result['3Hourly19.WindDirection'])
        self.assertEqual('13', result['3Hourly19.GustSpeed'])
        self.assertEqual('0', result['3Hourly19.UVIndex'])
        self.assertEqual('13', result['3Hourly19.Precipitation'])
        self.assertEqual('Cloudy', result['3Hourly19.Outlook'])
        self.assertEqual('special://temp/weather/26.png', result['3Hourly19.OutlookIcon'])

        self.assertEqual('Tue', result['3Hourly20.Day'])
        self.assertEqual('00:00', result['3Hourly20.Time'])
        self.assertEqual('2014-03-04Z', result['3Hourly20.Date'])
        self.assertEqual('3', result['3Hourly20.ActualTemp'])
        self.assertEqual('0', result['3Hourly20.FeelsLikeTemp'])
        self.assertEqual('9', result['3Hourly20.WindSpeed'])
        self.assertEqual('wnw', result['3Hourly20.WindDirection'])
        self.assertEqual('18', result['3Hourly20.GustSpeed'])
        self.assertEqual('0', result['3Hourly20.UVIndex'])
        self.assertEqual('2', result['3Hourly20.Precipitation'])
        self.assertEqual('Partly Cloudy', result['3Hourly20.Outlook'])
        self.assertEqual('special://temp/weather/29.png', result['3Hourly20.OutlookIcon'])

        self.assertEqual('Tue', result['3Hourly21.Day'])
        self.assertEqual('03:00', result['3Hourly21.Time'])
        self.assertEqual('2014-03-04Z', result['3Hourly21.Date'])
        self.assertEqual('3', result['3Hourly21.ActualTemp'])
        self.assertEqual('-1', result['3Hourly21.FeelsLikeTemp'])
        self.assertEqual('9', result['3Hourly21.WindSpeed'])
        self.assertEqual('wnw', result['3Hourly21.WindDirection'])
        self.assertEqual('18', result['3Hourly21.GustSpeed'])
        self.assertEqual('0', result['3Hourly21.UVIndex'])
        self.assertEqual('2', result['3Hourly21.Precipitation'])
        self.assertEqual('Partly Cloudy', result['3Hourly21.Outlook'])
        self.assertEqual('special://temp/weather/29.png', result['3Hourly21.OutlookIcon'])

        self.assertEqual('Tue', result['3Hourly22.Day'])
        self.assertEqual('06:00', result['3Hourly22.Time'])
        self.assertEqual('2014-03-04Z', result['3Hourly22.Date'])
        self.assertEqual('2', result['3Hourly22.ActualTemp'])
        self.assertEqual('-1', result['3Hourly22.FeelsLikeTemp'])
        self.assertEqual('9', result['3Hourly22.WindSpeed'])
        self.assertEqual('w', result['3Hourly22.WindDirection'])
        self.assertEqual('16', result['3Hourly22.GustSpeed'])
        self.assertEqual('0', result['3Hourly22.UVIndex'])
        self.assertEqual('2', result['3Hourly22.Precipitation'])
        self.assertEqual('Partly Cloudy', result['3Hourly22.Outlook'])
        self.assertEqual('special://temp/weather/29.png', result['3Hourly22.OutlookIcon'])

        self.assertEqual('Tue', result['3Hourly23.Day'])
        self.assertEqual('09:00', result['3Hourly23.Time'])
        self.assertEqual('2014-03-04Z', result['3Hourly23.Date'])
        self.assertEqual('5', result['3Hourly23.ActualTemp'])
        self.assertEqual('2', result['3Hourly23.FeelsLikeTemp'])
        self.assertEqual('11', result['3Hourly23.WindSpeed'])
        self.assertEqual('w', result['3Hourly23.WindDirection'])
        self.assertEqual('20', result['3Hourly23.GustSpeed'])
        self.assertEqual('1', result['3Hourly23.UVIndex'])
        self.assertEqual('6', result['3Hourly23.Precipitation'])
        self.assertEqual('Partly Cloudy', result['3Hourly23.Outlook'])
        self.assertEqual('special://temp/weather/30.png', result['3Hourly23.OutlookIcon'])

        self.assertEqual('Tue', result['3Hourly24.Day'])
        self.assertEqual('12:00', result['3Hourly24.Time'])
        self.assertEqual('2014-03-04Z', result['3Hourly24.Date'])
        self.assertEqual('8', result['3Hourly24.ActualTemp'])
        self.assertEqual('5', result['3Hourly24.FeelsLikeTemp'])
        self.assertEqual('11', result['3Hourly24.WindSpeed'])
        self.assertEqual('w', result['3Hourly24.WindDirection'])
        self.assertEqual('22', result['3Hourly24.GustSpeed'])
        self.assertEqual('1', result['3Hourly24.UVIndex'])
        self.assertEqual('7', result['3Hourly24.Precipitation'])
        self.assertEqual('Partly Cloudy', result['3Hourly24.Outlook'])
        self.assertEqual('special://temp/weather/30.png', result['3Hourly24.OutlookIcon'])

        self.assertEqual('Tue', result['3Hourly25.Day'])
        self.assertEqual('15:00', result['3Hourly25.Time'])
        self.assertEqual('2014-03-04Z', result['3Hourly25.Date'])
        self.assertEqual('8', result['3Hourly25.ActualTemp'])
        self.assertEqual('6', result['3Hourly25.FeelsLikeTemp'])
        self.assertEqual('11', result['3Hourly25.WindSpeed'])
        self.assertEqual('w', result['3Hourly25.WindDirection'])
        self.assertEqual('18', result['3Hourly25.GustSpeed'])
        self.assertEqual('1', result['3Hourly25.UVIndex'])
        self.assertEqual('10', result['3Hourly25.Precipitation'])
        self.assertEqual('Sunny', result['3Hourly25.Outlook'])
        self.assertEqual('special://temp/weather/32.png', result['3Hourly25.OutlookIcon'])

        self.assertEqual('Tue', result['3Hourly26.Day'])
        self.assertEqual('18:00', result['3Hourly26.Time'])
        self.assertEqual('2014-03-04Z', result['3Hourly26.Date'])
        self.assertEqual('6', result['3Hourly26.ActualTemp'])
        self.assertEqual('4', result['3Hourly26.FeelsLikeTemp'])
        self.assertEqual('7', result['3Hourly26.WindSpeed'])
        self.assertEqual('wsw', result['3Hourly26.WindDirection'])
        self.assertEqual('11', result['3Hourly26.GustSpeed'])
        self.assertEqual('0', result['3Hourly26.UVIndex'])
        self.assertEqual('8', result['3Hourly26.Precipitation'])
        self.assertEqual('Clear', result['3Hourly26.Outlook'])
        self.assertEqual('special://temp/weather/31.png', result['3Hourly26.OutlookIcon'])

        self.assertEqual('Tue', result['3Hourly27.Day'])
        self.assertEqual('21:00', result['3Hourly27.Time'])
        self.assertEqual('2014-03-04Z', result['3Hourly27.Date'])
        self.assertEqual('5', result['3Hourly27.ActualTemp'])
        self.assertEqual('2', result['3Hourly27.FeelsLikeTemp'])
        self.assertEqual('7', result['3Hourly27.WindSpeed'])
        self.assertEqual('sw', result['3Hourly27.WindDirection'])
        self.assertEqual('13', result['3Hourly27.GustSpeed'])
        self.assertEqual('0', result['3Hourly27.UVIndex'])
        self.assertEqual('11', result['3Hourly27.Precipitation'])
        self.assertEqual('Partly Cloudy', result['3Hourly27.Outlook'])
        self.assertEqual('special://temp/weather/29.png', result['3Hourly27.OutlookIcon'])

        self.assertEqual('Wed', result['3Hourly28.Day'])
        self.assertEqual('00:00', result['3Hourly28.Time'])
        self.assertEqual('2014-03-05Z', result['3Hourly28.Date'])
        self.assertEqual('4', result['3Hourly28.ActualTemp'])
        self.assertEqual('1', result['3Hourly28.FeelsLikeTemp'])
        self.assertEqual('9', result['3Hourly28.WindSpeed'])
        self.assertEqual('sw', result['3Hourly28.WindDirection'])
        self.assertEqual('16', result['3Hourly28.GustSpeed'])
        self.assertEqual('0', result['3Hourly28.UVIndex'])
        self.assertEqual('16', result['3Hourly28.Precipitation'])
        self.assertEqual('Cloudy', result['3Hourly28.Outlook'])
        self.assertEqual('special://temp/weather/26.png', result['3Hourly28.OutlookIcon'])

        self.assertEqual('Wed', result['3Hourly29.Day'])
        self.assertEqual('03:00', result['3Hourly29.Time'])
        self.assertEqual('2014-03-05Z', result['3Hourly29.Date'])
        self.assertEqual('4', result['3Hourly29.ActualTemp'])
        self.assertEqual('1', result['3Hourly29.FeelsLikeTemp'])
        self.assertEqual('9', result['3Hourly29.WindSpeed'])
        self.assertEqual('sw', result['3Hourly29.WindDirection'])
        self.assertEqual('16', result['3Hourly29.GustSpeed'])
        self.assertEqual('0', result['3Hourly29.UVIndex'])
        self.assertEqual('23', result['3Hourly29.Precipitation'])
        self.assertEqual('Cloudy', result['3Hourly29.Outlook'])
        self.assertEqual('special://temp/weather/26.png', result['3Hourly29.OutlookIcon'])

        self.assertEqual('Wed', result['3Hourly30.Day'])
        self.assertEqual('06:00', result['3Hourly30.Time'])
        self.assertEqual('2014-03-05Z', result['3Hourly30.Date'])
        self.assertEqual('4', result['3Hourly30.ActualTemp'])
        self.assertEqual('1', result['3Hourly30.FeelsLikeTemp'])
        self.assertEqual('11', result['3Hourly30.WindSpeed'])
        self.assertEqual('sw', result['3Hourly30.WindDirection'])
        self.assertEqual('20', result['3Hourly30.GustSpeed'])
        self.assertEqual('0', result['3Hourly30.UVIndex'])
        self.assertEqual('24', result['3Hourly30.Precipitation'])
        self.assertEqual('Overcast', result['3Hourly30.Outlook'])
        self.assertEqual('special://temp/weather/26.png', result['3Hourly30.OutlookIcon'])

        self.assertEqual('Wed', result['3Hourly31.Day'])
        self.assertEqual('09:00', result['3Hourly31.Time'])
        self.assertEqual('2014-03-05Z', result['3Hourly31.Date'])
        self.assertEqual('6', result['3Hourly31.ActualTemp'])
        self.assertEqual('2', result['3Hourly31.FeelsLikeTemp'])
        self.assertEqual('13', result['3Hourly31.WindSpeed'])
        self.assertEqual('wsw', result['3Hourly31.WindDirection'])
        self.assertEqual('29', result['3Hourly31.GustSpeed'])
        self.assertEqual('1', result['3Hourly31.UVIndex'])
        self.assertEqual('55', result['3Hourly31.Precipitation'])
        self.assertEqual('Light Rain', result['3Hourly31.Outlook'])
        self.assertEqual('special://temp/weather/11.png', result['3Hourly31.OutlookIcon'])

        self.assertEqual('Wed', result['3Hourly32.Day'])
        self.assertEqual('12:00', result['3Hourly32.Time'])
        self.assertEqual('2014-03-05Z', result['3Hourly32.Date'])
        self.assertEqual('8', result['3Hourly32.ActualTemp'])
        self.assertEqual('3', result['3Hourly32.FeelsLikeTemp'])
        self.assertEqual('18', result['3Hourly32.WindSpeed'])
        self.assertEqual('w', result['3Hourly32.WindDirection'])
        self.assertEqual('38', result['3Hourly32.GustSpeed'])
        self.assertEqual('1', result['3Hourly32.UVIndex'])
        self.assertEqual('37', result['3Hourly32.Precipitation'])
        self.assertEqual('Light Rain', result['3Hourly32.Outlook'])
        self.assertEqual('special://temp/weather/11.png', result['3Hourly32.OutlookIcon'])

        self.assertEqual('Wed', result['3Hourly33.Day'])
        self.assertEqual('15:00', result['3Hourly33.Time'])
        self.assertEqual('2014-03-05Z', result['3Hourly33.Date'])
        self.assertEqual('8', result['3Hourly33.ActualTemp'])
        self.assertEqual('3', result['3Hourly33.FeelsLikeTemp'])
        self.assertEqual('18', result['3Hourly33.WindSpeed'])
        self.assertEqual('w', result['3Hourly33.WindDirection'])
        self.assertEqual('36', result['3Hourly33.GustSpeed'])
        self.assertEqual('1', result['3Hourly33.UVIndex'])
        self.assertEqual('14', result['3Hourly33.Precipitation'])
        self.assertEqual('Partly Cloudy', result['3Hourly33.Outlook'])
        self.assertEqual('special://temp/weather/30.png', result['3Hourly33.OutlookIcon'])

        self.assertEqual('Wed', result['3Hourly34.Day'])
        self.assertEqual('18:00', result['3Hourly34.Time'])
        self.assertEqual('2014-03-05Z', result['3Hourly34.Date'])
        self.assertEqual('7', result['3Hourly34.ActualTemp'])
        self.assertEqual('2', result['3Hourly34.FeelsLikeTemp'])
        self.assertEqual('13', result['3Hourly34.WindSpeed'])
        self.assertEqual('w', result['3Hourly34.WindDirection'])
        self.assertEqual('27', result['3Hourly34.GustSpeed'])
        self.assertEqual('0', result['3Hourly34.UVIndex'])
        self.assertEqual('6', result['3Hourly34.Precipitation'])
        self.assertEqual('Partly Cloudy', result['3Hourly34.Outlook'])
        self.assertEqual('special://temp/weather/29.png', result['3Hourly34.OutlookIcon'])

        self.assertEqual('Wed', result['3Hourly35.Day'])
        self.assertEqual('21:00', result['3Hourly35.Time'])
        self.assertEqual('2014-03-05Z', result['3Hourly35.Date'])
        self.assertEqual('5', result['3Hourly35.ActualTemp'])
        self.assertEqual('1', result['3Hourly35.FeelsLikeTemp'])
        self.assertEqual('13', result['3Hourly35.WindSpeed'])
        self.assertEqual('wsw', result['3Hourly35.WindDirection'])
        self.assertEqual('25', result['3Hourly35.GustSpeed'])
        self.assertEqual('0', result['3Hourly35.UVIndex'])
        self.assertEqual('7', result['3Hourly35.Precipitation'])
        self.assertEqual('Partly Cloudy', result['3Hourly35.Outlook'])
        self.assertEqual('special://temp/weather/29.png', result['3Hourly35.OutlookIcon'])
        
    def test_text(self):
        forecast_data = json.load(open(FORECASTTEXT))
        result = self.jsonparser.text(forecast_data)
        self.assertEqual('16:00 Mon 24 Feb 2014', result['TextForecast.IssuedAt'])

        self.assertEqual('Headline', result['Text.Paragraph0.Title'])
        self.assertEqual('Rain clearing eastwards, showers following, with increasing winds.', result['Text.Paragraph0.Content'])
        self.assertEqual('This Evening and Tonight', result['Text.Paragraph1.Title'])
        self.assertEqual('Rain arriving in the far west around dusk will clear eastwards overnight, this heaviest in the west and over high ground, where winds will also become strong. Mild, with clear spells and scattered showers following. Minimum Temperature 5C.', result['Text.Paragraph1.Content'])
        self.assertEqual('Tuesday', result['Text.Paragraph2.Title'])
        self.assertEqual('Some dry and bright weather is likely at times but also scattered blustery, heavy showers. Remaining windy, especially around exposed coasts and hills where gales are likely. Maximum Temperature 9C.', result['Text.Paragraph2.Content'])
        self.assertEqual('Wednesday to Friday', result['Text.Paragraph3.Title'])
        self.assertEqual('Sunny spells and lighter winds on Wednesday, some showers along the coast. Wet and windy overnight, turning showery on Thursday and Friday, becoming wintry over hills.', result['Text.Paragraph3.Content'])
        self.assertEqual('Saturday 1 Mar 2014 to Monday 10 Mar 2014', result['Text.Paragraph4.Title'])
        self.assertEqual('The weekend will start unsettled with showers or longer spells of rain, with some heavier bursts at first. This will be most persistent in the far southeast and far north, with a risk of hill snow in the north. There will be some drier slots too, especially on Sunday with a risk of local frost and icy surfaces. Temperatures near normal. Through the next week it will remain unsettled in northern parts, with further rain or showers, and some hill snow. It will be mainly dry but fairly cloudy towards the south with isolated patchy frost. During the middle part of the week rain may spread southwards for a time, before turning wet and windy in the northwest again later, with a risk of gales.', result['Text.Paragraph4.Content'])
        self.assertEqual('Tuesday 11 Mar 2014 to Tuesday 25 Mar 2014', result['Text.Paragraph5.Title'])
        self.assertEqual('Current indications suggest a more typically unsettled pattern across the United Kingdom through much of March. Through this period we can expect to see fairly average conditions, which would mean spells of wet and windy weather, mostly in the north and west, but still some decent sunny spells in between. The best of the drier, brighter conditions is most likely in the south and east of the UK. Temperatures are likely to be around average, which may lead to more frequent incidences of frost compared to recent weeks.', result['Text.Paragraph5.Content'])
