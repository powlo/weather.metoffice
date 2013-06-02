import xbmc
import xbmcgui
import xbmcaddon
import os
from datetime import datetime
import time
import sys
from urllib2 import HTTPError

### addon info
__addon__       = xbmcaddon.Addon()
__addonid__     = __addon__.getAddonInfo('id')
__addonname__   = __addon__.getAddonInfo('name')
__author__      = __addon__.getAddonInfo('author')
__version__     = __addon__.getAddonInfo('version')
__addonpath__   = __addon__.getAddonInfo('path')
__resource__    = os.path.join( __addonpath__, 'resources', 'lib' )

sys.path.append(__resource__)

#We can now import from local lib dir
#Need to think about whether this fudging is a good thing
import utilities
from datapointapi import Datapoint

def log(txt):
    """
    Enters a message into xbmc's log file
    :param txt: Message to be logged. Eg, 'Downloading data'
    :type txt: str
    """
    if DEBUG == 'true':
        if isinstance (txt,str):
            txt = txt.decode("utf-8")
        message = u'%s: %s' % (__addonid__, txt)
        xbmc.log(msg=message.encode("utf-8"), level=xbmc.LOGDEBUG)

def set_locations():
    """
    Sets Window properties 'Location<n>' and 'Locations'
    based on addon settings.
    """
    locations = 0
    for count in range(1, LOCATIONS_MAX+1):
        loc_name = __addon__.getSetting('Location%s' % count)
        if loc_name != '':
            locations += 1
        else:
            __addon__.setSetting('Location%sid' % count, '')
        WEATHER_WINDOW.setProperty('Location%s' % count, loc_name)
    WEATHER_WINDOW.setProperty('Locations', str(locations))
    log('available locations: %s' % str(locations))

def set_forecast(num):
    """
    Sets forecast related Window properties for the given location
    by making Datapoint API queries for the location id
    that corresponds to the location number. If the forecast
    can't be fetched then empty data is assigned.
    :param num: Location number who's forecast will be fetched, eg '1'
    :type num: str
    :returns: None
    """
    while True:
        if num:
            location_name = __addon__.getSetting('Location%s' % num)
            location_id = __addon__.getSetting('Location%sid' % num)
        else:
            dialog = xbmcgui.Dialog()
            dialog.ok('No Locations Set', 'Set locations under weather settings.')
        if (location_id and location_name):
            break
        else:
            log("Location '%s' not set..." % (num))
            log("Trying next location down...")
            num = str(int(num)-1)
    #Get five day forecast:
    datapoint = Datapoint(API_KEY)
    try:
        log("Fetching forecast for Location%s '%s (%s)' from the Met Office..." % (num, location_name, location_id))
        data = datapoint.get_json_forecast(location_id)
        report = utilities.parse_json_day_forecast(data)

        log("Setting Window properties...")
        for day, forecast in report.iteritems():
            for field, value in forecast.iteritems():
                WEATHER_WINDOW.setProperty('%s.%s' % (day, field), value)

        #get current forecast based on the same data
        report = utilities.parse_json_current_forecast(data)
        for field, value in report.iteritems():
            WEATHER_WINDOW.setProperty(field, value)

    except:
        log("Setting empty forecast...")
        clear = utilities.clear()
        for field, value in clear.iteritems():
            WEATHER_WINDOW.setProperty(field, value)
    #Get observations:
    #data = weather.get_json_observations(OBSERVATION_ID)
    #observation = utilities.parse_json_observations(data)
    #for field, value in observation.iteritems():
    #    WEATHER_WINDOW.setProperty(field, value)
    #what does setting "isfetched" achieve?
    #WEATHER_WINDOW.setProperty('Location%s' % num, location_name)
    #'Forecast.IsFetched' and 'Current.IsFetched' seem to have no effect
    WEATHER_WINDOW.setProperty('Forecast.IsFetched', 'true')
    WEATHER_WINDOW.setProperty('Current.IsFetched', 'true')
    
def set_location(location):
    """
    Sets a location by providing a keyboard prompt to the user.
    The name entered by the user is searched in the Met Office
    site list. All matches are presented as a select list to
    the user. On successful selection internal addon setting
    is set and the Window property is set.
    :param location: The location to be targeted. Eg, 'Location1'
    :type location: string
    :returns: None
    """
    log("Setting '%s'..." % location)
    datapoint = Datapoint(API_KEY)
    dialog = xbmcgui.Dialog()
    keyboard = xbmc.Keyboard()
    keyboard.doModal()
    if (keyboard.isConfirmed() and keyboard.getText() != ''):
        text = keyboard.getText()
        xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        try:
            log("Fetching site list...")
            sitelist = datapoint.get_json_forecast_sitelist()
        except HTTPError as e:
            dialog.ok(str(e), "Is your API Key correct?")
            log(str(e))
            sys.exit(1)
        finally:
            xbmc.executebuiltin( "Dialog.Close(busydialog)" )

        locations, ids = utilities.match_name(text, sitelist)
        if locations != []:
            selected = dialog.select("Matching Locations", locations)
            if selected != -1:
                __addon__.setSetting(location, locations[selected])
                __addon__.setSetting(location + 'id', ids[selected])
        else:
            dialog.ok("No Matches", "No locations found containing '%s'" % text)
            log("No locations found containing '%s'" % text)
    else:
        locations = int(WEATHER_WINDOW.getProperty('Locations'))
        position = int(location.lstrip('Location'))
        if position <= locations:
            log("Clearing '%s'..." % location)
            for x in range(position,locations):
                __addon__.setSetting('Location%s' % str(x), __addon__.getSetting('Location%s' % str(x+1)))
                __addon__.setSetting('Location%sid' % str(x), __addon__.getSetting('Location%sid' % str(x+1)))
            __addon__.setSetting('Location%s' % str(locations), '')
            __addon__.setSetting('Location%sid' % str(locations), '')

#MAIN CODE
LOCATIONS_MAX = 3
WEATHER_WINDOW_ID = 12600
WEATHER_WINDOW = xbmcgui.Window(WEATHER_WINDOW_ID)
DEBUG = __addon__.getSetting('Debug')
API_KEY = __addon__.getSetting('ApiKey')

log('Startup...')
WEATHER_WINDOW.setProperty('WeatherProvider', __addonname__)

if not API_KEY:
    dialog = xbmcgui.Dialog()
    dialog.ok('No API Key', 'Enter your Met Office API Key under weather settings.')
    log('Error, No API Key')
    sys.exit(1)

set_locations()
if sys.argv[1].startswith('Location'):
    set_location(sys.argv[1])
else:
    set_forecast(sys.argv[1])
log('Done!')
