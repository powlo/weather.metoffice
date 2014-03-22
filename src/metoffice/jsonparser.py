import time
from datetime import timedelta
import utilities
import json
from operator import itemgetter

from constants import ISSUEDAT_FORMAT, DATAPOINT_DATETIME_FORMAT, SHORT_DAY_FORMAT, DATAPOINT_DATE_FORMAT,\
                        WEATHER_ICON_PATH, WEATHER_CODES, LONG_REGIONAL_NAMES, GEOIP_PROVIDER

def observation(filename):
    """
    Parse data to produce observation (current) data
    """
    data=json.load(open(filename))
    d = dict()
    dv = data['SiteRep']['DV']
    dataDate = dv.get('dataDate').rstrip('Z')
    d['HourlyObservation.IssuedAt'] = time.strftime(ISSUEDAT_FORMAT, time.strptime(dataDate, DATAPOINT_DATETIME_FORMAT))

    try:
        latest_period = dv['Location']['Period'][-1]
    except KeyError:
        latest_period = dv['Location']['Period']
    try:
        latest_obs = latest_period['Rep'][-1]
    except KeyError:
        latest_obs = latest_period['Rep']
    d['Current.Condition'] = WEATHER_CODES[latest_obs.get('W', 'na')][1]
    d['Current.Visibility'] = latest_obs.get('V', 'n/a')
    d['Current.Pressure'] = latest_obs.get('P', 'n/a')
    d['Current.Temperature'] = str(round(float(latest_obs.get('T', 'n/a')))).split('.')[0]
    d['Current.Wind'] = latest_obs.get('S', 'n/a')
    d['Current.WindDirection'] = latest_obs.get('D', 'n/a')
    d['Current.WindGust'] = latest_obs.get('G', 'n/a')
    d['Current.OutlookIcon'] = '%s.png' % WEATHER_CODES[latest_obs.get('W', 'na')][0]
    d['Current.FanartCode'] = '%s.png' % WEATHER_CODES[latest_obs.get('W','na')][0]
    return d

def daily(filename):
    """
    Parse data to produce daily forecast data
    """
    data=json.load(open(filename))
    d = dict()
    dv = data['SiteRep']['DV']
    dataDate = dv.get('dataDate').rstrip('Z')
    d['DailyForecast.IssuedAt'] = time.strftime(ISSUEDAT_FORMAT, time.strptime(dataDate, DATAPOINT_DATETIME_FORMAT))
    for p, period in enumerate(dv['Location']['Period']):
        d['Day%d.Title' %p] = time.strftime(SHORT_DAY_FORMAT, time.strptime(period.get('value'), DATAPOINT_DATE_FORMAT))
        for rep in period['Rep']:
            weather_type = rep.get('W', 'na')
            if rep.get('$') == 'Day':
                d['Day%d.HighTemp' %p] = rep.get('Dm', 'na')
                d['Day%d.Outlook' %p] = WEATHER_CODES.get(weather_type)[1]
                d['Day%d.OutlookIcon' % p] = WEATHER_ICON_PATH % WEATHER_CODES.get(weather_type, 'na')[0]
                d['Day%d.WindSpeed' % p] = rep.get('S', 'na')
                d['Day%d.WindDirection' % p] = rep.get('D', 'na').lower()
            elif rep.get('$') == 'Night':
                d['Day%d.LowTemp' %p] = rep.get('Nm', 'na')
    return d

def threehourly(filename):
    """
    Parse data to produce three hourly data
    """
    data=json.load(open(filename))
    d = dict()
    dv = data['SiteRep']['DV']
    dataDate = dv.get('dataDate').rstrip('Z')
    d['3HourlyForecast.IssuedAt'] = time.strftime(ISSUEDAT_FORMAT, time.strptime(dataDate, DATAPOINT_DATETIME_FORMAT))
    count = 0
    for period in dv['Location']['Period']:
        for rep in period['Rep']:
            #extra xbmc targeted info:
            weather_type = rep.get('W', 'na')
            d['3Hourly%d.Outlook' % count] = WEATHER_CODES.get(weather_type)[1]
            d['3Hourly%d.WindSpeed' % count] = rep.get('S', 'n/a')
            d['3Hourly%d.WindDirection' % count] = rep.get('D', 'na').lower()
            d['3Hourly%d.GustSpeed' % count] = rep.get('G', 'n/a')
            d['3Hourly%d.UVIndex' % count] = rep.get('U', 'n/a')
            d['3Hourly%d.Precipitation' % count] = rep.get('Pp')
            d['3Hourly%d.OutlookIcon' % count] = WEATHER_ICON_PATH % WEATHER_CODES.get(weather_type, 'na')[0]
            d['3Hourly%d.Day' % count] = time.strftime(SHORT_DAY_FORMAT, time.strptime(period.get('value'), DATAPOINT_DATE_FORMAT))
            d['3Hourly%d.Time' % count] = utilities.minutes_as_time(int(rep.get('$')))
            d['3Hourly%d.ActualTemp' % count] = rep.get('T', 'na')
            d['3Hourly%d.FeelsLikeTemp' % count] = rep.get('F', 'na')
            count +=1
    return d

