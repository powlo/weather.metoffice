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
    if DEBUG:
        if isinstance (txt,str):
            txt = txt.decode("utf-8")
        message = u'%s: %s' % (__addonid__, txt)
        xbmc.log(msg=message.encode("utf-8"), level=xbmc.LOGDEBUG)

def set_empty_forecast():
    log("Setting empty forecast...")
    clear = utilities.empty_forecast()
    for field, value in clear.iteritems():
        WEATHER_WINDOW.setProperty(field, value)
    
def set_empty_observation():
    log("Setting empty observation...")
    clear = utilities.empty_observation()
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
    #todo: can remove this and just let the url request fail when location is null
    location_name = __addon__.getSetting('ForecastLocation')
    location_id = __addon__.getSetting('ForecastLocationID')
    if not (location_id and location_name):
        log("Forecast location is not set")
        set_empty_forecast()
        return
        #sys.exit(1)

    #Get five day forecast:
    #todo: be more specific with the exception
    try:
        log("Fetching forecast for '%s (%s)' from the Met Office..." % (location_name, location_id))
        params = {'key':API_KEY, 'res':'daily'}
        data = json.loads(datapointapi.request(resource='wxfcs', object=location_id, params=params).decode('latin-1'))
        report = utilities.parse_json_daily_forecast(data)
        log("Setting Window properties...")
        for day, forecast in report.iteritems():
            for field, value in forecast.iteritems():
                WEATHER_WINDOW.setProperty('%s.%s' % (day, field), value)
    except:
        set_empty_forecast()
    WEATHER_WINDOW.setProperty('Forecast.IsFetched', 'true')

def set_observation():
    location_name = __addon__.getSetting('ObservationLocation')
    location_id = __addon__.getSetting('ObservationLocationID')
    if not (location_id and location_name):
        log("Observation location is not set")
        set_empty_observation()
        return

    try:
        log("Fetching forecast for '%s (%s)' from the Met Office..." % (location_name, location_id))
        params = {'key':API_KEY, 'res':'hourly'}
        data = json.loads(datapointapi.request(object=location_id, params=params).decode('latin-1'))
        log("Setting Window properties...")
        report = utilities.parse_json_observation(data)
        for field, value in report.iteritems():
            WEATHER_WINDOW.setProperty(field, value)
    except:
        set_empty_observation()
    WEATHER_WINDOW.setProperty('Current.IsFetched', 'true')

    #Get observations:
    #data = weather.get_observations(OBSERVATION_ID)
    #observation = utilities.parse_json_observations(data)
    #for field, value in observation.iteritems():
    #    WEATHER_WINDOW.setProperty(field, value)
    #what does setting "isfetched" achieve?
    #WEATHER_WINDOW.setProperty('Location%s' % num, location_name)
    #'Forecast.IsFetched' and 'Current.IsFetched' seem to have no effect

def get_keyboard_text():
    """
    Gets keyboard text from XBMC
    """
    keyboard = xbmc.Keyboard()
    keyboard.doModal()
    return keyboard.isConfirmed() and keyboard.getText()

def get_coords_from_ip():  
    provider = int(__addon__.getSetting('GeoIPProvider'))
    page = utilities.retryurlopen(utilities.GEOIP_PROVIDERS[provider]['url'])
    data = json.loads(page)
    latitude = utilities.GEOIP_PROVIDERS[provider]['latitude']
    longitude = utilities.GEOIP_PROVIDERS[provider]['longitude']
    return (float(data[latitude]), float(data[longitude]))

