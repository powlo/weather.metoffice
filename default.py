import xbmc
import xbmcgui
import xbmcaddon
import os
import time
import sys
import socket
import json
import urllib
import xbmcvfs

from datetime import datetime, timedelta

from urllib2 import URLError
from operator import itemgetter

from resources.lib import utilities
from resources.lib import jsonparser
from resources.lib import datapoint
from resources.lib.utilities import log

ISSUEDAT_FORMAT = '%Y-%m-%dT%H:%M:%S'
DEFAULT_INITIAL_TIMESTEP = '0'

__addon__ = xbmcaddon.Addon()

def set_properties(panel):
    #Look at the time the last regional forecast was fetched
    #and if fetched over a given period ago then refetch.
    #TODO: Embed the url in the config, not the url params.
    config = {
        'DailyForecast' : {
            'name' : 'Daily Forecast',
            'updatefrequency' : {'hours' : 1},
            'location_name' : 'ForecastLocation',
            'location_id' : 'ForecastLocationID',
            'parser' : 'daily',
            'api_args' : {
                'resource' : 'wxfcs',
                'params' : {'res' : 'daily'},
            }
        },
        '3HourlyForecast' : {
            'name' : '3Hourly Forecast',
            'updatefrequency' : {'hours' : 1},
            'location_name' : 'ForecastLocation',
            'location_id' : 'ForecastLocationID',
            'parser' : 'threehourly',
            'api_args' : {
                'resource' : 'wxfcs',
                'params' : {'res' : '3hourly'},
            }
        },
        'RegionalForecast' : {
            'name' : 'Regional Forecast',
            'updatefrequency' : {'hours' : 12},
            'location_name' : 'RegionalLocation',
            'location_id' : 'RegionalLocationID',
            'parser' : 'regional',
            'api_args' : {
                'format' : 'txt',
                'resource' : 'wxfcs',
                'group' : 'regionalforecast',
            }
        },
        'HourlyObservation' : {
            'name' : 'Hourly Observation',
            'updatefrequency' : {'hours' : 1},
            'location_name' : 'ObservationLocation',
            'location_id' : 'ObservationLocationID',
            'parser' : 'observation',
            'api_args' : {
                'params' : {'res' : 'hourly'},
            }
        },
        'ForecastMap' : {
            'name' : 'Forecast Map',
            'updatefrequency' : {'hours' : 1},
            'location_name' : 'ObservationLocation',
            'location_id' : 'ObservationLocationID',
            'parser' : 'observation',
            'api_args' : {
                'params' : {'res' : 'hourly'},
            }
        },
    }
    try:
        panel_config = config[panel]
    except KeyError:
        log("Unknown panel '%s'" % panel, xbmc.LOGERROR)
        return

    #is there a file in the local directory?
    #load the file from the local directory.
    #why use file when properties have probably been set? protects against pollution from other weather addons?
    #all we need to do is set a property that points to a file
    #maps do not have a locationID used in the url, although we may want to set a location, ie latitude and longitude.
    #examine timestamp
    #if timestamp is out of date then refresh from server
    #

    panel_name = panel_config.get('name')
    if WEATHER_WINDOW.getProperty('%s.IssuedAt' % panel):
        issuedat = WEATHER_WINDOW.getProperty('%s.IssuedAt' % panel)
        updatefrequency = timedelta(**panel_config['updatefrequency'])
        try:
            issuedat = datetime.fromtimestamp(time.mktime(time.strptime(issuedat, ISSUEDAT_FORMAT)))
        except ValueError:
            issuedat = datetime.now() - updatefrequency
        interval = datetime.now() - issuedat
        log("Last %s report was issued %s ago." % (panel_name, utilities.verbose_timedelta(interval)))
        if interval < updatefrequency:
            log("No need to fetch data.")
            return

    location_name = __addon__.getSetting(panel_config.get('location_name'))
    location_id = __addon__.getSetting(panel_config.get('location_id'))
    if not (location_id and location_name):
        log( "%s location is not set" % panel_name, xbmc.LOGERROR)
        return
    #Fetch data from Met Office:
    api_args = panel_config.get('api_args', {})
    try:
        api_args.get('params').update({'key': API_KEY})
    except AttributeError:
        api_args['params'] = {'key': API_KEY}

    #assumes we always want 'object' to be set. True at the moment.
    api_args.update({'object' : location_id})

    url = datapoint.url(**api_args)
    try:
        log( "Fetching %s for '%s (%s)' from the Met Office..." % (panel_name, location_name, location_id))
        log("URL: %s " % url)
        page = utilities.retryurlopen(url).decode('latin-1')
        log('Converting page to json data...')
        data = json.loads(page)
    except (socket.timeout, URLError, ValueError) as e:
        log(str(e), xbmc.LOGERROR)
        return
    log('Converting json to XBMC properties...')
    parsefunc = getattr(jsonparser, panel_config['parser'])
    report = parsefunc(data)
    for field, value in report.iteritems():
        WEATHER_WINDOW.setProperty(field, value)

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
    url = datapoint.url(**args)
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
        sitelist = datapoint.clean_sitelist(sitelist)
        #long names are more user friendly
        for site in sitelist:
            site['name'] = datapoint.LONG_REGIONAL_NAMES[site['name']]

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
    assert(location in datapoint.SITELIST_TYPES)
    keyboard = xbmc.Keyboard()
    keyboard.doModal()
    text= keyboard.isConfirmed() and keyboard.getText()
    dialog = xbmcgui.Dialog()
    sitelist = get_sitelist(location)
    filtered_sites = datapoint.filter_sitelist(text, sitelist)
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

