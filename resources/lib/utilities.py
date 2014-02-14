from functools import wraps
from datetime import datetime
import os
import time
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

def xbmcbusy(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        try:
            return f(*args, **kwds)
        finally:
            xbmc.executebuiltin( "Dialog.Close(busydialog)" )
    return wrapper

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
