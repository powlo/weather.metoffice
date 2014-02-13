
from datetime import datetime
import json
import os
import time
import urllib2
import xbmc
import xbmcaddon

DATAPOINT_FORMAT = '%Y-%m-%dT%H:%M:%S'
MAPTIME_FORMAT = '%H%M %a'
ISSUEDAT_FORMAT = '%H:%M %a %d %b %Y'

__addon__       = xbmcaddon.Addon(id="weather.metoffice")
__addonid__     = __addon__.getAddonInfo('id')

ADDON_DATA_PATH = xbmc.translatePath('special://profile/addon_data/%s/' % __addon__.getAddonInfo('id'))
CACHE_FOLDER = os.path.join(ADDON_DATA_PATH, 'cache')
CACHE_FILE = os.path.join(ADDON_DATA_PATH, 'cache.json')

def log(msg, level=xbmc.LOGNOTICE):
    xbmc.log("%s: %s" %(__addonid__, msg), level)

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