def set_map():
    #note that we're doing the same thing over and over: see if something is in cache. if not get it from a url.
    #a proper cache will have a centralised resource which lists cached files and expiry times

    #get underlay map
    log('Checking cache for surface map')
    folder = xbmc.translatePath('special://profile/addon_data/%s/cache/surfacemap/' % __addon__.getAddonInfo('id'))
    if not xbmcvfs.exists(folder):
        log('Creating folder for surface map image.')
        xbmcvfs.mkdirs(folder)
    file = os.path.join(folder, 'surface.json')
    if not xbmcvfs.exists(file):
        log('No surface map file in cache. Fetching file.')
        url='http://maps.googleapis.com/maps/api/staticmap?center=55,-3.5&zoom=5&size=385x513&sensor=false&maptype=satellite&style=feature:all|element:labels|visibility:off'
        urllib.urlretrieve(url, file)
    else:
        log('Cached file found.')
    WEATHER_WINDOW.setProperty('Weather.MapSurfaceFile', file)

    #get capabilities
    log('Checking cache for layer capabilities file')
    folder = xbmc.translatePath('special://profile/addon_data/%s/cache/layer/' % __addon__.getAddonInfo('id'))
    if not xbmcvfs.exists(folder):
        log('Creating folder for layer images.')
        xbmcvfs.mkdirs(folder)
    file = os.path.join(folder, 'capabilities.json')
    if not xbmcvfs.exists(file):
        log('No capbilities file in cache. Fetching file from datapoint.')
        url=datapoint.url(format='layer', resource='wxfcs', object='capabilities', params={'key': API_KEY})
        urllib.urlretrieve(url, file)
    else:
        log('Cached file found.')
    handle = open(file, 'r')
    data = json.load(handle)
    LayerURL = data['Layers']['BaseUrl']['$']
    #consider using jsonpath here
    for thislayer in data['Layers']['Layer']:
        if thislayer['@displayName'] == 'Rainfall':
            layer_name = thislayer['Service']['LayerName']
            image_format = thislayer['Service']['ImageFormat']
            default_time = thislayer['Service']['Timesteps']['@defaultTime']
            timesteps = thislayer['Service']['Timesteps']['Timestep']
            break
    else:
        log("Couldn't find layer")

    #get overlay using parameters from gui settings
    timestep = WEATHER_WINDOW.getProperty('Weather.SliderPosition') or DEFAULT_INITIAL_TIMESTEP
    url = LayerURL.format(LayerName=layer_name,
                             ImageFormat=image_format,
                             DefaultTime=default_time,
                             Timestep=timesteps[int(timestep)],
                             key=API_KEY)
    folder = xbmc.translatePath('special://profile/addon_data/%s/cache/layer/Rainfall/%s/' % (__addon__.getAddonInfo('id'), default_time))
    if not xbmcvfs.exists(folder):
        xbmcvfs.mkdirs(folder)
    file = os.path.join(folder, '{timestep}.png'.format(timestep=timestep))
    urllib.urlretrieve(url, file)
    WEATHER_WINDOW.setProperty('Weather.MapLayerFile', file)

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
elif sys.argv[1] == ('ForecastMap'):
    set_map()
else:
    set_properties(sys.argv[1])

WEATHER_WINDOW.setProperty('WeatherProvider', __addon__.getAddonInfo('name'))
WEATHER_WINDOW.setProperty('ObservationLocation', __addon__.getSetting('ObservationLocation'))
WEATHER_WINDOW.setProperty('ForecastLocation', __addon__.getSetting('ForecastLocation'))
WEATHER_WINDOW.setProperty('RegionalLocation', __addon__.getSetting('RegionalLocation'))
WEATHER_WINDOW.setProperty('Location1', __addon__.getSetting('ObservationLocation'))
WEATHER_WINDOW.setProperty('Locations', '1')
