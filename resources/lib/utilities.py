from datetime import datetime
import time

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
def parse_json_sitelist(data):
    pass

def parse_json_day_forecast(data):
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
    return forecast

def parse_json_current_forecast(data):
    #need a way of choosing day or night forecast
    forecast = dict()
    latest = data['SiteRep']['DV']['Location']['Period'][0]['Rep'][0]
    temp = latest['Dm']
    weather_type = latest['W']
    wind = latest['S']
    direction = latest['D']
    humidity = latest['Hn']
    feelslike = latest['FDm']
    maxuvindex = latest['U']
    weather_type = latest['W']
    outlook_text = WEATHER_CODES[weather_type][1]
    outlook_code = WEATHER_CODES[weather_type][0]   

    forecast['Current.Location'] = data['SiteRep']['DV']['Location']['name'].title()
    forecast['Current.Condition'] = outlook_text
    forecast['Current.Temperature'] = temp
    forecast['Current.Wind'] = wind
    forecast['Current.WindDirection'] = direction
    forecast['Current.Humidity'] = humidity
    forecast['Current.FeelsLike'] = feelslike
    forecast['Current.UVIndex'] = maxuvindex
    forecast['Current.DewPoint'] = ''
    forecast['Current.OutlookIcon'] = '%s.png' % outlook_code
    forecast['Current.FanartCode'] = '%s.png' % outlook_code
    return forecast

def parse_json_observations(data):
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
    temp = latest_obs['T']
    weather_type = latest_obs['W']
    wind = latest_obs['S']
    direction = latest_obs['D']
    weather_type = latest_obs['W']
    outlook_text = WEATHER_CODES[weather_type][1]
    outlook_code = WEATHER_CODES[weather_type][0]   

    observation = dict()
    observation['Current.Location'] = data['SiteRep']['DV']['Location']['name']
    observation['Current.Condition'] = outlook_text
    observation['Current.Temperature'] = temp
    observation['Current.Wind'] = wind
    observation['Current.WindDirection'] = direction
    observation['Current.OutlookIcon'] = '%s.png' % outlook_code
    observation['Current.FanartCode'] = '%s.png' % outlook_code

    return observation

def clear():
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
    for count in range (MAX_DAYS):
        d['Day%i.Title' % count] = 'N/A'
        d['Day%i.HighTemp' % count] = '0'
        d['Day%i.LowTemp' % count] = '0'
        d['Day%i.Outlook' % count] = 'N/A'
        d['Day%i.OutlookIcon' % count] = 'na.png'
        d['Day%i.FanartCode' % count] = 'na'

    return d