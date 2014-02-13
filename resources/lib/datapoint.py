#API for the Met Office's DataPoint API
#http://www.metoffice.gov.uk/datapoint
import urllib
import urllib2
from utilities import retryurlopen, log

URL_TEMPLATE = "http://datapoint.metoffice.gov.uk/public/data/{format}/{resource}/{group}/{datatype}/{object}?{get}"

FORECAST_SITELIST_URL = URL_TEMPLATE.format(format='val', resource='wxfcs', group='all', datatype='json', object='sitelist', 
                                            get=urllib.unquote(urllib.urlencode((('key','{key}'),))))
OBSERVATION_SITELIST_URL = URL_TEMPLATE.format(format='val', resource='wxobs', group='all', datatype='json', object='sitelist',
                                            get=urllib.unquote(urllib.urlencode((('key','{key}'),))))
REGIONAL_SITELIST_URL = URL_TEMPLATE.format(format='txt', resource='wxfcs', group='regionalforecast', datatype='json', object='sitelist',
                                            get=urllib.unquote(urllib.urlencode((('key','{key}'),))))

DAILY_LOCATION_FORECAST_URL = URL_TEMPLATE.format(format='val', resource='wxfcs', group='all', datatype='json', object='{object}',
                                            get=urllib.unquote(urllib.urlencode((('res', 'daily'),('key','{key}')))))
THREEHOURLY_LOCATION_FORECAST_URL = URL_TEMPLATE.format(format='val', resource='wxfcs', group='all', datatype='json', object='{object}',
                                            get=urllib.unquote(urllib.urlencode((('res', '3hourly'),('key','{key}')))))
HOURLY_LOCATION_OBSERVATION_URL = URL_TEMPLATE.format(format='val', resource='wxobs', group='all', datatype='json', object='{object}',
                                            get=urllib.unquote(urllib.urlencode((('res', 'hourly'),('key','{key}')))))
REGIONAL_TEXT_URL = URL_TEMPLATE.format(format='txt', resource='wxfcs', group='regionalforecast', datatype='json', object='{object}',
                                            get=urllib.unquote(urllib.urlencode((('key','{key}'),))))
FORECAST_LAYER_CAPABILITIES_URL = URL_TEMPLATE.format(format='layer', resource='wxfcs', group='all', datatype='json', object='capabilities',
                                            get=urllib.unquote(urllib.urlencode((('key','{key}'),))))

LONG_REGIONAL_NAMES = {'os': 'Orkney and Shetland',
                       'he': 'Highland and Eilean Siar',
                       'gr': 'Grampian',
                       'ta': 'Tayside',
                       'st': 'Strathclyde',
                       'dg': 'Dumfries, Galloway, Lothian',
                       'ni': 'Northern Ireland',
                       'yh': 'Yorkshire and the Humber',
                       'ne': 'Northeast England',
                       'em': 'East Midlands',
                       'ee': 'East of England',
                       'se': 'London and Southeast England',
                       'nw': 'Northwest England',
                       'wm': 'West Midlands',
                       'sw': 'Southwest England',
                       'wl': 'Wales',
                       'uk': 'United Kingdom'}

def get_sitelist(location):
    log("Getting sitelist for '%s'" % location)
    url_params = {
        'ForecastLocation' : {'resource' : 'wxfcs'},
        'ObservationLocation' : {'resource' : 'wxobs'},
        'RegionalLocation' : {'resource' : 'wxfcs', 'format': 'txt', 'group' : 'regionalforecast'},
        }
    args = url_params[location]
    args.update({'params':{'key': API_KEY}})
    url = url(**args)
    log("URL: %s" % url)
    page = utilities.retryurlopen(url).decode('latin-1')
    data = json.loads(page)
    sitelist = data['Locations']['Location']
    if location == 'RegionalLocation':
        #bug in datapoint: sitelist requires cleaning for regional forecast
        sitelist = clean_sitelist(sitelist)
        #long names are more user friendly
        for site in sitelist:
            site['name'] = LONG_REGIONAL_NAMES[site['name']]
    return sitelist

def clean_sitelist(sitelist):
    """
    A bug in datapoint returns keys prefixed with '@'
    This func chops them out
    """
    new_sites = []
    new_site = {}

    for site in sitelist:
        for key in site:
           if key.startswith('@'):
               new_key = key[1:]
               new_site[new_key] = site[key]
        new_sites.append(new_site.copy())
    return new_sites

def filter_sitelist(text, sitelist):
    """
    Takes a list of dictionaries and returns only
    those entries whose 'name' key contains text
    """
    filteredsitelist = list()
    for x in sitelist:
        if x['name'].lower().find(text.lower()) != -1:
            filteredsitelist.append(x)
    return filteredsitelist

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