import sys
import socket
import json
socket.setdefaulttimeout(20)

from datetime import datetime, timedelta
from PIL import Image
from operator import itemgetter

import utilities, jsonparser, urlcache, locator
from constants import ADDON, ADDON_DATA_PATH, DATAPOINT_DATETIME_FORMAT, GOOGLE_SURFACE, GOOGLE_MARKER,\
                        DEFAULT_INITIAL_LAYER, RAW_DATAPOINT_IMG_WIDTH, CROP_WIDTH, CROP_HEIGHT,\
                        ISSUEDAT_FORMAT, MAPTIME_FORMAT, WINDOW, FORECAST_SITELIST_URL, OBSERVATION_SITELIST_URL,\
                        DAILY_LOCATION_FORECAST_URL, THREEHOURLY_LOCATION_FORECAST_URL, TEXT_FORECAST_URL,\
                        HOURLY_LOCATION_OBSERVATION_URL, FORECAST_LAYER_CAPABILITIES_URL, API_KEY

def auto_location(location):
    utilities.log( "Auto-assigning '%s'..." % location)
    GEOIP_PROVIDER = int(ADDON.getSetting('GeoIPProvider'))
    if not GEOIP_PROVIDER:
        utilities.log( 'No GeoIP Provider is set.')
        GEOIP_PROVIDER = 0
    url = {'ForecastLocation' : FORECAST_SITELIST_URL,
           'ObservationLocation': OBSERVATION_SITELIST_URL}[location]
    url = url.format(key=API_KEY)

    with urlcache.URLCache(ADDON_DATA_PATH) as cache:
        with cache.get(url, lambda x: datetime.now()+timedelta(weeks=1)) as fyle:
            data = json.load(fyle)

    sitelist = data['Locations']['Location']
    locator.distances(sitelist, GEOIP_PROVIDER)
    sitelist.sort(key=itemgetter('distance'))
    first = sitelist[0]
    ADDON.setSetting(location, first['name'])#@UndefinedVariable
    ADDON.setSetting('%sID' % location, first['id'])#@UndefinedVariable
    utilities.log( "Location set to '%s'" % first['name'])

@utilities.panelbusy('RightPane')
def set_daily_forecast():
    name = ADDON.getSetting('ForecastLocation')
    flid = ADDON.getSetting('ForecastLocationID')
    utilities.log( "Fetching Daily Forecast for '%s (%s)' from the Met Office..." % (name, flid))
    url = DAILY_LOCATION_FORECAST_URL.format(object=flid, key=API_KEY)
    with urlcache.URLCache(ADDON_DATA_PATH) as cache:
        with cache.get(url, jsonparser.daily_expiry) as fyle:
            report = jsonparser.daily(fyle)
    for field, value in report.iteritems():
        WINDOW.setProperty(field, value)#@UndefinedVariable
    WINDOW.setProperty('DailyForecast.IsFetched', 'true')#@UndefinedVariable

@utilities.panelbusy('RightPane')
def set_3hourly_forecast():
    name = ADDON.getSetting('ForecastLocation')
    flid = ADDON.getSetting('ForecastLocationID')
    utilities.log( "Fetching 3 Hourly Forecast for '%s (%s)' from the Met Office..." % (name, flid))
    url = THREEHOURLY_LOCATION_FORECAST_URL.format(object=flid, key=API_KEY)
    with urlcache.URLCache(ADDON_DATA_PATH) as cache:
        with cache.get(url, jsonparser.threehourly_expiry) as fyle:
            report = jsonparser.threehourly(fyle)
    for field, value in report.iteritems():
        WINDOW.setProperty(field, value)#@UndefinedVariable
    WINDOW.setProperty('3HourlyForecast.IsFetched', 'true')#@UndefinedVariable

@utilities.panelbusy('RightPane')
def set_text_forecast():
    name = ADDON.getSetting('RegionalLocation')
    rlid = ADDON.getSetting('RegionalLocationID')
    utilities.log( "Fetching Text Forecast for '%s (%s)' from the Met Office..." % (name, rlid))
    url = TEXT_FORECAST_URL.format(object=rlid, key=API_KEY)
    with urlcache.URLCache(ADDON_DATA_PATH) as cache:
        with cache.get(url, jsonparser.text_expiry) as fyle:
            report = jsonparser.text(fyle)
    for field, value in report.iteritems():
        WINDOW.setProperty(field, value)#@UndefinedVariable
    WINDOW.setProperty('TextForecast.IsFetched', 'true')#@UndefinedVariable

