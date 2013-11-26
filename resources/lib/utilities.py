from datetime import datetime
import json
import math
import os
import time
import urllib2
import xbmc
import xbmcaddon

MAX_DAYS = 5
MAX_INTERVALS = 8

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

def parse_json_default_forecast(data):
    """
    Takes raw datapoint api data and generates a dictionary of
    weather window properties for a 5 day forecast that can be
    recognised by a standard skin.
    """
    #todo: set night values
    forecast = dict()
    for count, day in enumerate(data['SiteRep']['DV']['Location']['Period']):
        weather_type = day['Rep'][0]['W']
        forecast['Day%s.Title' % count] = day_name(day.get('value'))
        forecast['Day%s.HighTemp' % count] = day['Rep'][0]['Dm']
        forecast['Day%s.LowTemp' % count] = day['Rep'][1]['Nm']
        forecast['Day%s.Outlook' % count] = WEATHER_CODES[weather_type][1]
        forecast['Day%s.OutlookIcon' % count] = WEATHER_ICON % WEATHER_CODES[weather_type][0]
        
    #Add empty days for those not supported by Datapoint
    forecast['Day5.Title'] = ''
    forecast['Day6.Title'] = ''
    return forecast

def parse_json_report(data):
    """
    Takes raw datapoint api data and generates a dictionary of
    XBMC weather window properties for a given forecast. In
    order for these properties to be displayed a customised
    version of the skin will be required.
    """
    forecast = dict()
    if data.get('SiteRep') and data['SiteRep'].get('DV'):
        dv = data['SiteRep']['DV']
        if dv.get('type') == 'Forecast':
            #look at how cludgy this is...
            if dv['Location']['Period'][0]['Rep'][0]['$'] == 'Day':
                forecast['DailyForecast.IssuedAt'] = dv.get('dataDate').rstrip('Z')
            else:
                forecast['3HourlyForecast.IssuedAt'] = dv.get('dataDate').rstrip('Z')
            #Parse Daily or 3Hourly Forecast
            for p, period in enumerate(dv['Location']['Period']):
                for rep in period['Rep']:
                    dollar = rep.pop('$')
                    tim = 'None'
                    if dollar != 'Day' and dollar != 'Night':
                        tim = minutes_as_time(int(dollar))
                        dollar = 'Hour%d' % (int(dollar)/60)
                    for key, value in rep.iteritems():
                        if key == 'V':
                            try:
                                value = VISIBILITY_CODES[value]
                            except KeyError:
                                pass
                        forecast['Forecast.Day%s.%s.%s' % (p, dollar, key)] = value
                    #extra xbmc targeted info:
                    weather_type = rep.get('W', 'NA')
                    forecast['Forecast.Day%s.%s.Outlook' % (p, dollar)] = WEATHER_CODES.get(weather_type)[1]
                    forecast['Forecast.Day%s.%s.WindIcon' % (p, dollar)] = WIND_ICON % rep.get('D', 'na')
                    forecast['Forecast.Day%s.%s.GustIcon' % (p, dollar)] = GUST_ICON % rep.get('D', 'na')
                    forecast['Forecast.Day%s.%s.UVIcon' % (p, dollar)] = UV_ICON % UV_CODES.get(rep.get('U', '0'),'grey')
                    forecast['Forecast.Day%s.%s.OutlookIcon' % (p, dollar)] = WEATHER_ICON % WEATHER_CODES.get(weather_type, 'NA')[0]
                    forecast['Forecast.Day%s.%s.Title' % (p, dollar)] = day_name(period.get('value'))
                    forecast['Forecast.Day%s.%s.Time' % (p, dollar)] = tim
                    forecast['Forecast.Day%s.%s.Date' % (p, dollar)] = period.get('value')
                    if dollar == 'Day':
                        forecast['Forecast.Day%s.%s.ActualTempIcon' % (p, dollar)] = TEMP_ICON % rep['Dm']
                    elif dollar =='Night':
                        forecast['Forecast.Day%s.%s.ActualTempIcon' % (p, dollar)] = TEMP_ICON % rep['Nm']
                    else:
                        forecast['Forecast.Day%s.%s.ActualTempIcon' % (p, dollar)] = TEMP_ICON % rep['T']
                        forecast['Forecast.Day%s.%s.FeelsLikeTempIcon' % (p, dollar)] = TEMP_ICON % rep['F']

        else:
            forecast['HourlyObservation.IssuedAt'] = dv.get('dataDate').rstrip('Z')
            #assume observation
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

    elif data.get('RegionalFcst'):
        #Parse Regional Text Forecast
        rf = data['RegionalFcst']
        forecast['RegionalForecast.IssuedAt'] = rf['issuedAt'].rstrip('Z')
        for period in rf['FcstPeriods']['Period']:
            #have to check type because json can return list or dict here
            if isinstance(period['Paragraph'],list):
                for p, paragraph in enumerate(period['Paragraph']):
                    forecast['Regional.%s.Paragraph%s.Title' % (period.get('id'), p)] = paragraph['title'].rstrip(':').lstrip('UK Outlook for')
                    forecast['Regional.%s.Paragraph%s.Content' % (period.get('id'), p)] = paragraph['$']
            else:
                forecast['Regional.%s.Paragraph0.Title' % period.get('id')] = period['Paragraph']['title'].rstrip(':').lstrip('UK Outlook for')
                forecast['Regional.%s.Paragraph0.Content' % period.get('id')] = period['Paragraph']['$']
    return forecast

