import xbmc #@UnresolvedImport
import xbmcaddon #@UnresolvedImport
import sys
import socket
import json
socket.setdefaulttimeout(20)

from datetime import datetime, timedelta
from PIL import Image
from operator import itemgetter

from utils import utilities, jsonparser, datapoint, urlcache, locator

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

def auto_location(location):
    utilities.log( "Auto-assigning '%s'..." % location)
    GEOIP_PROVIDER = int(__addon__.getSetting('GeoIPProvider'))
    if not GEOIP_PROVIDER:
        utilities.log( 'No GeoIP Provider is set.')
        GEOIP_PROVIDER = 0
    url = {'ForecastLocation' : datapoint.FORECAST_SITELIST_URL,
           'ObservationLocation': datapoint.OBSERVATION_SITELIST_URL}[location]
    url = url.format(key=API_KEY)

    with urlcache.URLCache(utilities.ADDON_DATA_PATH) as cache:
        with cache.get(url, lambda x: datetime.now()+timedelta(weeks=1)) as fyle:
            data = json.load(fyle)

    sitelist = data['Locations']['Location']
    locator.distances(sitelist, GEOIP_PROVIDER)
    sitelist.sort(key=itemgetter('distance'))
    first = sitelist[0]
    __addon__.setSetting(location, first['name'])
    __addon__.setSetting('%sID' % location, first['id'])
    utilities.log( "Location set to '%s'" % first['name'])

def daily_expiry(fyle):
    with open(fyle) as f:
        data = json.load(f)
        dataDate = data['SiteRep']['DV']['dataDate'].rstrip('Z')
        return utilities.strptime(dataDate, utilities.DATAPOINT_DATETIME_FORMAT) + timedelta(hours=1.5)

def threehourly_expiry(fyle):
    with open(fyle) as f:
        data = json.load(f)
        dataDate = data['SiteRep']['DV']['dataDate'].rstrip('Z')
        return utilities.strptime(dataDate, utilities.DATAPOINT_DATETIME_FORMAT) + timedelta(hours=1.5)

def text_expiry(fyle):
    with open(fyle) as f:
        data = json.load(f)
        issuedAt = data['RegionalFcst']['issuedAt'].rstrip('Z')
        return utilities.strptime(issuedAt, utilities.DATAPOINT_DATETIME_FORMAT) + timedelta(hours=12)

def observation_expiry(fyle):
    with open(fyle) as f:
        data = json.load(f)
        dataDate = data['SiteRep']['DV']['dataDate'].rstrip('Z')
        return utilities.strptime(dataDate, utilities.DATAPOINT_DATETIME_FORMAT) + timedelta(hours=1.5)

def layer_capabilities_expiry(fyle):
    with open(fyle) as f:
        data = json.load(f)
        defaultTime = data['Layers']['Layer'][0]['Service']['Timesteps']['@defaultTime']
        return utilities.strptime(defaultTime, utilities.DATAPOINT_DATETIME_FORMAT) + timedelta(hours=9)

def layer_image_expiry(fyle):
    return datetime.now() + timedelta(days=1)

def google_expiry(fyle):
    return datetime.now() + timedelta(days=30)

@utilities.panelbusy('RightPane')
def set_daily_forecast():
    name = __addon__.getSetting('ForecastLocation')
    flid = __addon__.getSetting('ForecastLocationID')
    utilities.log( "Fetching Daily Forecast for '%s (%s)' from the Met Office..." % (name, flid))
    url = datapoint.DAILY_LOCATION_FORECAST_URL.format(object=flid, key=API_KEY)
    with urlcache.URLCache(utilities.ADDON_DATA_PATH) as cache:
        with cache.get(url, daily_expiry) as fyle:
            report = jsonparser.daily(json.load(fyle))
    for field, value in report.iteritems():
        WEATHER_WINDOW.setProperty(field, value)
    WEATHER_WINDOW.setProperty('DailyForecast.IsFetched', 'true')

@utilities.panelbusy('RightPane')
def set_3hourly_forecast():
    name = __addon__.getSetting('ForecastLocation')
    flid = __addon__.getSetting('ForecastLocationID')
    utilities.log( "Fetching 3 Hourly Forecast for '%s (%s)' from the Met Office..." % (name, flid))
    url = datapoint.THREEHOURLY_LOCATION_FORECAST_URL.format(object=flid, key=API_KEY)
    with urlcache.URLCache(utilities.ADDON_DATA_PATH) as cache:
        with cache.get(url, threehourly_expiry) as fyle:
            report = jsonparser.threehourly(json.load(fyle))
    for field, value in report.iteritems():
        WEATHER_WINDOW.setProperty(field, value)
    WEATHER_WINDOW.setProperty('3HourlyForecast.IsFetched', 'true')

