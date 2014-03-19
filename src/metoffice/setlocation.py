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

import locator, urlcache, utilities

from constants import API_KEY, ADDON_DATA_PATH, GEOIP_PROVIDER, KEYBOARD, DIALOG, ADDON, FORECAST_SITELIST_URL,\
                        OBSERVATION_SITELIST_URL, REGIONAL_SITELIST_URL, LONG_REGIONAL_NAMES

@utilities.xbmcbusy
def fetchandfilter(location, text):
    url = {'ForecastLocation' : FORECAST_SITELIST_URL,
           'ObservationLocation': OBSERVATION_SITELIST_URL,
           'RegionalLocation': REGIONAL_SITELIST_URL}[location]
    url = url.format(key=API_KEY)

    with urlcache.URLCache(ADDON_DATA_PATH) as cache:
        with cache.get(url, lambda x: datetime.now()+timedelta(weeks=1)) as fyle:
            data = json.load(fyle)
    sitelist = data['Locations']['Location']
    if location == 'RegionalLocation':
        for site in sitelist:
            #fix datapoint bug where keys start with @
            for key in site:
                if key.startswith('@'):
                    site[key[1:]] = site.pop(key)
            site['name'] = LONG_REGIONAL_NAMES[site['name']]

    filtered = list()
    for site in sitelist:
        if site['name'].lower().find(text.lower()) != -1:
            filtered.append(site)

    if location != 'RegionalLocation':
        locator.distances(filtered, int(GEOIP_PROVIDER))
        for site in filtered:
            site['display'] = "{name} ({distance}km)".format(name=site['name'].encode('utf-8'),distance=site['distance'])
        filtered = sorted(filtered,key=itemgetter('distance'))
    else:
        for site in filtered:
            site['display'] = site['name']
        filtered = sorted(filtered,key=itemgetter('name'))
    return filtered

@utilities.failgracefully
def main(location):
    if not API_KEY:
        raise Exception('No API Key. Enter your Met Office API Key under settings.')

    KEYBOARD.doModal()#@UndefinedVariable
    text= KEYBOARD.isConfirmed() and KEYBOARD.getText()#@UndefinedVariable
    sitelist = fetchandfilter(location, text)
    if sitelist == []:
        DIALOG.ok("No Matches", "No locations found containing '%s'" % text)#@UndefinedVariable
        utilities.log( "No locations found containing '%s'" % text)
        return
    display_list = [site['display'] for site in sitelist]
    selected = DIALOG.select("Matching Sites", display_list)#@UndefinedVariable
    if selected != -1:
        ADDON.setSetting(location, sitelist[selected]['name'])#@UndefinedVariable
        ADDON.setSetting("%sID" % location, sitelist[selected]['id'])#@UndefinedVariable
        ADDON.setSetting("%sLatitude" % location, str(sitelist[selected].get('latitude')))#@UndefinedVariable
        ADDON.setSetting("%sLongitude" % location, str(sitelist[selected].get('longitude')))#@UndefinedVariable
        utilities.log( "Setting '{location}' to '{name} ({distance})'".format(location=location,
                                                                     name=sitelist[selected]['name'].encode('utf-8'),
                                                                     distance=sitelist[selected]['id']))

if __name__ == '__main__':
    #check sys.argv
    main(sys.argv[1])
