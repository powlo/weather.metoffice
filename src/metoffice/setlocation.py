"""
Sets the forecast location by providing a keyboard prompt
to the user. The name entered by the user is searched in
site list. All matches are presented as a select list to
the user. On successful selection internal addon setting
is set.
"""
import sys
from datetime import datetime, timedelta
from operator import itemgetter

import xbmc #@UnresolvedImport
import xbmcgui #@UnresolvedImport
import xbmcaddon #@UnresolvedImport

from utils import datapoint, locator, urlcache, utilities

__addon__ = xbmcaddon.Addon(id='weather.metoffice')
API_KEY = __addon__.getSetting('ApiKey')
if not API_KEY:
    dialog = xbmcgui.Dialog()
    dialog.ok('No API Key', 'Enter your Met Office API Key under weather settings.')
    xbmc.log( 'No API Key', xbmc.LOGERROR)
    sys.exit(1)

GEOIP_PROVIDER = int(__addon__.getSetting('GeoIPProvider'))
if not GEOIP_PROVIDER:
    xbmc.log( 'No GeoIP Provider is set.')
    GEOIP_PROVIDER = 0

@utilities.xbmcbusy
def fetchandfilter(location, text):
    url = {'ForecastLocation' : datapoint.FORECAST_SITELIST_URL,
           'ObservationLocation': datapoint.OBSERVATION_SITELIST_URL,
           'RegionalLocation': datapoint.REGIONAL_SITELIST_URL}[location]
    url = url.format(key=API_KEY)

    with urlcache.URLCache(utilities.CACHE_FILE, utilities.CACHE_FOLDER) as cache:
        data = cache.jsonretrieve(url, datetime.now()+timedelta(weeks=1))
    sitelist = data['Locations']['Location']
    if location == 'RegionalLocation':
        for site in sitelist:
            #fix datapoint bug where keys start with @
            for key in site:
                if key.startswith('@'):
                    site[key[1:]] = site.pop(key)
            site['name'] = datapoint.LONG_REGIONAL_NAMES[site['name']]

    filtered = list()
    for site in sitelist:
        if site['name'].lower().find(text.lower()) != -1:
            filtered.append(site)

    if location != 'RegionalLocation':
        locator.distances(filtered, GEOIP_PROVIDER)
        for site in filtered:
            site['display'] = "{name} ({distance}km)".format(name=site['name'].encode('utf-8'),distance=site['distance'])
        filtered = sorted(filtered,key=itemgetter('distance'))
    else:
        for site in filtered:
            site['display'] = site['name']
        filtered = sorted(filtered,key=itemgetter('name'))
    return filtered

def main(location):

    keyboard = xbmc.Keyboard()
    keyboard.doModal()
    text= keyboard.isConfirmed() and keyboard.getText()
    dialog = xbmcgui.Dialog()
    sitelist = fetchandfilter(location, text)
    if sitelist == []:
        dialog.ok("No Matches", "No locations found containing '%s'" % text)
        xbmc.log( "No locations found containing '%s'" % text)
        return
    display_list = [site['display'] for site in sitelist]
    selected = dialog.select("Matching Sites", display_list)
    if selected != -1:
        __addon__.setSetting(location, sitelist[selected]['name'])
        __addon__.setSetting("%sID" % location, sitelist[selected]['id'])
        __addon__.setSetting("%sLatitude" % location, str(sitelist[selected].get('latitude')))
        __addon__.setSetting("%sLongitude" % location, str(sitelist[selected].get('longitude')))
        xbmc.log( "Setting '{location}' to '{name} ({distance})'".format(location=location,
                                                                     name=sitelist[selected]['name'].encode('utf-8'),
                                                                     distance=sitelist[selected]['id']))

if __name__ == '__main__':
    #check sys.argv
    main(sys.argv[1])
