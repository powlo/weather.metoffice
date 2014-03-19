import math
import json
from datetime import datetime, timedelta

import utilities
from urlcache import URLCache

from constants import GEOIP_PROVIDERS, ADDON_DATA_PATH

def distances(sitelist, n=0):
    provider = GEOIP_PROVIDERS[n]
    url = provider['url']
    utilities.log("Calculating distances based on GeoIP data from %s" % url.split('/')[2].lstrip('www.'))
    utilities.log("URL: %s" % url)
    with URLCache(ADDON_DATA_PATH) as cache:
        with cache.get(url, lambda x: datetime.now()+timedelta(hours=1)) as fyle:
            geoip = json.load(fyle)
    #different geoip providers user different names for latitude, longitude
    providers_lat_name = provider['latitude']
    providers_long_name = provider['longitude']
    (geoip_lat, geoip_long) = (float(geoip[providers_lat_name]), float(geoip[providers_long_name]))
    for site in sitelist:
        site['distance'] = int(utilities.haversine_distance(geoip_lat, geoip_long, float(site['latitude']), float(site['longitude'])))
