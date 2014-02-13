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

from resources.lib import utilities, jsonparser, datapoint, urlcache, locator
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

def auto_location(location):
    GEOIP_PROVIDER = int(__addon__.getSetting('GeoIPProvider'))
    if not GEOIP_PROVIDER:
        log( 'No GeoIP Provider is set.')
        GEOIP_PROVIDER = 0
    
    log( "Auto-assigning '%s'..." % location)
    url = {'ForecastLocation' : datapoint.FORECAST_SITELIST_URL,
           'ObservationLocation': datapoint.OBSERVATION_SITELIST_URL}[location]
    url = url.format(key=API_KEY)
    with urlcache.URLCache(utilities.CACHE_FILE, utilities.CACHE_FOLDER) as cache:
        data = cache.jsonretrieve(url, datetime.now()+timedelta(weeks=1))
    sitelist = data['Locations']['Location']
    for site in sitelist:
        site['distance'] = locator.distance(float(site['latitude']), float(site['longitude']), GEOIP_PROVIDER)
    sitelist.sort(key=itemgetter('distance'))
    first = sitelist[0]
    __addon__.setSetting(location, first['name'])
    __addon__.setSetting('%sID' % location, first['id'])
    log( "Location set to '%s'" % first['name'])

def set_daily_forecast():
    name = __addon__.getSetting('ForecastLocation')
    id = __addon__.getSetting('ForecastLocationID')
    log( "Fetching Daily Forecast for '%s (%s)' from the Met Office..." % (name, id))
    url = datapoint.DAILY_LOCATION_FORECAST_URL.format(object=id, key=API_KEY)
    expiry = datetime.now() + timedelta(hours=1)
    with urlcache.URLCache(utilities.CACHE_FILE, utilities.CACHE_FOLDER) as cache:
        data = cache.jsonretrieve(url, expiry)
    report = jsonparser.daily(data)
    for field, value in report.iteritems():
        WEATHER_WINDOW.setProperty(field, value)

def set_3hourly_forecast():
    name = __addon__.getSetting('ForecastLocation')
    id = __addon__.getSetting('ForecastLocationID')
    log( "Fetching 3 Hourly Forecast for '%s (%s)' from the Met Office..." % (name, id))
    url = datapoint.THREEHOURLY_LOCATION_FORECAST_URL.format(object=id, key=API_KEY)
    expiry = datetime.now() + timedelta(hours=1)
    with urlcache.URLCache(utilities.CACHE_FILE, utilities.CACHE_FOLDER) as cache:
        data = cache.jsonretrieve(url, expiry)
    report = jsonparser.threehourly(data)
    for field, value in report.iteritems():
        WEATHER_WINDOW.setProperty(field, value)

def set_regional_forecast():
    name = __addon__.getSetting('RegionalLocation')
    id = __addon__.getSetting('RegionalLocationID')
    log( "Fetching Regional Forecast for '%s (%s)' from the Met Office..." % (name, id))
    url = datapoint.REGIONAL_TEXT_URL.format(object=id, key=API_KEY)
    expiry = datetime.now() + timedelta(hours=1)
    with urlcache.URLCache(utilities.CACHE_FILE, utilities.CACHE_FOLDER) as cache:
        data = cache.jsonretrieve(url, expiry)
    report = jsonparser.regional(data)
    for field, value in report.iteritems():
        WEATHER_WINDOW.setProperty(field, value)

def set_hourly_observation():
    name = __addon__.getSetting('ObservationLocation')
    id = __addon__.getSetting('ObservationLocationID')
    log( "Fetching Hourly Observation for '%s (%s)' from the Met Office..." % (name, id))
    url = datapoint.HOURLY_LOCATION_OBSERVATION_URL.format(object=id, key=API_KEY)
    expiry = datetime.now() + timedelta(hours=1)
    with urlcache.URLCache(utilities.CACHE_FILE, utilities.CACHE_FOLDER) as cache:
        data = cache.jsonretrieve(url, expiry)
    report = jsonparser.observation(data)
    for field, value in report.iteritems():
        WEATHER_WINDOW.setProperty(field, value)

