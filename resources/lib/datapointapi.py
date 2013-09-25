#API for the Met Office's DataPoint API
#http://www.metoffice.gov.uk/datapoint
import urllib
import urllib2
from utilities import retryurlopen

#resource can be 'wxobs', 'wxfcs'
#format can be 'val', 'txt', 'image', 'layer'
#datatype can be 'json', 'xml'
#object can be 'sitelist', 'capabilties', \d+ (string of digits)
BASE_URL = "http://datapoint.metoffice.gov.uk/public/data/"
RESOURCE_URL = "%(format)s/%(resource)s/%(group)s/%(datatype)s/%(object)s?%(params)s"

SITELIST_TYPES = ['ForecastLocation', 'ObservationLocation', 'RegionalLocation']

#get data from datapoint
def url(format='val', resource='wxobs', group='all', datatype='json', object='sitelist', params={}):
    #todo: validate parameters
    get_params = urllib.urlencode(params)
    substitute = {'format': format,
                  'resource': resource,
                  'group': group,
                  'datatype': datatype,
                  'object': object,
                  'params': get_params}
    return BASE_URL + RESOURCE_URL % substitute

def parse_sitelist():
    #write a helper to disect the json data
    pass