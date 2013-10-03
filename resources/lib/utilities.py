from datetime import datetime
import time
import math
import urllib2
import json

MAX_DAYS = 5
MAX_INTERVALS = 8

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

#This list must appear in the same order as it appears in 
#the settings.xml in order for the indexes to align.
GEOIP_PROVIDERS = [{'url':'http://ip-api.com/json/', 'latitude':'lat', 'longitude':'lon'},
             {'url':'http://freegeoip.net/json/', 'latitude':'latitude', 'longitude':'longitude'},
             {'url':'http://www.telize.com/geoip/','latitude':'latitude', 'longitude':'longitude'},
             {'url':'http://api.hostip.info/get_json.php?position=true','latitude':'lat', 'longitude':'lng'},
             {'url':'http://geoiplookup.net/geoapi.php?output=json', 'latitude':'latitude', 'longitude':'longitude'}
                   ]

LONG_REGIONAL_NAMES = {'os': 'Orkney and Shetland',
                       'he': 'Highland and Eilean Siar',
                       'gr': 'Grampian',
                       'ta': 'Tayside',
                       'st': 'Strathclyde',
                       'dg': 'Dumfries, Galloway, Lothian',
                       'ni': 'Northern Ireland',
                       'yh': 'Yorkshire and the Humber',
                       'ne': 'Northeast England',
                       'em': 'East Midlands',
                       'ee': 'East of England',
                       'se': 'London and Southeast England',
                       'nw': 'Northwest England',
                       'wm': 'West Midlands',
                       'sw': 'Southwest England',
                       'wl': 'Wales',
                       'uk': 'United Kingdom'}
#calculate sunrise/sunset:
# H = | (1/15)*arccos[-tan(L)*tan(23.44*sin(360(D+284)/365))] |.
# http://www.had2know.com/society/sunrise-sunset-time-calculator-formula.html

#Calculate noon
#http://en.wikipedia.org/wiki/Equation_of_time#Alternative_calculation

def day_name(date):
    return datetime.fromtimestamp(time.mktime(time.strptime(date, '%Y-%m-%dZ'))).strftime('%A')

def minutes_as_time(minutes):
    return time.strftime('%H:%M', time.gmtime(minutes*60))

def parse_json_default_forecast(data):
    """
    Takes raw api data and converts into something recognisable to xbmc
    
    Met Office Daily Forecast Data:
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
    #todo: set night values
    forecast = dict()
    for count, day in enumerate(data['SiteRep']['DV']['Location']['Period']):
        weather_type = day['Rep'][0]['W']
        forecast['Day%s.Title' % count] = day_name(day.get('value'))
        forecast['Day%s.HighTemp' % count] = day['Rep'][0]['Dm']
        forecast['Day%s.LowTemp' % count] = day['Rep'][1]['Nm']
        forecast['Day%s.Outlook' % count] = WEATHER_CODES[weather_type][1]
        forecast['Day%s.OutlookIcon' % count] = "%s.png" % WEATHER_CODES[weather_type][0]
        
    #Add empty days for those not supported by Datapoint
    forecast['Day5.Title'] = ''
    forecast['Day6.Title'] = ''

    return forecast

def parse_json_daily_forecast(data):
    """
    Takes raw api data and converts into something recognisable to xbmc
    
    Met Office Daily Forecast Data:
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
    forecast = dict()
    dv = data['SiteRep']['DV']
    #test on dv as beginnings of universal parser
    if dv['type'] == 'Forecast':
        for p, period in enumerate(dv['Location']['Period']):
            for rep in period:
                rep_value = rep['value']
                weather_type = rep.get('W', 'NA')
                for key, value in rep.iteritems():
                    forecast['Daily%s.%s.%s' % (p, rep_value, key)] = value

                #extra xbmc targeted info:
                forecast['Daily%s.%s.Outlook' % (p, rep_value)] = WEATHER_CODES.get(weather_type)[1]
                forecast['Daily%s.%s.OutlookIcon' % (p, rep_value)] = "%s.png" % WEATHER_CODES.get(weather_type)[0]
            forecast['Daily%s.DayOfWeek' % p] = day_name(period.get('value'))
    return forecast


