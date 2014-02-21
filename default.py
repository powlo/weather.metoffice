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
import socket
socket.setdefaulttimeout(20)

from datetime import datetime, timedelta
from PIL import Image
from urllib2 import URLError
from operator import itemgetter

from resources.lib import utilities, jsonparser, datapoint, urlcache, locator

__addon__ = xbmcaddon.Addon()
ADDON_DATA_PATH = xbmc.translatePath('special://profile/addon_data/%s/' % __addon__.getAddonInfo('id'))

DEFAULT_INITIAL_LAYER = 'Rainfall'

GOOGLE_BASE = 'http://maps.googleapis.com/maps/api/staticmap'
GOOGLE_GLOBAL = GOOGLE_BASE + '?sensor={sensor}&center={center}&zoom={zoom}&size={size}'
GOOGLE_SURFACE = GOOGLE_GLOBAL + '&maptype={maptype}'
GOOGLE_MARKER = GOOGLE_GLOBAL + '&style={style}&markers={markers}'

RAW_DATAPOINT_IMG_WIDTH = 500
CROP_WIDTH = 40
CROP_HEIGHT = 20

def auto_location(location, cache):
    GEOIP_PROVIDER = int(__addon__.getSetting('GeoIPProvider'))
    if not GEOIP_PROVIDER:
        xbmc.log( 'No GeoIP Provider is set.')
        GEOIP_PROVIDER = 0
    
    xbmc.log( "Auto-assigning '%s'..." % location)
    url = {'ForecastLocation' : datapoint.FORECAST_SITELIST_URL,
           'ObservationLocation': datapoint.OBSERVATION_SITELIST_URL}[location]
    url = url.format(key=API_KEY)
    data = cache.jsonretrieve(url, datetime.now()+timedelta(weeks=1))
    sitelist = data['Locations']['Location']
    for site in sitelist:
        site['distance'] = locator.distance(float(site['latitude']), float(site['longitude']), GEOIP_PROVIDER)
    sitelist.sort(key=itemgetter('distance'))
    first = sitelist[0]
    __addon__.setSetting(location, first['name'])
    __addon__.setSetting('%sID' % location, first['id'])
    xbmc.log( "Location set to '%s'" % first['name'])

def set_daily_forecast(cache):
    name = __addon__.getSetting('ForecastLocation')
    id = __addon__.getSetting('ForecastLocationID')
    xbmc.log( "Fetching Daily Forecast for '%s (%s)' from the Met Office..." % (name, id))
    url = datapoint.DAILY_LOCATION_FORECAST_URL.format(object=id, key=API_KEY)
    expiry = datetime.now() + timedelta(hours=1)
    data = cache.jsonretrieve(url, expiry)
    report = jsonparser.daily(data)
    for field, value in report.iteritems():
        WEATHER_WINDOW.setProperty(field, value)
    WEATHER_WINDOW.setProperty('DailyForecast.IsFetched', 'true')

def set_3hourly_forecast(cache):
    name = __addon__.getSetting('ForecastLocation')
    id = __addon__.getSetting('ForecastLocationID')
    xbmc.log( "Fetching 3 Hourly Forecast for '%s (%s)' from the Met Office..." % (name, id))
    url = datapoint.THREEHOURLY_LOCATION_FORECAST_URL.format(object=id, key=API_KEY)
    expiry = datetime.now() + timedelta(hours=1)
    data = cache.jsonretrieve(url, expiry)
    report = jsonparser.threehourly(data)
    for field, value in report.iteritems():
        WEATHER_WINDOW.setProperty(field, value)
    WEATHER_WINDOW.setProperty('3HourlyForecast.IsFetched', 'true')

def set_text_forecast(cache):
    name = __addon__.getSetting('RegionalLocation')
    id = __addon__.getSetting('RegionalLocationID')
    xbmc.log( "Fetching Text Forecast for '%s (%s)' from the Met Office..." % (name, id))
    url = datapoint.TEXT_FORECAST_URL.format(object=id, key=API_KEY)
    expiry = datetime.now() + timedelta(hours=1)
    data = cache.jsonretrieve(url, expiry)
    report = jsonparser.text(data)
    for field, value in report.iteritems():
        WEATHER_WINDOW.setProperty(field, value)
    WEATHER_WINDOW.setProperty('TextForecast.IsFetched', 'true')