@utilities.panelbusy('RightPane')
def set_text_forecast():
    name = __addon__.getSetting('RegionalLocation')
    rlid = __addon__.getSetting('RegionalLocationID')
    utilities.log( "Fetching Text Forecast for '%s (%s)' from the Met Office..." % (name, rlid))
    url = datapoint.TEXT_FORECAST_URL.format(object=rlid, key=API_KEY)
    with urlcache.URLCache(utilities.ADDON_DATA_PATH) as cache:
        with cache.get(url, text_expiry) as fyle:
            report = jsonparser.text(json.load(fyle))
    for field, value in report.iteritems():
        WEATHER_WINDOW.setProperty(field, value)
    WEATHER_WINDOW.setProperty('TextForecast.IsFetched', 'true')

@utilities.panelbusy('LeftPane')
def set_hourly_observation():
    name = __addon__.getSetting('ObservationLocation')
    olid = __addon__.getSetting('ObservationLocationID')
    utilities.log( "Fetching Hourly Observation for '%s (%s)' from the Met Office..." % (name, olid))
    url = datapoint.HOURLY_LOCATION_OBSERVATION_URL.format(object=olid, key=API_KEY)
    with urlcache.URLCache(utilities.ADDON_DATA_PATH) as cache:
        with cache.get(url, observation_expiry) as fyle:
            report = jsonparser.observation(json.load(fyle))
    for field, value in report.iteritems():
        WEATHER_WINDOW.setProperty(field, value)
    WEATHER_WINDOW.setProperty('HourlyObservation.IsFetched', 'true')

@utilities.panelbusy('RightPane')
def set_forecast_layer():
    with urlcache.URLCache(utilities.ADDON_DATA_PATH) as cache:
        #there are two kinds of fetches for this app, get a json file and get an image file.
        params = {'sensor':'false', 'center':'55,-3.5','zoom':'5','size':'323x472'}

        #get underlay map
        url=GOOGLE_SURFACE.format(maptype='satellite', **params)
        with cache.get(url, google_expiry) as fyle:
            surface = fyle.name
        #get marker map
        lat = __addon__.getSetting('ForecastLocationLatitude')
        lng = __addon__.getSetting('ForecastLocationLongitude')

        markers = '{lat},{lng}'.format(lat=lat, lng=lng)
        url = GOOGLE_MARKER.format(style='feature:all|element:all|visibility:off', markers=markers, **params)
        with cache.get(url, google_expiry) as fyle:
            marker = fyle.name

        #remove any marker that isn't the one we just fetched
        markers = '(?!{lat})(\d+),(?!{long})(\d+)'.format(lat=lat, long=long)

        #get capabilities
        url = datapoint.FORECAST_LAYER_CAPABILITIES_URL.format(key=API_KEY)
        
        with cache.get(url, layer_capabilities_expiry) as fyle:
            data = json.load(fyle)
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
            utilities.log("Couldn't find layer '%s'" % selection)
            return

        issuedat = utilities.strptime(default_time, utilities.DATAPOINT_DATETIME_FORMAT)
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
        with cache.get(url, layer_image_expiry) as fyle:
            layer = fyle.name

        #remove the 'cone' from the image
        img = Image.open(layer)
        (width, height) = img.size
        if width == RAW_DATAPOINT_IMG_WIDTH:
            img.crop((CROP_WIDTH, CROP_HEIGHT, width-CROP_WIDTH, height-CROP_HEIGHT)).save(layer, image_format)

        WEATHER_WINDOW.setProperty('ForecastMap.Surface', surface)
        WEATHER_WINDOW.setProperty('ForecastMap.Marker', marker)
        WEATHER_WINDOW.setProperty('ForecastMap.SliderPosition', timestepindex)
        WEATHER_WINDOW.setProperty('ForecastMap.IssuedAt', issuedat.strftime(utilities.ISSUEDAT_FORMAT))
        WEATHER_WINDOW.setProperty('ForecastMap.MapTime', maptime.strftime(utilities.MAPTIME_FORMAT))
        WEATHER_WINDOW.setProperty('ForecastMap.Layer', layer)
        WEATHER_WINDOW.setProperty('ForecastMap.IsFetched', 'true')

#MAIN CODE
WEATHER_WINDOW = utilities.WEATHER_WINDOW

API_KEY = __addon__.getSetting('ApiKey')
AUTOLOCATION = True if __addon__.getSetting('AutoLocation') == 'true' else False
FORCEAUTOLOCATION = True if __addon__.getSetting('ForceAutoLocation') == 'true' else False

@utilities.failgracefully
def main():
    if not API_KEY:
        raise Exception('No API Key. Enter your Met Office API Key under settings.')

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
    elif sys.argv[1] == 'TextForecast':
        set_text_forecast()
    elif sys.argv[1] == 'HourlyObservation':
        set_hourly_observation()

    WEATHER_WINDOW.setProperty('WeatherProvider', __addon__.getAddonInfo('name'))
    WEATHER_WINDOW.setProperty('ObservationLocation', __addon__.getSetting('ObservationLocation'))
    WEATHER_WINDOW.setProperty('ForecastLocation', __addon__.getSetting('ForecastLocation'))
    WEATHER_WINDOW.setProperty('RegionalLocation', __addon__.getSetting('RegionalLocation'))
    WEATHER_WINDOW.setProperty('Location1', __addon__.getSetting('ObservationLocation'))
    WEATHER_WINDOW.setProperty('Locations', '1')

if __name__ == '__main__':
    main()