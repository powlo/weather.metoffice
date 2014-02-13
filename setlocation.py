"""
Sets the forecast location by providing a keyboard prompt
to the user. The name entered by the user is searched in
site list. All matches are presented as a select list to
the user. On successful selection internal addon setting
is set.
"""
import sys
import json
from datetime import datetime, timedelta
from operator import itemgetter

import xbmc
import xbmcgui
import xbmcaddon

from resources.lib import datapoint, locator, urlcache, utilities
from resources.lib.utilities import log

def main(location):
    __addon__ = xbmcaddon.Addon(id='weather.metoffice')    
    API_KEY = __addon__.getSetting('ApiKey')
    if not API_KEY:
        dialog = xbmcgui.Dialog()
        dialog.ok('No API Key', 'Enter your Met Office API Key under weather settings.')
        log( 'No API Key', xbmc.LOGERROR)
        return

    GEOIP_PROVIDER = int(__addon__.getSetting('GeoIPProvider'))
    if not GEOIP_PROVIDER:
        log( 'No GeoIP Provider is set.')
        GEOIP_PROVIDER = 0

    keyboard = xbmc.Keyboard()
    keyboard.doModal()
    text= keyboard.isConfirmed() and keyboard.getText()
    dialog = xbmcgui.Dialog()
    
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
    for x in sitelist:
        if x['name'].lower().find(text.lower()) != -1:
            filtered.append(x)

    if filtered == []:
        dialog.ok("No Matches", "No locations found containing '%s'" % text)
        log( "No locations found containing '%s'" % text)
        return

    if location != 'RegionalLocation':
        for site in filtered:
            site['distance'] = locator.distance(float(site['latitude']), float(site['longitude']), GEOIP_PROVIDER)
        filtered = sorted(filtered,key=itemgetter('distance'))
        display_list = ["%s (%skm)" % (x['name'], x['distance']) for x in filtered]
    else:
        filtered = sorted(filtered,key=itemgetter('name'))
        display_list = [x['name'] for x in filtered]
    
    selected = dialog.select("Matching Sites", display_list)
    if selected != -1:
        __addon__.setSetting(location, filtered[selected]['name'])
        __addon__.setSetting("%sID" % location, filtered[selected]['id'])
        __addon__.setSetting("%sLatitude" % location, str(filtered[selected].get('latitude')))
        __addon__.setSetting("%sLongitude" % location, str(filtered[selected].get('longitude')))
        log( "Setting '%s' to '%s (%s)'" % (location, filtered[selected]['name'], filtered[selected]['id']))

if __name__ == '__main__':
    #check sys.argv
    main(sys.argv[1])
