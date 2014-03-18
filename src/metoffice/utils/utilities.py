from functools import wraps
from datetime import datetime
import time
import traceback
import xbmc #@UnresolvedImport
import xbmcgui #@UnresolvedImport
import xbmcaddon #@UnresolvedImport

WINDOW_WEATHER = 12600
WINDOW_SETTINGS_MYWEATHER = 10014
WEATHER_WINDOW = xbmcgui.Window(WINDOW_WEATHER)

DATAPOINT_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'
DATAPOINT_DATE_FORMAT = '%Y-%m-%dZ'
SHORT_DAY_FORMAT = "%a"
MAPTIME_FORMAT = '%H%M %a'
ISSUEDAT_FORMAT = '%H:%M %a %d %b %Y'

__addon__       = xbmcaddon.Addon(id="weather.metoffice")
__addonid__     = __addon__.getAddonInfo('id')

ADDON_DATA_PATH = xbmc.translatePath('special://profile/addon_data/%s/' % __addon__.getAddonInfo('id'))

LOGPREFIX = "weather.metoffice: "

POPUP = xbmcgui.Dialog()

#by importing utilities all messages in xbmc log will be prepended with LOGPREFIX
def log(msg, level=xbmc.LOGNOTICE):
    xbmc.log('weather.metoffice: {0}'.format(msg), level)

#python datetime.strptime is not thread safe: sometimes causes 'NoneType is not callable' error
def strptime(dt, fmt):
    return datetime.fromtimestamp(time.mktime(time.strptime(dt, fmt)))

def failgracefully(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        try:
            return f(*args, **kwds)
        except Exception as e:
            log(traceback.format_exc(), xbmc.LOGSEVERE)
            if xbmcgui.getCurrentWindowId() == WINDOW_WEATHER or xbmcgui.getCurrentWindowId() == WINDOW_SETTINGS_MYWEATHER:
                POPUP.ok("An Error Occurred", "Check log file for details.", str(type(e)), str(e))
    return wrapper

def xbmcbusy(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        if xbmcgui.getCurrentWindowId() == WINDOW_WEATHER or xbmcgui.getCurrentWindowId() == WINDOW_SETTINGS_MYWEATHER:
            xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        try:
            return f(*args, **kwds)
        finally:
            xbmc.executebuiltin( "Dialog.Close(busydialog)" )
    return wrapper

def panelbusy(pane):
    def decorate(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            WEATHER_WINDOW.setProperty('{0}.IsBusy'.format(pane), 'true')
            try:
                return f(*args, **kwargs)
            finally:
                WEATHER_WINDOW.clearProperty('{0}.IsBusy'.format(pane))
        return wrapper
    return decorate

def minutes_as_time(minutes):
    """
    Takes an integer number of minutes and returns it
    as a time, starting at midnight.
    """
    return time.strftime('%H:%M', time.gmtime(minutes*60))
