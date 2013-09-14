import xbmc
import xbmcgui
import xbmcaddon
import os
import time
import sys
import json
from datetime import datetime
from urllib2 import HTTPError, URLError
from operator import itemgetter

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
import datapointapi

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

def set_empty_forecast():
    log("Setting empty forecast...")
    clear = utilities.clear()
    for field, value in clear.iteritems():
        WEATHER_WINDOW.setProperty(field, value)

def set_forecast():
    """
    Sets forecast related Window properties for the given location
    by making Datapoint API queries for the location id
    that corresponds to the location number. If the forecast
    can't be fetched then empty data is assigned.
    :param num: Location number who's forecast will be fetched, eg '1'
    :type num: str
    :returns: None
    """
    location_name = __addon__.getSetting('ForecastLocation')
    location_id = __addon__.getSetting('ForecastLocationID')
    if not (location_id and location_name):
        log("Forecast location is not set")
        set_empty_forecast()
        sys.exit(1)

    #Get five day forecast:
    #todo: be more specific with the exception
    try:
        log("Fetching forecast for '%s (%s)' from the Met Office..." % (location_name, location_id))
        params = {'key':API_KEY, 'res':'daily'}
        data = json.loads(datapointapi.request(resource='wxfcs', object=location_id, params=params).decode('latin-1'))
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
        set_empty_forecast()
        log("Setting empty forecast...")

    #Get observations:
    #data = weather.get_observations(OBSERVATION_ID)
    #observation = utilities.parse_json_observations(data)
    #for field, value in observation.iteritems():
    #    WEATHER_WINDOW.setProperty(field, value)
    #what does setting "isfetched" achieve?
    #WEATHER_WINDOW.setProperty('Location%s' % num, location_name)
    #'Forecast.IsFetched' and 'Current.IsFetched' seem to have no effect
    WEATHER_WINDOW.setProperty('Forecast.IsFetched', 'true')
    WEATHER_WINDOW.setProperty('Current.IsFetched', 'true')

def get_keyboard_text():
    """
    Gets keyboard text from XBMC
    """
    keyboard = xbmc.Keyboard()
    keyboard.doModal()
    return keyboard.isConfirmed() and keyboard.getText()

def get_coords_from_ip():
    data = json.loads(utilities.get_freegeoipnet())
    return (float(data['latitude']), float(data['longitude']))

def get_sitelist(category):
    
    log("Fetching %s site list..." % category)
    if category == 'Forecast':
        resource = 'wxfcs'
    else:
        resource = 'wxobs'
    params = {'key': API_KEY}
    xbmc.executebuiltin( "ActivateWindow(busydialog)" )
    try:
        data = json.loads(datapointapi.request(resource=resource, params=params).decode('latin-1'))
    except (HTTPError, URLError) as e:
        xbmc.executebuiltin( "Dialog.Close(busydialog)" )
        dialog = xbmcgui.Dialog()
        dialog.ok(str(e.reason), "Is your API Key correct?")
        log(str(e))
        sys.exit(1)
    xbmc.executebuiltin( "Dialog.Close(busydialog)" )
    sitelist = data['Locations']['Location']
    (latitude, longitude) = get_coords_from_ip()
    for site in sitelist:
        site['distance'] = int(utilities.haversine_distance(latitude, longitude, float(site['latitude']), float(site['longitude'])))
    return sitelist

def auto_location():
    #if auto location is on and if each info region is enabled
    #then get an auto location for that category
    log("Auto-assigning forecast location...")
    sitelist = get_sitelist('Forecast')
    sitelist.sort(key=itemgetter('distance'))
    first = sitelist[0]
    __addon__.setSetting('ForecastLocation', first['name'])
    __addon__.setSetting('ForecastLocationID', first['id'])

    log("Location set to '%s'" % first['name'])

def set_location(category):
    """
    Sets the forecast location by providing a keyboard prompt
    to the user. The name entered by the user is searched in
    site list. All matches are presented as a select list to
    the user. On successful selection internal addon setting
    is set.
    :returns: None
    """
    assert(category in datapointapi.SITELIST_TYPES)
    log("Setting %s location..." % category)
    text = get_keyboard_text()
    dialog = xbmcgui.Dialog()
    sitelist = get_sitelist(category)
    filtered_sites = utilities.filter_sitelist(text, sitelist)
    if filtered_sites != []:
        filtered_sites = sorted(filtered_sites,key=itemgetter('distance'))
        names = [x['name'] for x in filtered_sites]
        names_distances = ["%s (%skm)" % (x['name'], x['distance']) for x in filtered_sites]
        ids = [x['id'] for x in filtered_sites]
        selected = dialog.select("Matching Sites", names_distances)
        if selected != -1:
            __addon__.setSetting('%sLocation' % category, names[selected])
            __addon__.setSetting('%sLocationID' % category, ids[selected])
    else:
        dialog.ok("No Matches", "No locations found containing '%s'" % text)
        log("No locations found containing '%s'" % text)

#MAIN CODE
WEATHER_WINDOW_ID = 12600
WEATHER_WINDOW = xbmcgui.Window(WEATHER_WINDOW_ID)

DEBUG = __addon__.getSetting('Debug')
API_KEY = __addon__.getSetting('ApiKey')
AUTOLOCATION = __addon__.getSetting('AutoLocation')

log('Startup...')
WEATHER_WINDOW.setProperty('WeatherProvider', __addonname__)

if not API_KEY:
    dialog = xbmcgui.Dialog()
    dialog.ok('No API Key', 'Enter your Met Office API Key under weather settings.')
    log('Error, No API Key')
    sys.exit(1)

if AUTOLOCATION and not __addon__.getSetting('ForecastLocation'):
    auto_location()

if sys.argv[1] == ('SetLocation'):
    set_location(sys.argv[2])
else:
    set_forecast()

WEATHER_WINDOW.setProperty('Location1', __addon__.getSetting('ForecastLocation'))
WEATHER_WINDOW.setProperty('Locations', '1')

log('Done!')
