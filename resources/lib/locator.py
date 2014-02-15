import json
import math
from datetime import datetime, timedelta

import xbmc

import utilities
from urlcache import URLCache

#This list must appear in the same order as it appears in 
#the settings.xml in order for the indexes to align.
GEOIP_PROVIDERS = [{'url':'http://ip-api.com/json/', 'latitude':'lat', 'longitude':'lon'},
             {'url':'http://freegeoip.net/json/', 'latitude':'latitude', 'longitude':'longitude'},
             {'url':'http://www.telize.com/geoip/','latitude':'latitude', 'longitude':'longitude'},
             {'url':'http://api.hostip.info/get_json.php?position=true','latitude':'lat', 'longitude':'lng'},
             {'url':'http://geoiplookup.net/geoapi.php?output=json', 'latitude':'latitude', 'longitude':'longitude'}
                   ]

def distance(site_lat, site_long, n=0):
    provider = GEOIP_PROVIDERS[n]
    url = provider['url']
    xbmc.log("Calculating distances based on GeoIP data from %s" % url.split('/')[2].lstrip('www.'))
    xbmc.log("URL: %s" % url)
    with URLCache(utilities.CACHE_FILE, utilities.CACHE_FOLDER) as cache:
        with open(cache.urlretrieve(url, datetime.now()+timedelta(hours=1))) as file:
            geoip = json.load(file)
    #different geoip providers user different names for latitude, longitude
    providers_lat_name = provider['latitude']
    providers_long_name = provider['longitude']
    (geoip_lat, geoip_long) = (float(geoip[providers_lat_name]), float(geoip[providers_long_name]))
    return int(haversine_distance(geoip_lat, geoip_long, site_lat, site_long))

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two coords
    using the haversine formula
    http://en.wikipedia.org/wiki/Haversine_formula
    """
    EARTH_RADIUS = 6371
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dlat = lat2-lat1
    dlon = lon2-lon1
    a = math.sin(dlat/2)**2 + \
        math.cos(lat1) * math.cos(lat2) * \
        math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return EARTH_RADIUS * c