def get_sitelist(location):
    
    log("Fetching %s site list..." % location)
    if location == 'ForecastLocation':
        resource = 'wxfcs'
    else:
        resource = 'wxobs'
    params = {'key': API_KEY}
    xbmc.executebuiltin( "ActivateWindow(busydialog)" )
    try:
        page=datapointapi.request(resource=resource, params=params).decode('latin-1')
    except (HTTPError, URLError) as e:
        xbmc.executebuiltin( "Dialog.Close(busydialog)" )
        log("Is your API Key correct?")
        log(str(e))
        sys.exit(1)
    try:
        data = json.loads(page)
    except ValueError as e:
        xbmc.executebuiltin( "Dialog.Close(busydialog)" )
        log("There was a problem with the json data.")
        log(str(e))
        log(data)
        sys.exit(1)
        
    xbmc.executebuiltin( "Dialog.Close(busydialog)" )
    sitelist = data['Locations']['Location']
    if __addon__.getSetting('GeoLocation') == 'true':
        try:
            (latitude, longitude) = get_coords_from_ip()
        except TypeError:
            #TypeError occurs when lat or long are null and cant be converted to float
            return sitelist
        for site in sitelist:
            site['distance'] = int(utilities.haversine_distance(latitude, longitude, float(site['latitude']), float(site['longitude'])))
    return sitelist

def auto_location(location):
    log("Auto-assigning '%s'..." % location)
    sitelist = get_sitelist(location)
    try:
        sitelist.sort(key=itemgetter('distance'))
    except KeyError:
        #if geoip service can't add distance then we can't autolocate
        log("Can't autolocate. Returned sitelist doesn't have 'distance' key.")
        return
    first = sitelist[0]
    __addon__.setSetting(location, first['name'])
    __addon__.setSetting('%sID' % location, first['id'])

    log("Location set to '%s'" % first['name'])

def set_location(location):
    """
    Sets the forecast location by providing a keyboard prompt
    to the user. The name entered by the user is searched in
    site list. All matches are presented as a select list to
    the user. On successful selection internal addon setting
    is set.
    :returns: None
    """  
    assert(location in datapointapi.SITELIST_TYPES)
    log("Setting '%s' ..." % location)
    text = get_keyboard_text()
    dialog = xbmcgui.Dialog()
    sitelist = get_sitelist(location)
    filtered_sites = utilities.filter_sitelist(text, sitelist)
    if filtered_sites != []:
        try:
            filtered_sites = sorted(filtered_sites,key=itemgetter('distance'))
            display_list = ["%s (%skm)" % (x['name'], x['distance']) for x in filtered_sites]
        except KeyError:
            filtered_sites = sorted(filtered_sites,key=itemgetter('name'))
            display_list = [x['name'] for x in filtered_sites]
            
        selected = dialog.select("Matching Sites", display_list)
        if selected != -1:
            __addon__.setSetting(location, filtered_sites[selected]['name'])
            __addon__.setSetting("%sID" % location, filtered_sites[selected]['id'])
    else:
        dialog.ok("No Matches", "No locations found containing '%s'" % text)
        log("No locations found containing '%s'" % text)

#MAIN CODE
WEATHER_WINDOW_ID = 12600
WEATHER_WINDOW = xbmcgui.Window(WEATHER_WINDOW_ID)

DEBUG = True if __addon__.getSetting('Debug') == 'true' else False
API_KEY = __addon__.getSetting('ApiKey')
AUTOLOCATION = True if __addon__.getSetting('AutoLocation') == 'true' else False
FORCEAUTOLOCATION = True if __addon__.getSetting('ForceAutoLocation') == 'true' else False

log('Startup...')
WEATHER_WINDOW.setProperty('WeatherProvider', __addonname__)

if not API_KEY:
    dialog = xbmcgui.Dialog()
    dialog.ok('No API Key', 'Enter your Met Office API Key under weather settings.')
    log('Error, No API Key')
    sys.exit(1)

if sys.argv[1] == ('SetLocation'):
    set_location(sys.argv[2])
else:
    if FORCEAUTOLOCATION or (AUTOLOCATION and not __addon__.getSetting('ForecastLocation')):
        auto_location('ForecastLocation')
    if FORCEAUTOLOCATION or (AUTOLOCATION and not __addon__.getSetting('ObservationLocation')):
        auto_location('ObservationLocation')
    set_forecast()
    set_observation()

WEATHER_WINDOW.setProperty('Location1', __addon__.getSetting('ForecastLocation'))
WEATHER_WINDOW.setProperty('Locations', '1')

log('Done!')
