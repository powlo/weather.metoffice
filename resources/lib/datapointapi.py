#API for the Met Office's DataPoint API
#http://www.metoffice.gov.uk/datapoint
import urllib
import urllib2
import json
import httplib
from httplib import HTTP

BASE_URL = "http://datapoint.metoffice.gov.uk/public/data/"

OBSERVATION_SITE_LIST_URL      = "val/wxobs/all/%(datatype)s/sitelist?%(params)s"
OBSERVATION_CAPABILITIES_URL   = "val/wxobs/all/%(datatype)s/capabilities?%(params)s"
OBSERVATION_LOCATION_URL       = "val/wxobs/all/%(datatype)s/%(location)s?%(params)s"

FORECAST_SITE_LIST_URL         = "val/wxfcs/all/%(datatype)s/sitelist?%(params)s"
FORECAST_CAPABILITIES_URL      = "val/wxfcs/all/%(datatype)s/capabilities?%(params)s"
FORECAST_LOCATION_URL          = "val/wxfcs/all/%(datatype)s/%(location)s?%(params)s"

DEFAULT_RESOLUTION = "daily"

class Datapoint(object):
    def __init__(self, key, res=DEFAULT_RESOLUTION):
        self.key = key
        self.res = res
        self.RETRY_MAX = 3
    
    def set_key(key):
        self.key = key
    
    def set_resolution(res):
        self.res = res
    
    #get list of sites supported
    def get_json_forecast_sitelist(self):
        retry = self.RETRY_MAX
        params = urllib.urlencode({'key' : self.key})
        substitute = {'datatype': 'json', 'params': params}
        url = BASE_URL + FORECAST_SITE_LIST_URL % substitute
        while True:
            try:
                response = urllib2.urlopen(url)
                data = response.read().decode('latin-1')
                break
            except:
                if retry:
                    retry -= 1
                else:
                    raise
        return json.loads(data)

    #get capabilities
    def get_json_capabilites(self):
        retry = self.RETRY_MAX
        params = urllib.urlencode({'key' : self.key})
        substitute = {'datatype': 'json', 'params': params}
        url = BASE_URL + FORECAST_SITE_LIST_URL % substitute
        while True:
            try:
                response = urllib2.urlopen(url)
                data = response.read()
                break
            except:
                if retry:
                    retry -= 1
                else:
                    raise
        return json.loads(data)    
        
    #get weather forecast for a given location
    #does forecast update over the day?
    def get_json_forecast(self, location):
        retry = self.RETRY_MAX
        params = urllib.urlencode({'res': self.res, 'key' : self.key})
        substitute = {'datatype': 'json', 'location': location, 'params': params}
        url = BASE_URL + FORECAST_LOCATION_URL % substitute
        while True:
            try:
                response = urllib2.urlopen(url)
                data = response.read()
                break
            except:
                if retry:
                    retry -= 1
                else:
                    raise
        return json.loads(data)

    #get current observations for a location
    def get_json_observations(self, location):
        retry = self.RETRY_MAX
        params = urllib.urlencode({'res': 'hourly', 'key' : self.key})
        substitute = {'datatype': 'json', 'location': location, 'params': params}
        url = BASE_URL + OBSERVATION_LOCATION_URL % substitute
        while True:
            try:
                response = urllib2.urlopen(url)
                data = response.read()
                break
            except:
                if retry:
                    retry -= 1
                else:
                    raise
        return json.loads(data)

###U R HERE  - Write code to fetch observation data