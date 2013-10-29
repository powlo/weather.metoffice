import xbmc
import xbmcgui
import xbmcaddon
import os
import time
import sys
import json
from datetime import datetime, timedelta
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

TIMESTAMP_FORMAT = '%d/%m/%y %H:%M:%S'
REGIONAL_FORECAST_INTERVAL = timedelta(hours=1)

def set_empty_daily_forecast():
    utilities.log(__addonid__, "Setting empty daily forecast...", DEBUG)
    clear = utilities.empty_daily_forecast()
    for field, value in clear.iteritems():
        WEATHER_WINDOW.setProperty(field, value)

def set_empty_3hourly_forecast():
    utilities.log(__addonid__, "Setting empty 3 hourly forecast...", DEBUG)
    clear = utilities.empty_3hourly_forecast()
    for field, value in clear.iteritems():
        WEATHER_WINDOW.setProperty(field, value)

def set_empty_regional_forecast():
    utilities.log(__addonid__, "Setting empty regional forecast...", DEBUG)
    clear = utilities.empty_3hourly_forecast()
    for field, value in clear.iteritems():
        WEATHER_WINDOW.setProperty(field, value)
    
def set_empty_observation():
    utilities.log(__addonid__, "Setting empty observation...", DEBUG)
    clear = utilities.empty_observation()
    for field, value in clear.iteritems():
        WEATHER_WINDOW.setProperty(field, value)

def set_daily_forecast():
    """
    Sets daily forecast related Window properties
    If the forecast can't be fetched then empty data is assigned.
    :returns: None
    """
    #todo: can remove this and just let the url request fail when location is null
    location_name = __addon__.getSetting('ForecastLocation')
    location_id = __addon__.getSetting('ForecastLocationID')
    if not (location_id and location_name):
        utilities.log(__addonid__, "Forecast location is not set", DEBUG)
        set_empty_daily_forecast()
        return
        #sys.exit(1)

    #Get five day forecast:
    #todo: be more specific with the exception
    utilities.log(__addonid__, "Fetching forecast for '%s (%s)' from the Met Office..." % (location_name, location_id), DEBUG)
    params = {'key':API_KEY, 'res':'daily'}
    url = datapointapi.url(resource='wxfcs', object=location_id, params=params)
    try:
        page = utilities.retryurlopen(url).decode('latin-1')
        data = json.loads(page)
        report = utilities.parse_json_report(data)
        utilities.log(__addonid__, "Setting Window properties...", DEBUG)
        for field, value in report.iteritems():
            WEATHER_WINDOW.setProperty(field, value)
    except:
        set_empty_daily_forecast()
    WEATHER_WINDOW.setProperty('Forecast.IsFetched', 'true')

def set_3hourly_forecast():
    """
    Sets forecast related Window properties for the given location
    by making Datapoint API queries for the location id
    that corresponds to the location number. If the forecast
    can't be fetched then empty data is assigned.
    :returns: None
    """
    #todo: can remove this and just let the url request fail when location is null
    location_name = __addon__.getSetting('ForecastLocation')
    location_id = __addon__.getSetting('ForecastLocationID')
    if not (location_id and location_name):
        utilities.log(__addonid__, "Forecast location is not set", DEBUG)
        set_empty_3hourly_forecast()
        return

    #Get three hour forecast:
    utilities.log(__addonid__, "Fetching 3 hourly forecast for '%s (%s)' from the Met Office..." % (location_name, location_id), DEBUG)
    params = {'key':API_KEY, 'res':'3hourly'}
    url = datapointapi.url(resource='wxfcs', object=location_id, params=params)
    try:
        page = utilities.retryurlopen(url).decode('latin-1')
        data = json.loads(page)
        report = utilities.parse_json_report(data)
        utilities.log(__addonid__, "Setting Window properties...", DEBUG)
        for field, value in report.iteritems():
            WEATHER_WINDOW.setProperty(field, value)
    except Exception as e:
        set_empty_3hourly_forecast()
    WEATHER_WINDOW.setProperty('3Hour.IsFetched', 'true')

