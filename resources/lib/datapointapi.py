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
RESOURCE_URL = "%(format)s/%(resource)s/all/%(datatype)s/%(object)s?%(params)s"

#get data from datapoint
def request(format='val', resource='wxobs', datatype='json', object='sitelist', params={}):
    #todo: validate parameters
    get_params = urllib.urlencode(params)
    substitute = {'format': format,
                  'resource': resource,
                  'datatype': datatype,
                  'object': object,
                  'params': get_params}
    url = BASE_URL + RESOURCE_URL % substitute
    return retryurlopen(url)

def parse_sitelist():
    #write a helper to disect the json data
    pass