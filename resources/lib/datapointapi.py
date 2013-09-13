#API for the Met Office's DataPoint API
#http://www.metoffice.gov.uk/datapoint
import urllib
import urllib2
from utilities import retryurlopen

BASE_URL = "http://datapoint.metoffice.gov.uk/public/data/"

OBSERVATION_SITE_LIST_URL      = "val/wxobs/all/%(datatype)s/sitelist?%(params)s"
OBSERVATION_CAPABILITIES_URL   = "val/wxobs/all/%(datatype)s/capabilities?%(params)s"
OBSERVATION_LOCATION_URL       = "val/wxobs/all/%(datatype)s/%(location)s?%(params)s"

FORECAST_SITE_LIST_URL         = "val/wxfcs/all/%(datatype)s/sitelist?%(params)s"
FORECAST_CAPABILITIES_URL      = "val/wxfcs/all/%(datatype)s/capabilities?%(params)s"
FORECAST_LOCATION_URL          = "val/wxfcs/all/%(datatype)s/%(location)s?%(params)s"

#get list of sites supported
def get_forecast_sitelist(key, datatype='json'):
    params = urllib.urlencode({'key' : key})
    substitute = {'datatype': datatype, 'params': params}
    url = BASE_URL + FORECAST_SITE_LIST_URL % substitute
    return retryurlopen(url)

#get capabilities
def get_forecast_capabilites(key, datatype='json'):
    params = urllib.urlencode({'key' : key})
    substitute = {'datatype': datatype, 'params': params}
    url = BASE_URL + FORECAST_CAPABILITIES_URL % substitute
    return retryurlopen(url)
    
#get weather forecast for a given location
def get_forecast(location, key, datatype='json', res='daily'):
    params = urllib.urlencode({'res': res, 'key' : key})
    substitute = {'datatype': datatype, 'location': location, 'params': params}
    url = BASE_URL + FORECAST_LOCATION_URL % substitute
    return retryurlopen(url)

#get current observations for a location
def get_observations(location, key, datatype='json', res='hourly'):
    params = urllib.urlencode({'res': res, 'key' : key})
    substitute = {'datatype': datatype, 'location': location, 'params': params}
    url = BASE_URL + OBSERVATION_LOCATION_URL % substitute
    return retryurlopen(url)