def set_forecast_layer():
    #there are two kinds of fetches for this app, get a json file and get an image file.
    with urlcache.URLCache(utilities.CACHE_FILE, utilities.CACHE_FOLDER) as cache:
        layer = WEATHER_WINDOW.getProperty('ForecastMap.LayerSelection') or DEFAULT_INITIAL_LAYER
        timestepindex = WEATHER_WINDOW.getProperty('ForecastMap.SliderPosition') or DEFAULT_INITIAL_TIMESTEP
        params = {'sensor':'false', 'center':'55,-3.5','zoom':'5','size':'323x472'}
        google_expiry = datetime.now() + timedelta(days=30)

        #get underlay map
        url=GOOGLE_SURFACE.format(maptype='satellite', **params)
        xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        try:
            file = cache.urlretrieve(url, google_expiry)
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
        xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        try:
            file = cache.urlretrieve(url, google_expiry)
        except (URLError, IOError):
            WEATHER_WINDOW.setProperty('ForecastMap.ConnectionFailure', 'true')
            return
        else:
            #remove any marker that isn't the one we just fetched
            markers = '(?!{lat})(\d+),(?!{long})(\d+)'.format(lat=lat, long=long)
            pattern = GOOGLE_MARKER.replace('?', '\?').format(sensor='false', center='55,-3.5',zoom='5',size='323x472',
                                       style='feature:all|element:all|visibility:off', markers=markers)
            cache.flush(pattern)
            WEATHER_WINDOW.setProperty('ForecastMap.Marker', file)
        finally:
            xbmc.executebuiltin( "Dialog.Close(busydialog)" )

        #get capabilities
        url = datapoint.FORECAST_LAYER_CAPABILITIES_URL.format(key=API_KEY)
        data = cache.jsonretrieve(url)
        expiry = data['Layers']['Layer'][0]['Service']['Timesteps']['@defaultTime']
        expiry = datetime.fromtimestamp(time.mktime(time.strptime(expiry, utilities.DATAPOINT_FORMAT)))
        expiry = expiry + timedelta(hours=9)
        cache.setexpiry(url, expiry)

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
            return

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
        xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        try:
            file = cache.urlretrieve(url, expiry)
        except (URLError, IOError):
            WEATHER_WINDOW.setProperty('ForecastMap.ConnectionFailure', 'true')
            return
        else:
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
            WEATHER_WINDOW.setProperty('ForecastMap.Layer', file)
        finally:
            xbmc.executebuiltin( "Dialog.Close(busydialog)" )

#MAIN CODE
WEATHER_WINDOW_ID = 12600
WEATHER_WINDOW = xbmcgui.Window(WEATHER_WINDOW_ID)

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
    set_hourly_observation()
    set_daily_forecast()
elif sys.argv[1] == 'ForecastMap':
    set_forecast_layer()
elif sys.argv[1] == 'DailyForecast':
    set_daily_forecast()
elif sys.argv[1] == '3HourlyForecast':
    set_3hourly_forecast()
elif sys.argv[1] == 'RegionalForecast':
    set_regional_forecast()
elif sys.arg[1] == 'HourlyObservation':
    set_hourly_observation()

WEATHER_WINDOW.setProperty('WeatherProvider', __addon__.getAddonInfo('name'))
WEATHER_WINDOW.setProperty('ObservationLocation', __addon__.getSetting('ObservationLocation'))
WEATHER_WINDOW.setProperty('ForecastLocation', __addon__.getSetting('ForecastLocation'))
WEATHER_WINDOW.setProperty('RegionalLocation', __addon__.getSetting('RegionalLocation'))
WEATHER_WINDOW.setProperty('Location1', __addon__.getSetting('ObservationLocation'))
WEATHER_WINDOW.setProperty('Locations', '1')
