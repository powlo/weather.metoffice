from datetime import datetime
import time
import math
import urllib2
import json

MAX_DAYS = 5

#Translate Datapoint Codes into XBMC codes
WEATHER_CODES = {
    'NA': ('na', 'Not Available'),
    '0': ('31', 'Clear'), #night
    '1': ('32', 'Sunny'),
    '2': ('29', 'Partly Cloudy'), #night
    '3': ('30', 'Partly Cloudy'),
#   '4': ('na', 'Not available'),
    '5': ('21', 'Mist'),
    '6': ('20', 'Fog'),
    '7': ('26', 'Cloudy'),
    '8': ('26', 'Overcast'),
    '9': ('45', 'Light Rain'), #night
    '10': ('11', 'Light Rain'),
    '11': ('9', 'Drizzle'),
    '12': ('11', 'Light Rain'),
    '13': ('45', 'Heavy Rain'), #night
    '14': ('40', 'Heavy Rain'),
    '15': ('40', 'Heavy Rain'),
    '16': ('46', 'Sleet'), #night
    '17': ('6', 'Sleet'),
    '18': ('6', 'Sleet'),
    '19': ('45', 'Hail'), #night
    '20': ('18', 'Hail'),
    '21': ('18', 'Hail'),
    '22': ('46', 'Light Snow'), #night
    '23': ('14', 'Light snow'),
    '24': ('14', 'Light Snow'),
    '25': ('46', 'Heavy Snow'), #night
    '26': ('16', 'Heavy Snow'),
    '27': ('16', 'Heavy Snow'),
    '28': ('47', 'Thunder'), #night
    '29': ('17', 'Thunder'),
    '30': ('17', 'Thunder')
}

#calculate sunrise/sunset:
# H = | (1/15)*arccos[-tan(L)*tan(23.44*sin(360(D+284)/365))] |.
# http://www.had2know.com/society/sunrise-sunset-time-calculator-formula.html

#Calculate noon
#http://en.wikipedia.org/wiki/Equation_of_time#Alternative_calculation

def parse_json_daily_forecast(data):
    """
    Takes raw api data and converts into something recognisable to xbmc
    
    Met Office Forecast Data:    
    <Param name="FDm" units="C">Feels Like Day Maximum Temperature</Param>
    <Param name="Dm" units="C">Day Maximum Temperature</Param>
    <Param name="FNm" units="C">Feels Like Night Minimum Temperature</Param>
    <Param name="Nm" units="C">Night Minimum Temperature</Param>
    <Param name="Gn" units="mph">Wind Gust Noon</Param>
    <Param name="Gm" units="mph">Wind Gust Midnight</Param>
    <Param name="Hn" units="%">Screen Relative Humidity Noon</Param>
    <Param name="Hm" units="%">Screen Relative Humidity Midnight</Param>
    <Param name="V" units="">Visibility</Param>
    <Param name="D" units="compass">Wind Direction</Param>
    <Param name="S" units="mph">Wind Speed</Param>
    <Param name="U" units="">Max UV Index</Param>
    <Param name="W" units="">Weather Type</Param>
    <Param name="PPd" units="%">Precipitation Probability Day</Param>
    <Param name="PPn" units="%">Precipitation Probability Night</Param>
    """
    #todo: rewrite this so it doesn't build dicts within a dict. this is unnecessary
    forecast = dict()
    for count, day in enumerate(data['SiteRep']['DV']['Location']['Period']):
        weather_type = day['Rep'][0]['W']
        forecast['Day%s' % count] = dict()
        forecast['Day%s' % count]['Title'] = datetime.fromtimestamp(time.mktime(time.strptime(day['value'], '%Y-%m-%dZ'))).strftime('%A')
        forecast['Day%s' % count]['HighTemp'] = day['Rep'][0]['Dm']
        forecast['Day%s' % count]['LowTemp'] = day['Rep'][1]['Nm']
        forecast['Day%s' % count]['Outlook'] = WEATHER_CODES[weather_type][1]
        forecast['Day%s' % count]['OutlookIcon'] = "%s.png" % WEATHER_CODES[weather_type][0]
        forecast['Day%s' % count]['FanartCode'] = "%s.png" % WEATHER_CODES[weather_type][0]
        
    #Add empty days for those not supported by Datapoint
    forecast['Day5'] = dict()
    forecast['Day5']['Title'] = ''
    forecast['Day6'] = dict()
    forecast['Day6']['Title'] = ''

    return forecast

