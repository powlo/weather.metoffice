import os
import xbmc
import xbmcaddon
import utilities

WEATHER_CODES = {
    'na': ('na', 'Not Available'),
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

VISIBILITY_CODES = {
    'UN': 'Unknown',
    'VP': 'Very Poor',
    'PO': 'Poor',
    'MO': 'Moderate',
    'GO': 'Good',
    'VG': 'Very Good',
    'EX': 'Excellent'
}

UV_CODES = {
    '0' : 'grey',
    '1' : 'green',
    '2' : 'green',
    '3' : 'yellow',
    '4' : 'yellow',
    '5' : 'yellow',
    '6' : 'red',
    '7' : 'red',
    '8' : 'purple',
    '9' : 'purple',
    '10': 'purple',
    '11': 'purple'
    }

__addon__ = xbmcaddon.Addon()
__addonpath__ = __addon__.getAddonInfo('path')
__media__ = os.path.join( __addonpath__, 'resources', 'media' )

WEATHER_ICON = xbmc.translatePath('special://temp/weather/%s.png').decode("utf-8")
TEMP_ICON = os.path.join(__media__, 'temp', '%s.png')
WIND_ICON = os.path.join(__media__, 'wind', 'average', '%s.png')
GUST_ICON = os.path.join(__media__, 'wind', 'gust', '%s.png')
UV_ICON = os.path.join(__media__, 'uv', '%s.png')

def regional(data):
    """
    Parse data to produce regional forecast data
    """
    forecast = dict()
    rf = data['RegionalFcst']
    forecast['RegionalForecast.IssuedAt'] = rf['issuedAt'].rstrip('Z')
    count = 0
    for period in rf['FcstPeriods']['Period']:
        #have to check type because json can return list or dict here
        if isinstance(period['Paragraph'],list):
            for paragraph in period['Paragraph']:
                forecast['Regional.Paragraph%d.Title' % count] = paragraph['title'].rstrip(':').lstrip('UK Outlook for')
                forecast['Regional.Paragraph%d.Content' % count] = paragraph['$']
                count+=1
        else:
            forecast['Regional.Paragraph%d.Title' % count] = period['Paragraph']['title'].rstrip(':').lstrip('UK Outlook for')
            forecast['Regional.Paragraph%d.Content' % count] = period['Paragraph']['$']
            count+=1
    return forecast

def threehourly(data):
    """
    Parse data to produce three hourly data
    """
    forecast = dict()
    dv = data['SiteRep']['DV']
    forecast['3HourlyForecast.IssuedAt'] = dv.get('dataDate').rstrip('Z')
    count = 0
    for period in dv['Location']['Period']:
        for rep in period['Rep']:
            #extra xbmc targeted info:
            weather_type = rep.get('W', 'NA')
            forecast['3Hourly%d.Outlook' % count] = WEATHER_CODES.get(weather_type)[1]
            forecast['3Hourly%d.WindSpeed' % count] = rep.get('S', 'n/a')
            forecast['3Hourly%d.WindIcon' % count] = WIND_ICON % rep.get('D', 'na')
            forecast['3Hourly%d.GustSpeed' % count] = rep.get('G', 'n/a')
            forecast['3Hourly%d.GustIcon' % count] = GUST_ICON % rep.get('D', 'na')
            forecast['3Hourly%d.UVIndex' % count] = rep.get('U', 'n/a')
            forecast['3Hourly%d.UVIcon' % count] = UV_ICON % UV_CODES.get(rep.get('U', '0'),'grey')
            forecast['3Hourly%d.Precipitation' % count] = rep.get('Pp')
            forecast['3Hourly%d.OutlookIcon' % count] = WEATHER_ICON % WEATHER_CODES.get(weather_type, 'NA')[0]
            forecast['3Hourly%d.Day' % count] = utilities.day_name(period.get('value'))
            forecast['3Hourly%d.Time' % count] = utilities.minutes_as_time(int(rep.get('$')))
            forecast['3Hourly%d.Date' % count] = period.get('value')
            forecast['3Hourly%d.ActualTempIcon' % count] = TEMP_ICON % rep['T']
            forecast['3Hourly%d.FeelsLikeTempIcon' % count] = TEMP_ICON % rep['F']
            count +=1
    return forecast

def observation(data):
    """
    Parse data to produce observation (current) data
    """
    forecast = dict()
    dv = data['SiteRep']['DV']
    forecast['HourlyObservation.IssuedAt'] = dv.get('dataDate').rstrip('Z')
    latest_obs = dv['Location']['Period'][-1]['Rep'][-1]
    forecast['Current.Location'] = dv['Location']['name']
    forecast['Current.Condition'] = WEATHER_CODES[latest_obs.get('W', 'NA')][1]
    forecast['Current.Visibility'] = latest_obs.get('V', 'n/a')
    forecast['Current.Pressure'] = latest_obs.get('P', 'n/a')
    forecast['Current.Temperature'] = latest_obs.get('T', 'n/a').split('.')[0]
    forecast['Current.Wind'] = latest_obs.get('S', 'n/a')
    forecast['Current.WindDirection'] = latest_obs.get('D', 'n/a')
    forecast['Current.WindGust'] = latest_obs.get('G', 'n/a')
    forecast['Current.OutlookIcon'] = '%s.png' % WEATHER_CODES[latest_obs.get('W', 'NA')][0]
    forecast['Current.FanartCode'] = '%s.png' % WEATHER_CODES[latest_obs.get('W','NA')][0]
    return forecast

def daily(data):
    """
    Parse data to produce daily forecast data
    """
    forecast = dict()
    dv = data['SiteRep']['DV']
    forecast['DailyForecast.IssuedAt'] = dv.get('dataDate').rstrip('Z')
    for p, period in enumerate(dv['Location']['Period']):
        forecast['Day%d.Title' %p] = utilities.day_name(period.get('value'))
        for rep in period['Rep']:
            weather_type = rep.get('W', 'na')
            if rep.get('$') == 'Day':
                forecast['Day%d.HighTemp' %p] = rep.get('Dm', 'na')
                forecast['Day%d.HighTempIcon' % p] = TEMP_ICON % rep.get('Dm', 'na')
                forecast['Day%d.Outlook' %p] = WEATHER_CODES.get(weather_type)[1]
                forecast['Day%d.OutlookIcon' % p] = WEATHER_ICON % WEATHER_CODES.get(weather_type, 'na')[0]
                forecast['Day%d.WindSpeed' % p] = rep.get('S', 'na')
                forecast['Day%d.WindIcon' % p] = WIND_ICON % rep.get('D', 'na')
                forecast['Day%d.GustIcon' % p] = GUST_ICON % rep.get('D', 'na')
                forecast['Day%d.UVIcon' % p] = UV_ICON % UV_CODES.get(rep.get('U', '0'),'grey')
            elif rep.get('$') == 'Night':
                forecast['Day%d.LowTemp' %p] = rep.get('Nm', 'na')
                forecast['Day%d.LowTempIcon' % p] = TEMP_ICON % rep.get('Nm', 'na')
    print forecast
    return forecast