def set_hourly_observation(cache):
    name = __addon__.getSetting('ObservationLocation')
    id = __addon__.getSetting('ObservationLocationID')
    xbmc.log( "Fetching Hourly Observation for '%s (%s)' from the Met Office..." % (name, id))
    url = datapoint.HOURLY_LOCATION_OBSERVATION_URL.format(object=id, key=API_KEY)
    expiry = datetime.now() + timedelta(hours=1)
    data = cache.jsonretrieve(url, expiry)
    report = jsonparser.observation(data)
    for field, value in report.iteritems():
        WEATHER_WINDOW.setProperty(field, value)
    WEATHER_WINDOW.setProperty('HourlyObservation.IsFetched', 'true')

def set_forecast_layer(cache):
    #there are two kinds of fetches for this app, get a json file and get an image file.
    params = {'sensor':'false', 'center':'55,-3.5','zoom':'5','size':'323x472'}
    google_expiry = datetime.now() + timedelta(days=30)

    #get underlay map
    url=GOOGLE_SURFACE.format(maptype='satellite', **params)
    surface = cache.urlretrieve(url, google_expiry)

    #get marker map
    lat = __addon__.getSetting('ForecastLocationLatitude')
    long = __addon__.getSetting('ForecastLocationLongitude')

    markers = '{lat},{long}'.format(lat=lat, long=long)
    url = GOOGLE_MARKER.format(style='feature:all|element:all|visibility:off', markers=markers, **params)
    marker = cache.urlretrieve(url, google_expiry)

    #remove any marker that isn't the one we just fetched
    markers = '(?!{lat})(\d+),(?!{long})(\d+)'.format(lat=lat, long=long)
    pattern = GOOGLE_MARKER.replace('?', '\?').format(sensor='false', center='55,-3.5',zoom='5',size='323x472',
                               style='feature:all|element:all|visibility:off', markers=markers)
    cache.flush(pattern)

    #get capabilities
    url = datapoint.FORECAST_LAYER_CAPABILITIES_URL.format(key=API_KEY)
    data = cache.jsonretrieve(url)
    expiry = data['Layers']['Layer'][0]['Service']['Timesteps']['@defaultTime']
    expiry = datetime.fromtimestamp(time.mktime(time.strptime(expiry, utilities.DATAPOINT_FORMAT)))
    expiry = expiry + timedelta(hours=9)
    cache.setexpiry(url, expiry)

    selection = WEATHER_WINDOW.getProperty('ForecastMap.LayerSelection') or DEFAULT_INITIAL_LAYER
    #pull parameters out of capabilities file - consider using jsonpath here
    for thislayer in data['Layers']['Layer']:
        if thislayer['@displayName'] == selection:
            layer_name = thislayer['Service']['LayerName']
            image_format = thislayer['Service']['ImageFormat']
            default_time = thislayer['Service']['Timesteps']['@defaultTime']
            timesteps = thislayer['Service']['Timesteps']['Timestep']
            break
    else:
        xbmc.log("Couldn't find layer '%s'" % selection)
        return

    issuedat = datetime.fromtimestamp(time.mktime(time.strptime(default_time, utilities.DATAPOINT_FORMAT)))

    timestepindex = WEATHER_WINDOW.getProperty('ForecastMap.SliderPosition') or '0'

    #allow the timestep to be modified by a second argument. Supports keyboard navigation in skin.
    try:
        adjust = sys.argv[2]
    except IndexError:
        adjust = '0'
    timestepindex = str(int(timestepindex) + int(adjust))
    if int(timestepindex) < 0:
         timestepindex = '0'
    elif int(timestepindex) > len(timesteps)-1:
         timestepindex = str(len(timesteps)-1)

    timestep = timesteps[int(timestepindex)]
    delta = timedelta(hours=timestep)
    maptime = issuedat + delta

    #get overlay using parameters from gui settings
    LayerURL = data['Layers']['BaseUrl']['$']
    url = LayerURL.format(LayerName=layer_name,
                             ImageFormat=image_format,
                             DefaultTime=default_time,
                             Timestep=timestep,
                             key=API_KEY)
    layer = cache.urlretrieve(url, expiry)

    #flush any image with the same name and timestep that isnt the one we just fetched
    pattern = LayerURL.replace('?', '\?').format(LayerName=layer_name,
                         ImageFormat=image_format,
                         DefaultTime="(?!%s)(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})" % default_time,
                         Timestep=timestep,
                         key="[a-z0-9-]+")
    cache.flush(pattern)

    #remove the 'cone' from the image
    img = Image.open(layer)
    (width, height) = img.size
    if width == RAW_DATAPOINT_IMG_WIDTH:
        img.crop((CROP_WIDTH, CROP_HEIGHT, width-CROP_WIDTH, height-CROP_HEIGHT)).save(layer)

    WEATHER_WINDOW.setProperty('ForecastMap.Surface', surface)
    WEATHER_WINDOW.setProperty('ForecastMap.Marker', marker)
    WEATHER_WINDOW.setProperty('ForecastMap.SliderPosition', timestepindex)
    WEATHER_WINDOW.setProperty('ForecastMap.IssuedAt', issuedat.strftime(utilities.ISSUEDAT_FORMAT))
    WEATHER_WINDOW.setProperty('ForecastMap.MapTime', maptime.strftime(utilities.MAPTIME_FORMAT))
    WEATHER_WINDOW.setProperty('ForecastMap.Layer', layer)
    WEATHER_WINDOW.setProperty('ForecastMap.IsFetched', 'true')