def parse_json_observation(data):
    """
    Observations return the following data:
    <Param name="G" units="mph">Wind Gust</Param>
    <Param name="T" units="C">Temperature</Param>
    <Param name="V" units="m">Visibility</Param>
    <Param name="D" units="compass">Wind Direction</Param>
    <Param name="S" units="mph">Wind Speed</Param>
    <Param name="W" units="">Weather Type</Param>
    <Param name="P" units="hpa">Pressure</Param>    
    """
    latest_obs = data['SiteRep']['DV']['Location']['Period'][-1]['Rep'][-1]
    observation = dict()
    observation['Current.Location'] = data['SiteRep']['DV']['Location']['name']
    observation['Current.Condition'] = WEATHER_CODES[latest_obs.get('W', 'NA')][1]
    observation['Current.Visibility'] = latest_obs.get('V')
    observation['Current.Pressure'] = latest_obs.get('P')
    observation['Current.Temperature'] = latest_obs.get('T')
    observation['Current.Wind'] = latest_obs.get('S')
    observation['Current.WindDirection'] = latest_obs.get('D')
    observation['Current.OutlookIcon'] = '%s.png' % WEATHER_CODES[latest_obs.get('W', 'NA')][0]  
    observation['Current.FanartCode'] = '%s.png' % WEATHER_CODES[latest_obs.get('W','NA')][0]  

    return observation

def empty_forecast():
    d = dict()
    for count in range (MAX_DAYS):
        d['Day%i.Title' % count] = 'N/A'
        d['Day%i.HighTemp' % count] = '0'
        d['Day%i.LowTemp' % count] = '0'
        d['Day%i.Outlook' % count] = 'N/A'
        d['Day%i.OutlookIcon' % count] = 'na.png'
        d['Day%i.FanartCode' % count] = 'na'
    return d

def empty_observation():
    d = dict()
    d['Current.Condition'] = 'N/A'
    d['Current.Temperature'] = '0'
    d['Current.Wind'] = '0'
    d['Current.WindDirection'] = 'N/A'
    d['Current.Humidity'] = '0'
    d['Current.FeelsLike'] = '0'
    d['Current.UVIndex'] = '0'
    d['Current.DewPoint'] = '0'
    d['Current.OutlookIcon'] = 'na.png'
    d['Current.FanartCode'] = 'na'
    return d

def filter_sitelist(text, sitelist):
    filteredsitelist = list()
    for x in sitelist:
        if x['name'].lower().find(text.lower()) != -1:
            filteredsitelist.append(x)
    return filteredsitelist

def get_freegeoipnet(datatype='json'):
    url = 'http://freegeoip.net/%s/' % datatype
    return retryurlopen(url)

def haversine_distance(lat1, lon1, lat2, lon2):
    EARTH_RADIUS = 6371
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dlat = lat2-lat1
    dlon = lon2-lon1
    a = math.sin(dlat/2)**2 + \
        math.cos(lat1) * math.cos(lat2) * \
        math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return EARTH_RADIUS * c

def retryurlopen(url, retry=3):
    while True:
        try:
            return urllib2.urlopen(url).read()
        except:
            if retry:
                retry -= 1
            else:
                raise

def dewpoint_temp(temp, humidity):
    return str(int(temp) - ((100 - int(humidity))/5))