def set_properties(panel):
    #Look at the time the last regional forecast was fetched
    #and if fetched over a given period ago then refetch.
    config = {
        'RegionalForecast' : {
            'name' : 'Regional Forecast',
            'interval' : timedelta(hours=1),
            'location_name' : 'RegionalLocation',
            'location_id' : 'RegionalLocationID',
            'format' : 'txt',
            'resource' : 'wxfcs',
            'group' : 'regionalforecast'}
    }
    panel_config = config.get(panel)
    if WEATHER_WINDOW.getProperty('%s.TimeStamp' % panel):
        timestamp_string = WEATHER_WINDOW.getProperty('%s.TimeStamp' % panel)
        timestamp = datetime.fromtimestamp(time.mktime(time.strptime(timestamp_string, TIMESTAMP_FORMAT)))
        interval = datetime.now() - timestamp
        if interval < panel_config['interval']:
            utilities.log(__addonid__, "Last update was %d minutes ago. No need to fetch data." % (interval.seconds/60), DEBUG)
            return
    
    panel_name = panel_config.get('name')
    location_name = __addon__.getSetting(panel_config.get('location_name'))
    location_id = __addon__.getSetting(panel_config.get('location_id'))
    if not (location_id and location_name):
        utilities.log(__addonid__, "%s location is not set" % panel_config.get('name'), DEBUG)
        #set_empty_regional_forecast()
        return
    #Fetch data from Met Office:
    utilities.log(__addonid__, "Fetching %s for '%s (%s)' from the Met Office..." % (panel_name, location_name, location_id), DEBUG)
    params = {'key':API_KEY}
    format = panel_config.get('format')
    resource = panel_config.get('resource')
    group = panel_config.get('group')
    url = datapointapi.url(format=format, resource=resource, group=group, object=location_id, params=params)
    try:
        page = utilities.retryurlopen(url).decode('latin-1')
        data = json.loads(page)
        report = utilities.parse_json_report(data)
        utilities.log(__addonid__, "Setting Window properties...", DEBUG)
        for field, value in report.iteritems():
            WEATHER_WINDOW.setProperty(field, value)
    except:
        pass
        #set_empty_regional_forecast()
    WEATHER_WINDOW.setProperty('%s.TimeStamp' % panel, datetime.now().strftime(TIMESTAMP_FORMAT))

def set_observation():
    location_name = __addon__.getSetting('ObservationLocation')
    location_id = __addon__.getSetting('ObservationLocationID')
    if not (location_id and location_name):
        utilities.log(__addonid__, "Observation location is not set", DEBUG)
        set_empty_observation()
        return

    utilities.log(__addonid__, "Fetching forecast for '%s (%s)' from the Met Office..." % (location_name, location_id), DEBUG)
    params = {'key':API_KEY, 'res':'hourly'}
    url = datapointapi.url(object=location_id, params=params)
    try:
        page = utilities.retryurlopen(url).decode('latin-1')
        data = json.loads(page)
        utilities.log(__addonid__, "Setting Window properties...", DEBUG)
        report = utilities.parse_json_report(data)
        for field, value in report.iteritems():
            if value:
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

def get_sitelist(location):
    url_params = {
        'ForecastLocation' : {'resource' : 'wxfcs'},
        'ObservationLocation' : {'resource' : 'wxobs'},
        'RegionalLocation' : {'resource' : 'wxfcs', 'format': 'txt', 'group' : 'regionalforecast'},
        }
    args = url_params[location]
    args.update({'params':{'key': API_KEY}})
    xbmc.executebuiltin( "ActivateWindow(busydialog)" )
    url = datapointapi.url(**args)
    try:
        page = utilities.retryurlopen(url).decode('latin-1')
    except (HTTPError, URLError) as e:
        xbmc.executebuiltin( "Dialog.Close(busydialog)" )
        utilities.log(__addonid__, "Is your API Key correct?", DEBUG)
        utilities.log(__addonid__, str(e), DEBUG)
        sys.exit(1)
    try:
        data = json.loads(page)
    except ValueError as e:
        xbmc.executebuiltin( "Dialog.Close(busydialog)" )
        utilities.log(__addonid__, "There was a problem with the json data.", DEBUG)
        utilities.log(__addonid__, str(e), DEBUG)
        utilities.log(__addonid__, data, DEBUG)
        sys.exit(1)
        
    xbmc.executebuiltin( "Dialog.Close(busydialog)" )
    sitelist = data['Locations']['Location']
    try:
        if __addon__.getSetting('GeoLocation') == 'true':
            provider = int(__addon__.getSetting('GeoIPProvider'))
            url = utilities.GEOIP_PROVIDERS[provider]['url']
            page = utilities.retryurlopen(url)
            try:
                geoip = json.loads(page)
            except ValueError:
            #ValueError occurs when json attempts to read empty page eg if geoip provider closes
                utilities.log(__addonid__, "Couldn't parse json data from %s" % url, DEBUG)
            latitude = utilities.GEOIP_PROVIDERS[provider]['latitude']
            longitude = utilities.GEOIP_PROVIDERS[provider]['longitude']
            try:
                (latitude, longitude) = (float(geoip[latitude]), float(geoip[longitude]))
            except TypeError:
                utilities.log(__addonid__, "Couldn't get lat,long data from %s" % url, DEBUG)
            for site in sitelist:
                try:
                    site['distance'] = int(utilities.haversine_distance(latitude, longitude, float(site['latitude']), float(site['longitude'])))
                except KeyError:
                    utilities.log(__addonid__, "Site '%s' does not have latitude, longitude info" % site['name'], DEBUG)
    finally:
        return sitelist