#MAIN CODE
WEATHER_WINDOW = xbmcgui.Window(utilities.WINDOW_WEATHER)

API_KEY = __addon__.getSetting('ApiKey')
AUTOLOCATION = True if __addon__.getSetting('AutoLocation') == 'true' else False
FORCEAUTOLOCATION = True if __addon__.getSetting('ForceAutoLocation') == 'true' else False
POPUP = xbmcgui.Dialog()

@utilities.xbmcbusy
def main():
    try:
        with urlcache.URLCache(utilities.CACHE_FILE, utilities.CACHE_FOLDER) as cache:
            if not API_KEY:
                POPUP.ok('No API Key', 'Enter your Met Office API Key under weather settings.')
                xbmc.log( 'No API Key', xbmc.LOGERROR)
                sys.exit(1)

            if sys.argv[1].isdigit():
                #only autolocate when given a refresh command
                if FORCEAUTOLOCATION:
                    auto_location('ForecastLocation', cache)
                    auto_location('ObservationLocation', cache)
                elif AUTOLOCATION:
                    if not __addon__.getSetting('ForecastLocation'):
                        auto_location('ForecastLocation', cache)
                    if not __addon__.getSetting('ObservationLocation'):
                        auto_location('ObservationLocation', cache)

                #fetch all?
                #TODO: actually we want to do something smarter: look and see which panels are
                #visible and only fetch data for them, so we'll pass a list into set_properties?...
                set_hourly_observation(cache)
                set_daily_forecast(cache)
            elif sys.argv[1] == 'ForecastMap':
                set_forecast_layer(cache)
            elif sys.argv[1] == 'DailyForecast':
                set_daily_forecast(cache)
            elif sys.argv[1] == '3HourlyForecast':
                set_3hourly_forecast(cache)
            elif sys.argv[1] == 'TextForecast':
                set_text_forecast(cache)
            elif sys.arg[1] == 'HourlyObservation':
                set_hourly_observation(cache)

            WEATHER_WINDOW.clearProperty('{0}.ConnectionFailure'.format(sys.argv[1]))
            WEATHER_WINDOW.setProperty('WeatherProvider', __addon__.getAddonInfo('name'))
            WEATHER_WINDOW.setProperty('ObservationLocation', __addon__.getSetting('ObservationLocation'))
            WEATHER_WINDOW.setProperty('ForecastLocation', __addon__.getSetting('ForecastLocation'))
            WEATHER_WINDOW.setProperty('RegionalLocation', __addon__.getSetting('RegionalLocation'))
            WEATHER_WINDOW.setProperty('Location1', __addon__.getSetting('ObservationLocation'))
            WEATHER_WINDOW.setProperty('Locations', '1')
    except (URLError, IOError) as e:
        if xbmcgui.getCurrentWindowId() == utilities.WINDOW_WEATHER:
            if type(e)==URLError:
                line2 = e.reason
            else:
                line2 = e.filename if e.filename!=None else 'Check your internet connection'
            POPUP.ok(str(e.errno), str(e.strerror), line2)
            xbmc.log( '{0} {1} {2}'.format(e.errno, str(e.strerror), line2), xbmc.LOGERROR)
        WEATHER_WINDOW.setProperty('{0}.ConnectionFailure'.format(sys.argv[1]), 'true')

if __name__ == '__main__':
    main()