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
import shutil

from datetime import datetime, timedelta
from PIL import Image
from urllib2 import URLError
from operator import itemgetter

from resources.lib import utilities
from resources.lib import jsonparser
from resources.lib import datapoint
from resources.lib.urlcache import URLCache
from resources.lib.utilities import log

__addon__ = xbmcaddon.Addon()
ADDON_DATA_PATH = xbmc.translatePath('special://profile/addon_data/%s/' % __addon__.getAddonInfo('id'))

DEFAULT_INITIAL_TIMESTEP = '0'
DEFAULT_INITIAL_LAYER = 'Rainfall'

GOOGLE_BASE = 'http://maps.googleapis.com/maps/api/staticmap'
GOOGLE_GLOBAL = GOOGLE_BASE + '?sensor={sensor}&center={center}&zoom={zoom}&size={size}'
GOOGLE_SURFACE = GOOGLE_GLOBAL + '&maptype={maptype}'
GOOGLE_MARKER = GOOGLE_GLOBAL + '&style={style}&markers={markers}'

RAW_DATAPOINT_IMG_WIDTH = 500
CROP_WIDTH = 40
CROP_HEIGHT = 20

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

    panel_name = panel_config.get('name')
    if WEATHER_WINDOW.getProperty('%s.IssuedAt' % panel):
        issuedat = WEATHER_WINDOW.getProperty('%s.IssuedAt' % panel)
        updatefrequency = timedelta(**panel_config['updatefrequency'])
        try:
            issuedat = datetime.fromtimestamp(time.mktime(time.strptime(issuedat, utilities.ISSUEDAT_FORMAT)))
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
    except (socket.timeout, URLError, ValueError) as e:
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
        __addon__.setSetting("%sLatitude" % location, str(filtered_sites[selected].get('latitude')))
        __addon__.setSetting("%sLongitude" % location, str(filtered_sites[selected].get('longitude')))
        log( "Setting '%s' to '%s (%s)'" % (location, filtered_sites[selected]['name'], filtered_sites[selected]['id']))