def text(filename):
    """
    Parse data to produce text forecast data
    """
    data=json.load(open(filename))
    d = dict()
    rf = data['RegionalFcst']
    issuedat = rf['issuedAt'].rstrip('Z')
    d['TextForecast.IssuedAt'] = time.strftime(ISSUEDAT_FORMAT, time.strptime(issuedat, DATAPOINT_DATETIME_FORMAT))
    count = 0
    for period in rf['FcstPeriods']['Period']:
        #have to check type because json can return list or dict here
        if isinstance(period['Paragraph'],list):
            for paragraph in period['Paragraph']:
                d['Text.Paragraph%d.Title' % count] = paragraph['title'].rstrip(':').lstrip('UK Outlook for')
                d['Text.Paragraph%d.Content' % count] = paragraph['$']
                count+=1
        else:
            d['Text.Paragraph%d.Title' % count] = period['Paragraph']['title'].rstrip(':').lstrip('UK Outlook for')
            d['Text.Paragraph%d.Content' % count] = period['Paragraph']['$']
            count+=1
    return d

def sitelist(filename):
    data = json.load(open(filename))
    sitelist = data['Locations']['Location']
    for site in sitelist:
        #fix datapoint bug where keys start with @. Usually in Regional Sitelist
        for key in site:
            if key.startswith('@'):
                site[key[1:]] = site.pop(key)
        #Change regional names to long versions. Untouched otherwise.
        site['name'] = LONG_REGIONAL_NAMES.get(site['name'], site['name'])
    return sitelist

def layercapabilities(filename, selection):
    d = {}
    #pull parameters out of capabilities file - consider using jsonpath here
    data = json.load(open(filename))
    d['BaseUrl'] = data['Layers']['BaseUrl']['$']
    for thislayer in data['Layers']['Layer']:
        if thislayer['@displayName'] == selection:
            d['layer_name'] = thislayer['Service']['LayerName']
            d['image_format'] = thislayer['Service']['ImageFormat']
            d['default_time'] = thislayer['Service']['Timesteps']['@defaultTime']
            d['timesteps'] = thislayer['Service']['Timesteps']['Timestep']
            return d
    else:
        raise Exception("Couldn't find layer '%s'" % selection)

def geoip(filename):
    data = json.load(open(filename))
    return (float(data[GEOIP_PROVIDER['latitude']]), float(data[GEOIP_PROVIDER['longitude']]))

def daily_expiry(filename):
    data = json.load(open(filename))
    dataDate = data['SiteRep']['DV']['dataDate'].rstrip('Z')
    return utilities.strptime(dataDate, DATAPOINT_DATETIME_FORMAT) + timedelta(hours=1.5)

def threehourly_expiry(filename):
    data = json.load(open(filename))
    dataDate = data['SiteRep']['DV']['dataDate'].rstrip('Z')
    return utilities.strptime(dataDate, DATAPOINT_DATETIME_FORMAT) + timedelta(hours=1.5)

def text_expiry(filename):
    data = json.load(open(filename))
    issuedAt = data['RegionalFcst']['issuedAt'].rstrip('Z')
    return utilities.strptime(issuedAt, DATAPOINT_DATETIME_FORMAT) + timedelta(hours=12)

def observation_expiry(filename):
    data = json.load(open(filename))
    dataDate = data['SiteRep']['DV']['dataDate'].rstrip('Z')
    return utilities.strptime(dataDate, DATAPOINT_DATETIME_FORMAT) + timedelta(hours=1.5)

def layer_capabilities_expiry(filename):
    data = json.load(open(filename))
    defaultTime = data['Layers']['Layer'][0]['Service']['Timesteps']['@defaultTime']
    return utilities.strptime(defaultTime, DATAPOINT_DATETIME_FORMAT) + timedelta(hours=9)
