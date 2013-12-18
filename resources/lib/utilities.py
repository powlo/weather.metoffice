from datetime import datetime
import json
import math
import os
import time
import urllib2
import xbmc
import xbmcaddon

#This list must appear in the same order as it appears in 
#the settings.xml in order for the indexes to align.
GEOIP_PROVIDERS = [{'url':'http://ip-api.com/json/', 'latitude':'lat', 'longitude':'lon'},
             {'url':'http://freegeoip.net/json/', 'latitude':'latitude', 'longitude':'longitude'},
             {'url':'http://www.telize.com/geoip/','latitude':'latitude', 'longitude':'longitude'},
             {'url':'http://api.hostip.info/get_json.php?position=true','latitude':'lat', 'longitude':'lng'},
             {'url':'http://geoiplookup.net/geoapi.php?output=json', 'latitude':'latitude', 'longitude':'longitude'}
                   ]

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