def parse_json_3hourly_forecast(data):
    """
    <Param name="F" units="C">Feels Like Temperature</Param>
    <Param name="G" units="mph">Wind Gust</Param>
    <Param name="H" units="%">Screen Relative Humidity</Param>
    <Param name="T" units="C">Temperature</Param><Param name="V" units="">Visibility</Param>
    <Param name="D" units="compass">Wind Direction</Param>
    <Param name="S" units="mph">Wind Speed</Param>
    <Param name="U" units="">Max UV Index</Param>
    <Param name="W" units="">Weather Type</Param>
    <Param name="Pp" units="%">Precipitation Probability</Param>
    """
    """
    NB/TODO: If a report contains the value "Day", then we set day values
    if it contains night then we set night values
    if it contains a number then we set hourly values
    use these facts to automate json handling
    """
    forecast = dict()
    interval = 0
    for period in data['SiteRep']['DV']['Location']['Period']:
        for report in period['Rep']:
            forecast['3Hour%s.Day' % interval] = day_name(period.get('value'))
            forecast['3Hour%s.Time' % interval] = minutes_as_time(int(report.get('$')))
            forecast['3Hour%s.FeelsTemp' % interval] = report.get('F')
            forecast['3Hour%s.WindGust' % interval] = report.get('G')
            forecast['3Hour%s.Humidity' % interval] = report.get('H')
            forecast['3Hour%s.Temp' % interval] = report.get('T')
            forecast['3Hour%s.Visibility' % interval] = report.get('T')
            forecast['3Hour%s.WindDirection' % interval] = report.get('D')
            forecast['3Hour%s.WindSpeed' % interval] = report.get('S')
            forecast['3Hour%s.MaxUV' % interval] = report.get('U')
            forecast['3Hour%s.OutlookIcon' % interval] = '%s.png' % WEATHER_CODES[report.get('W', 'NA')][0]
            forecast['3Hour%s.Precipitation' % interval] = report.get('Pp')
            interval += 1
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
    observation['Current.Visibility'] = latest_obs.get('V', 'n/a')
    observation['Current.Pressure'] = latest_obs.get('P', 'n/a')
    observation['Current.Temperature'] = latest_obs.get('T', 'n/a')
    observation['Current.Wind'] = latest_obs.get('S', 'n/a')
    observation['Current.WindDirection'] = latest_obs.get('D', 'n/a')
    observation['Current.WindGust'] = latest_obs.get('G', 'n/a')
    observation['Current.OutlookIcon'] = '%s.png' % WEATHER_CODES[latest_obs.get('W', 'NA')][0]
    observation['Current.FanartCode'] = '%s.png' % WEATHER_CODES[latest_obs.get('W','NA')][0]

    return observation

def parse_regional_forecast(data):
    forecast = dict()
    count = 0
    rf = data['RegionalFcst']
    forecast['Regional.issuedAt'] = rf['issuedAt']
    for period in rf['FcstPeriods']['Period']:
        #have to check type because json can return list or dict here
        if isinstance(period['Paragraph'],list):
            for paragraph in period['Paragraph']:
                forecast['Regional.Period%s.Title' % count] = paragraph['title'].rstrip(':').lstrip('UK Outlook for')
                forecast['Regional.Period%s.Content' % count] = paragraph['$']
                count+=1
        else:
            forecast['Regional.Period%s.Title' % count] = period['Paragraph']['title'].rstrip(':').lstrip('UK Outlook for')
            forecast['Regional.Period%s.Content' % count] = period['Paragraph']['$']
            count+=1
    return forecast

def empty_daily_forecast():
    d = dict()
    for count in range (MAX_DAYS):
        d['Day%i.Title' % count] = 'N/A'
        d['Day%i.HighTemp' % count] = '0'
        d['Day%i.LowTemp' % count] = '0'
        d['Day%i.Outlook' % count] = 'N/A'
        d['Day%i.OutlookIcon' % count] = 'na.png'
        d['Day%i.FanartCode' % count] = 'na'
    return d

def empty_3hourly_forecast():
    d = dict()
    for day in range (MAX_DAYS):
        for interval in range (MAX_INTERVALS):
            d['3Hour%s.FeelsTemp' % interval*day] = 'N/A'
            d['3Hour%s.WindGust' % interval*day] = 'N/A'
            d['3Hour%s.Humidity' % interval*day] = 'N/A'
            d['3Hour%s.Temp' % interval*day] = 'N/A'
            d['3Hour%s.Visibility' % interval*day] = 'N/A'
            d['3Hour%s.WindDirection' % interval*day] = 'N/A'
            d['3Hour%s.WindSpeed' % interval*day] = 'N/A'
            d['3Hour%s.MaxUV' % interval*day] = 'N/A'
            d['3Hour%s.OutlookIcon' % interval*day] = 'na.png'
            d['3Hour%s.Precipitation' % interval*day] = 'N/A'
    return d

#Not sure what the point is in setting empty values
#should be checked in skin surely.
def empty_regional_forecast():
    d = dict()
    for period in range(6):
        d['Regional.Period%s.Title' % period] = ''
        d['Regional.Period%s.Content' % period] = ''
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


def clean_sitelist(sitelist):
    """
    A bug in datapoint returns keys prefixed with '@'
    This func chops them out
    """
    new_sites = []
    new_site = {}

    for site in sitelist:
        for key in site:
           if key.startswith('@'):
               new_key = key[1:]
               new_site[new_key] = site[key]
        new_sites.append(new_site.copy())
    return new_sites

def filter_sitelist(text, sitelist):
    filteredsitelist = list()
    for x in sitelist:
        if x['name'].lower().find(text.lower()) != -1:
            filteredsitelist.append(x)
    return filteredsitelist

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