def set_map():
    #there are two kinds of fetches for this app, get a json file and get an image file.
    with URLCache(cache_file, cache_folder) as cache:
        layer = WEATHER_WINDOW.getProperty('ForecastMap.LayerSelection') or DEFAULT_INITIAL_LAYER
        timestepindex = WEATHER_WINDOW.getProperty('ForecastMap.SliderPosition') or DEFAULT_INITIAL_TIMESTEP
    
        #get underlay map
        params = {'sensor':'false', 'center':'55,-3.5','zoom':'5','size':'323x472'}
        url=GOOGLE_SURFACE.format(maptype='satellite', **params)
        expiry = datetime.now() + timedelta(days=30)
        xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        try:
            file = cache.urlretrieve(url, expiry)
            WEATHER_WINDOW.setProperty('ForecastMap.Surface', file)
        except (URLError, IOError):
            WEATHER_WINDOW.setProperty('ForecastMap.ConnectionFailure', 'true')
            return
        finally:
            xbmc.executebuiltin( "Dialog.Close(busydialog)" )

        #get marker map
        lat = __addon__.getSetting('ForecastLocationLatitude')
        long = __addon__.getSetting('ForecastLocationLongitude')
        markers = '{lat},{long}'.format(lat=lat, long=long)
        url = GOOGLE_MARKER.format(style='feature:all|element:all|visibility:off', markers=markers, **params)
        expiry = datetime.now() + timedelta(days=30)
        xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        try:
            file = cache.urlretrieve(url, expiry)
        except (URLError, IOError):
            WEATHER_WINDOW.setProperty('ForecastMap.ConnectionFailure', 'true')
            return
        else:
            WEATHER_WINDOW.setProperty('ForecastMap.Marker', file)
            #remove any marker that isn't the one we just fetched
            markers = '(?!{lat})(\d+),(?!{long})(\d+)'.format(lat=lat, long=long)
            pattern = GOOGLE_MARKER.replace('?', '\?').format(sensor='false', center='55,-3.5',zoom='5',size='323x472',
                                       style='feature:all|element:all|visibility:off', markers=markers)
            cache.flush(pattern)
        finally:
            xbmc.executebuiltin( "Dialog.Close(busydialog)" )

        #get capabilities
        url=datapoint.url(format='layer', resource='wxfcs', object='capabilities', params={'key': API_KEY})
        expiry = datetime.now() + timedelta(hours=12) #need to investigate further into how often forecasts are updated
        xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        try:
            with open(cache.urlretrieve(url, expiry)) as file:
                try:
                    data = json.load(file)
                except ValueError:
                    cache.remove(url)
                    log('Couldn\'t load json data from %s' % file.name)
                    return
        except (URLError, IOError):
            WEATHER_WINDOW.setProperty('ForecastMap.ConnectionFailure', 'true')
            return
        finally:
            xbmc.executebuiltin( "Dialog.Close(busydialog)" )

        LayerURL = data['Layers']['BaseUrl']['$']
        #consider using jsonpath here
        for thislayer in data['Layers']['Layer']:
            if thislayer['@displayName'] == layer:
                layer_name = thislayer['Service']['LayerName']
                image_format = thislayer['Service']['ImageFormat']
                default_time = thislayer['Service']['Timesteps']['@defaultTime']
                timesteps = thislayer['Service']['Timesteps']['Timestep']
                break
        else:
            log("Couldn't find layer '%s'" % layer)
            sys.exit(1)

        default = datetime.fromtimestamp(time.mktime(time.strptime(default_time, utilities.DATAPOINT_FORMAT)))
        #we create 12 slider positions but pressure only returns 8 timesteps.
        try:
            timestep = timesteps[int(timestepindex)]
        except IndexError:
            timestep = timesteps[0]
            WEATHER_WINDOW.setProperty('ForecastMap.SliderPosition', DEFAULT_INITIAL_TIMESTEP)
        delta = timedelta(hours=timestep)
        maptime = default + delta
        WEATHER_WINDOW.setProperty('ForecastMap.IssuedAt', default.strftime(utilities.ISSUEDAT_FORMAT))
        WEATHER_WINDOW.setProperty('ForecastMap.MapTime', maptime.strftime(utilities.MAPTIME_FORMAT))

        #get overlay using parameters from gui settings
        url = LayerURL.format(LayerName=layer_name,
                                 ImageFormat=image_format,
                                 DefaultTime=default_time,
                                 Timestep=timestep,
                                 key=API_KEY)
        expiry = datetime.now() + timedelta(hours=12) # change to midnight
        xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        try:
            file = cache.urlretrieve(url, expiry)
        except (URLError, IOError):
            WEATHER_WINDOW.setProperty('ForecastMap.ConnectionFailure', 'true')
            return
        else:
            WEATHER_WINDOW.setProperty('ForecastMap.Layer', file)
            #flush any image with the same name and timestep that isnt the one we just fetched
            pattern = LayerURL.replace('?', '\?').format(LayerName=layer_name,
                                 ImageFormat=image_format,
                                 DefaultTime="(?!%s)(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})" % default_time,
                                 Timestep=timestep,
                                 key="[a-z0-9-]+")
            cache.flush(pattern)
            #remove the 'cone' from the image
            img = Image.open(file)
            (width, height) = img.size
            if width == RAW_DATAPOINT_IMG_WIDTH:
                img.crop((CROP_WIDTH, CROP_HEIGHT, width-CROP_WIDTH, height-CROP_HEIGHT)).save(file)
        finally:
            xbmc.executebuiltin( "Dialog.Close(busydialog)" )

#MAIN CODE
WEATHER_WINDOW_ID = 12600
WEATHER_WINDOW = xbmcgui.Window(WEATHER_WINDOW_ID)

DEBUG = True if __addon__.getSetting('Debug') == 'true' else False
API_KEY = __addon__.getSetting('ApiKey')
AUTOLOCATION = True if __addon__.getSetting('AutoLocation') == 'true' else False
FORCEAUTOLOCATION = True if __addon__.getSetting('ForceAutoLocation') == 'true' else False
cache_folder = os.path.join(ADDON_DATA_PATH, 'cache')
if not os.path.exists(cache_folder):
    os.makedirs(cache_folder)
cache_file = os.path.join(ADDON_DATA_PATH, 'cache.json')
cache = URLCache(cache_file, cache_folder)

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