@utilities.panelbusy('LeftPane')
def set_hourly_observation():
    name = ADDON.getSetting('ObservationLocation')
    olid = ADDON.getSetting('ObservationLocationID')
    utilities.log( "Fetching Hourly Observation for '%s (%s)' from the Met Office..." % (name, olid))
    url = HOURLY_LOCATION_OBSERVATION_URL.format(object=olid, key=API_KEY)
    with urlcache.URLCache(ADDON_DATA_PATH) as cache:
        with cache.get(url, jsonparser.observation_expiry) as fyle:
            report = jsonparser.observation(fyle)
    for field, value in report.iteritems():
        WINDOW.setProperty(field, value)#@UndefinedVariable
    WINDOW.setProperty('HourlyObservation.IsFetched', 'true')#@UndefinedVariable

@utilities.panelbusy('RightPane')
def set_forecast_layer():
    with urlcache.URLCache(ADDON_DATA_PATH) as cache:
        #there are two kinds of fetches for this app, get a json file and get an image file.
        params = {'sensor':'false', 'center':'55,-3.5','zoom':'5','size':'323x472'}

        #get underlay map
        url=GOOGLE_SURFACE.format(maptype='satellite', **params)#@UndefinedVariable
        with cache.get(url, lambda x:  datetime.now() + timedelta(days=30)) as fyle:
            surface = fyle.name
        #get marker map
        lat = ADDON.getSetting('ForecastLocationLatitude')
        lng = ADDON.getSetting('ForecastLocationLongitude')

        markers = '{lat},{lng}'.format(lat=lat, lng=lng)
        url = GOOGLE_MARKER.format(style='feature:all|element:all|visibility:off', markers=markers, **params)#@UndefinedVariable
        with cache.get(url, lambda x:  datetime.now() + timedelta(days=30)) as fyle:
            marker = fyle.name

        #remove any marker that isn't the one we just fetched
        markers = '(?!{lat})(\d+),(?!{long})(\d+)'.format(lat=lat, long=long)

        #get capabilities
        url = FORECAST_LAYER_CAPABILITIES_URL.format(key=API_KEY)
        
        with cache.get(url, jsonparser.layer_capabilities_expiry) as fyle:
            data = json.load(fyle)
        selection = WINDOW.getProperty('ForecastMap.LayerSelection') or DEFAULT_INITIAL_LAYER#@UndefinedVariable
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

        issuedat = utilities.strptime(default_time, DATAPOINT_DATETIME_FORMAT)
        timestepindex = WINDOW.getProperty('ForecastMap.SliderPosition') or '0'#@UndefinedVariable

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
        with cache.get(url, lambda x: datetime.now() + timedelta(days=1)) as fyle:
            layer = fyle.name

        #remove the 'cone' from the image
        img = Image.open(layer)
        (width, height) = img.size
        if width == RAW_DATAPOINT_IMG_WIDTH:
            img.crop((CROP_WIDTH, CROP_HEIGHT, width-CROP_WIDTH, height-CROP_HEIGHT)).save(layer, image_format)

        WINDOW.setProperty('ForecastMap.Surface', surface)#@UndefinedVariable
        WINDOW.setProperty('ForecastMap.Marker', marker)#@UndefinedVariable
        WINDOW.setProperty('ForecastMap.SliderPosition', timestepindex)#@UndefinedVariable
        WINDOW.setProperty('ForecastMap.IssuedAt', issuedat.strftime(ISSUEDAT_FORMAT))#@UndefinedVariable
        WINDOW.setProperty('ForecastMap.MapTime', maptime.strftime(MAPTIME_FORMAT))#@UndefinedVariable
        WINDOW.setProperty('ForecastMap.Layer', layer)#@UndefinedVariable
        WINDOW.setProperty('ForecastMap.IsFetched', 'true')#@UndefinedVariable

#MAIN CODE

@utilities.failgracefully
def main():
    if not API_KEY:
        raise Exception('No API Key. Enter your Met Office API Key under settings.')

    if sys.argv[1].isdigit():
        #only autolocate when given a refresh command
        if ADDON.getSetting('ForceAutoLocation') == 'true':
            auto_location('ForecastLocation')
            auto_location('ObservationLocation')
        elif ADDON.getSetting('AutoLocation') == 'true':
            if not ADDON.getSetting('ForecastLocation'):
                auto_location('ForecastLocation')
            if not ADDON.getSetting('ObservationLocation'):
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

    WINDOW.setProperty('WeatherProvider', ADDON.getAddonInfo('name'))#@UndefinedVariable
    WINDOW.setProperty('ObservationLocation', ADDON.getSetting('ObservationLocation'))#@UndefinedVariable
    WINDOW.setProperty('ForecastLocation', ADDON.getSetting('ForecastLocation'))#@UndefinedVariable
    WINDOW.setProperty('RegionalLocation', ADDON.getSetting('RegionalLocation'))#@UndefinedVariable
    WINDOW.setProperty('Location1', ADDON.getSetting('ObservationLocation'))#@UndefinedVariable
    WINDOW.setProperty('Locations', '1')#@UndefinedVariable

if __name__ == '__main__':
    main()