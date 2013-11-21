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
__media__       = os.path.join( __addonpath__, 'resources', 'media' )

sys.path.append(__resource__)

#We can now import from local lib dir
#Need to think about whether this fudging is a good thing
import utilities
import datapointapi
ISSUEDAT_FORMAT = '%Y-%m-%dT%H:%M:%S'
REGIONAL_FORECAST_INTERVAL = timedelta(hours=1)
ACTUAL_TEMP_FRAME_ICON = os.path.join(__media__, 'temp', 'actual.png')
FEELSLIKE_TEMP_FRAME_ICON = os.path.join(__media__, 'temp', 'feelslike.png')

def log(msg, level=xbmc.LOGNOTICE):
    xbmc.log("%s: %s" %(__addonid__, msg), level)

def set_empty_daily_forecast():
    log("Setting empty daily forecast...")
    clear = utilities.empty_daily_forecast()
    for field, value in clear.iteritems():
        WEATHER_WINDOW.setProperty(field, value)

def set_empty_3hourly_forecast():
    log("Setting empty 3 hourly forecast...", DEBUG)
    clear = utilities.empty_3hourly_forecast()
    for field, value in clear.iteritems():
        WEATHER_WINDOW.setProperty(field, value)

def set_empty_regional_forecast():
    log("Setting empty regional forecast...", DEBUG)
    clear = utilities.empty_3hourly_forecast()
    for field, value in clear.iteritems():
        WEATHER_WINDOW.setProperty(field, value)
    
def set_empty_observation():
    log("Setting empty observation...", DEBUG)
    clear = utilities.empty_observation()
    for field, value in clear.iteritems():
        WEATHER_WINDOW.setProperty(field, value)

def set_properties(panel):
    #Look at the time the last regional forecast was fetched
    #and if fetched over a given period ago then refetch.
    config = {
        'DailyForecast' : {
            'name' : 'Daily Forecast',
            'interval' : timedelta(hours=1),
            'location_name' : 'ForecastLocation',
            'location_id' : 'ForecastLocationID',
            'api_args' : {
                'resource' : 'wxfcs',
                'params' : {'res' : 'daily'},
                'object' : __addon__.getSetting('ForecastLocationID')
            }
        },
        '3HourlyForecast' : {
            'name' : '3Hourly Forecast',
            'interval' : timedelta(hours=1),
            'location_name' : 'ForecastLocation',
            'location_id' : 'ForecastLocationID',
            'api_args' : {
                'resource' : 'wxfcs',
                'params' : {'res' : '3hourly'},
                'object' : __addon__.getSetting('ForecastLocationID')
            }
        },
        'RegionalForecast' : {
            'name' : 'Regional Forecast',
            'interval' : timedelta(hours=1),
            'location_name' : 'RegionalLocation',
            'location_id' : 'RegionalLocationID',
            'api_args' : {
                'format' : 'txt',
                'resource' : 'wxfcs',
                'group' : 'regionalforecast',
                'object' : __addon__.getSetting('RegionalLocationID')
            },
        },
        'HourlyObservation' : {
            'name' : 'Hourly Observation',
            'interval' : timedelta(hours=1),
            'location_name' : 'ObservationLocation',
            'location_id' : 'ObservationLocationID',
            'api_args' : {
                'params' : {'res' : 'hourly'},
                'object' : __addon__.getSetting('ObservationLocationID')
            }
        },
    }
    try:
        panel_config = config[panel]
    except KeyError:
        log("Unknown panel '%s'" % panel, xbmc.LOGERROR)
        return

    if WEATHER_WINDOW.getProperty('%s.IssuedAt' % panel):
        issuedat = WEATHER_WINDOW.getProperty('%s.IssuedAt' % panel)
        try:
            issuedat = datetime.fromtimestamp(time.mktime(time.strptime(issuedat, ISSUEDAT_FORMAT)))
        except ValueError:
            issuedat = datetime.now() - panel_config['interval']
        interval = datetime.now() - issuedat
        log("Last %s report was issued %s minutes ago." % (panel_config.get('name'), interval.seconds/60))
        if interval < panel_config['interval']:
            log("No need to fetch data.")
            return

    location_name = __addon__.getSetting(panel_config.get('location_name'))
    location_id = __addon__.getSetting(panel_config.get('location_id'))
    if not (location_id and location_name):
        log( "%s location is not set" % panel_config.get('name'), xbmc.LOGERROR)
        #set_empty_regional_forecast()
        return
    #Fetch data from Met Office:
    panel_name = panel_config.get('name')
    api_args = panel_config.get('api_args', {})
    try:
        api_args.get('params').update({'key': API_KEY})
    except AttributeError:
        api_args['params'] = {'key': API_KEY}
    
    url = datapointapi.url(**api_args)
    try:
        log( "Fetching %s for '%s (%s)' from the Met Office..." % (panel_name, location_name, location_id))
        log("URL: %s " % url)
        page = utilities.retryurlopen(url).decode('latin-1')
        log('Converting page to json data...')
        data = json.loads(page)
    except (URLError, ValueError) as e:
        log(str(e), xbmc.LOGERROR)
        return
    log('Converting json to XBMC properties...')
    report = utilities.parse_json_report(data)
    for field, value in report.iteritems():
        WEATHER_WINDOW.setProperty(field, value)
        #set_empty_regional_forecast()

