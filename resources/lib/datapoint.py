#API for the Met Office's DataPoint API
#http://www.metoffice.gov.uk/datapoint
import urllib
import urllib2
from utilities import log

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