def empty_daily_forecast():
    """
    Sets default Window Property values to null.
    """
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
    """
    Sets 3hourly forecast Window Property values to null.
    """
    d = dict()
    for day in range (MAX_DAYS):
        for interval in range (MAX_INTERVALS):
            d['3hourly%s.FeelsTemp' % interval*day] = 'N/A'
            d['3hourly%s.WindGust' % interval*day] = 'N/A'
            d['3hourly%s.Humidity' % interval*day] = 'N/A'
            d['3hourly%s.Temp' % interval*day] = 'N/A'
            d['3hourly%s.Visibility' % interval*day] = 'N/A'
            d['3hourly%s.WindDirection' % interval*day] = 'N/A'
            d['3hourly%s.WindSpeed' % interval*day] = 'N/A'
            d['3hourly%s.MaxUV' % interval*day] = 'N/A'
            d['3hourly%s.OutlookIcon' % interval*day] = 'na.png'
            d['3hourly%s.Precipitation' % interval*day] = 'N/A'
    return d

#Not sure what the point is in setting empty values
#should be checked in skin surely.
def empty_regional_forecast():
    """
    Sets regional text forecast Window Property values to null.
    """
    d = dict()
    for period in range(6):
        d['Regional.Period%s.Title' % period] = ''
        d['Regional.Period%s.Content' % period] = ''
    return d

def empty_observation():
    """
    Sets "Current" observation Window Property values to null.
    """
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
    """
    Takes a list of strings and returns only
    those entries which contain a given string
    """
    filteredsitelist = list()
    for x in sitelist:
        if x['name'].lower().find(text.lower()) != -1:
            filteredsitelist.append(x)
    return filteredsitelist

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two coords
    using the haversine formula
    http://en.wikipedia.org/wiki/Haversine_formula
    """
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
    """
    A helper function to retry a url a number of times
    """
    while True:
        try:
            return urllib2.urlopen(url, timeout=1).read()
        except:
            if retry:
                retry -= 1
            else:
                raise

def dewpoint_temp(temp, humidity):
    """
    Approximate dewpoint using simple approximation
    http://en.wikipedia.org/wiki/Dew_point#Simple_approximation
    """
    return str(int(temp) - ((100 - int(humidity))/5))

def day_name(date):
    """
    Takes a date and returns the day of the week as a string
    """
    return datetime.fromtimestamp(time.mktime(time.strptime(date, '%Y-%m-%dZ'))).strftime('%a')

def minutes_as_time(minutes):
    """
    Takes an integer number of minutes and returns it
    as a time, starting at midnight.
    """
    return time.strftime('%H:%M', time.gmtime(minutes*60))

def verbose_timedelta(delta):
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    dstr = "%s day%s" % (delta.days, "s" if delta.days != 1 else "")
    hstr = "%s hour%s" % (hours, "s" if hours!=1 else "")
    mstr = "%s minute%s" % (minutes, "s" if minutes != 1 else "")
    sstr = "%s second%s" % (seconds, "s" if seconds != 1 else "")
    dhms = [dstr, hstr, mstr, sstr]
    for _ in range(2):
        for x, y in enumerate(dhms):
            if not y.startswith('0'):
                dhms = dhms[x:]
                break
        dhms.reverse()
    return ', '.join(dhms)