def geoip_distance(sitelist):
    if __addon__.getSetting('GeoLocation') != 'true':
        return sitelist
    provider = int(__addon__.getSetting('GeoIPProvider'))
    url = utilities.GEOIP_PROVIDERS[provider]['url']
    log("Adding distances based on GeoIP data from %s" % url.split('/')[2].lstrip('www.'))
    log("URL: %s" % url)
    try:
        page = utilities.retryurlopen(url)
        geoip = json.loads(page)
    except (URLError, ValueError) as e:
        log( str(e), xbmc.LOGERROR)
        return sitelist
    #different geoip providers user different names for latitude, longitude
    latitude = utilities.GEOIP_PROVIDERS[provider]['latitude']
    longitude = utilities.GEOIP_PROVIDERS[provider]['longitude']

    try:
        (latitude, longitude) = (float(geoip[latitude]), float(geoip[longitude]))
    except TypeError:
        #if geoip provider returns None
        log( "Couldn't get lat,long data from %s" % url, xbmc.LOGERROR)
        return sitelist
    newlist = list(sitelist)
    for site in newlist:
        try:
            site['distance'] = int(utilities.haversine_distance(latitude, longitude, float(site['latitude']), float(site['longitude'])))
        except KeyError:
            log( "Site '%s' does not have latitude, longitude info" % site['name'], xbmc.LOGERROR)
            return sitelist
    return newlist

def get_sitelist(location):
    log("Getting sitelist for '%s'" % location)
    url_params = {
        'ForecastLocation' : {'resource' : 'wxfcs'},
        'ObservationLocation' : {'resource' : 'wxobs'},
        'RegionalLocation' : {'resource' : 'wxfcs', 'format': 'txt', 'group' : 'regionalforecast'},
        }
    args = url_params[location]
    args.update({'params':{'key': API_KEY}})
    url = datapointapi.url(**args)
    log("URL: %s" % url)
    xbmc.executebuiltin( "ActivateWindow(busydialog)" )
    try:
        page = utilities.retryurlopen(url).decode('latin-1')
        data = json.loads(page)
    except (URLError, ValueError) as e:
        log(str(e), xbmc.LOGERROR)
    finally:
        xbmc.executebuiltin( "Dialog.Close(busydialog)" )

    try:
        sitelist = data['Locations']['Location']
    except NameError:
        log("Could not fetch sitelist", xbmc.LOGERROR)

    if location == 'RegionalLocation':
        #bug in datapoint: sitelist requires cleaning for regional forecast
        sitelist = utilities.clean_sitelist(sitelist)
        #long names are more user friendly
        for site in sitelist:
            site['name'] = utilities.LONG_REGIONAL_NAMES[site['name']]

    return geoip_distance(sitelist)

def auto_location(location):
    log( "Auto-assigning '%s'..." % location)
    sitelist = get_sitelist(location)
    try:
        sitelist.sort(key=itemgetter('distance'))
    except KeyError:
        #if geoip service can't add distance then we can't autolocate
        log( "Can't autolocate. Returned sitelist doesn't have 'distance' key.")
        return
    first = sitelist[0]
    __addon__.setSetting(location, first['name'])
    __addon__.setSetting('%sID' % location, first['id'])

    log( "Location set to '%s'" % first['name'])

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
    keyboard = xbmc.Keyboard()
    keyboard.doModal()
    text= keyboard.isConfirmed() and keyboard.getText()
    dialog = xbmcgui.Dialog()
    sitelist = get_sitelist(location)
    filtered_sites = utilities.filter_sitelist(text, sitelist)
    if filtered_sites == []:
        dialog.ok("No Matches", "No locations found containing '%s'" % text)
        log( "No locations found containing '%s'" % text)
        return
    
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
        log( "Setting '%s' to '%s (%s)'" % (location, filtered_sites[selected]['name'], filtered_sites[selected]['id']))

#MAIN CODE
WEATHER_WINDOW_ID = 12600
WEATHER_WINDOW = xbmcgui.Window(WEATHER_WINDOW_ID)

DEBUG = True if __addon__.getSetting('Debug') == 'true' else False
API_KEY = __addon__.getSetting('ApiKey')
AUTOLOCATION = True if __addon__.getSetting('AutoLocation') == 'true' else False
FORCEAUTOLOCATION = True if __addon__.getSetting('ForceAutoLocation') == 'true' else False

if not API_KEY:
    dialog = xbmcgui.Dialog()
    dialog.ok('No API Key', 'Enter your Met Office API Key under weather settings.')
    log( 'No API Key', xbmc.LOGERROR)
    sys.exit(1)

if sys.argv[1].isdigit():
    #only autolocate when given a refresh command
    if FORCEAUTOLOCATION:
        auto_location('ForecastLocation')
        auto_location('ObservationLocation')
    elif AUTOLOCATION:
        if not __addon__.getSetting('ForecastLocation'):
            auto_location('ForecastLocation')
        if not __addon__.getSetting('ObservationLocation'):
            auto_location('ObservationLocation')

    #fetch all?
    #TODO: actually we want to do something smarter: look and see which panels are
    #visible and only fetch data for them, so we'll pass a list into set_properties?...
    set_properties('HourlyObservation')
    set_properties('DailyForecast')

elif sys.argv[1] == ('SetLocation'):
    set_location(sys.argv[2])
else:
    set_properties(sys.argv[1])

WEATHER_WINDOW.setProperty('Forecast.ActualTempFrameIcon', ACTUAL_TEMP_FRAME_ICON)
WEATHER_WINDOW.setProperty('Forecast.FeelsLikeTempFrameIcon', FEELSLIKE_TEMP_FRAME_ICON)
WEATHER_WINDOW.setProperty('WeatherProvider', __addonname__)
WEATHER_WINDOW.setProperty('Location1', __addon__.getSetting('ForecastLocation'))
WEATHER_WINDOW.setProperty('Locations', '1')