def auto_location(location):
    utilities.log(__addonid__, "Auto-assigning '%s'..." % location, DEBUG)
    sitelist = get_sitelist(location)
    try:
        sitelist.sort(key=itemgetter('distance'))
    except KeyError:
        #if geoip service can't add distance then we can't autolocate
        utilities.log(__addonid__, "Can't autolocate. Returned sitelist doesn't have 'distance' key.", DEBUG)
        return
    first = sitelist[0]
    __addon__.setSetting(location, first['name'])
    __addon__.setSetting('%sID' % location, first['id'])

    utilities.log(__addonid__, "Location set to '%s'" % first['name'], DEBUG)

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
    utilities.log(__addonid__, "Setting '%s' ..." % location, DEBUG)
    text = get_keyboard_text()
    dialog = xbmcgui.Dialog()
    sitelist = get_sitelist(location)

    if location == 'RegionalLocation':
        #bug in datapoint: sitelist requires cleaning for regional forecast
        sitelist = utilities.clean_sitelist(sitelist)
        #long names are more user friendly
        for site in sitelist:
            site['name'] = utilities.LONG_REGIONAL_NAMES[site['name']]

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
        utilities.log(__addonid__, "No locations found containing '%s'" % text, DEBUG)

#MAIN CODE
WEATHER_WINDOW_ID = 12600
WEATHER_WINDOW = xbmcgui.Window(WEATHER_WINDOW_ID)

DEBUG = True if __addon__.getSetting('Debug') == 'true' else False
API_KEY = __addon__.getSetting('ApiKey')
AUTOLOCATION = True if __addon__.getSetting('AutoLocation') == 'true' else False
FORCEAUTOLOCATION = True if __addon__.getSetting('ForceAutoLocation') == 'true' else False

utilities.log(__addonid__, 'Startup...', DEBUG)
WEATHER_WINDOW.setProperty('WeatherProvider', __addonname__)

if not API_KEY:
    dialog = xbmcgui.Diautilities.log()
    dialog.ok('No API Key', 'Enter your Met Office API Key under weather settings.')
    utilities.log(__addonid__, 'Error, No API Key', DEBUG)
    sys.exit(1)

if sys.argv[1] == ('SetLocation'):
    set_location(sys.argv[2])
else:
    if FORCEAUTOLOCATION or (AUTOLOCATION and not __addon__.getSetting('ForecastLocation')):
        auto_location('ForecastLocation')
    if FORCEAUTOLOCATION or (AUTOLOCATION and not __addon__.getSetting('ObservationLocation')):
        auto_location('ObservationLocation')

    set_daily_forecast()
    set_3hourly_forecast()
    if sys.argv[1] == "RegionalForecast":
        set_properties(sys.argv[1])

    set_observation()

WEATHER_WINDOW.setProperty('Location1', __addon__.getSetting('ForecastLocation'))
WEATHER_WINDOW.setProperty('Locations', '1')

utilities.log(__addonid__, 'Done!', DEBUG)
