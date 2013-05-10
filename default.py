#Get some API stuff working outside XBMC
#Eg fetch list of Locations

import xbmc
import xbmcgui
import xbmcaddon
import os
from datetime import datetime
import time
import sys

label = xbmc.getInfoLabel('Weather.Location')

### addon info
__addon__       = xbmcaddon.Addon()
__addonid__     = __addon__.getAddonInfo('id')
__addonname__   = __addon__.getAddonInfo('name')
__author__      = __addon__.getAddonInfo('author')
__version__     = __addon__.getAddonInfo('version')
__addonpath__   = __addon__.getAddonInfo('path')
__resource__    = os.path.join( __addonpath__, 'resources', 'lib' )

sys.path.append(__resource__)

#Whats the use in passing in a location int to the script?
#How do we know which location is selected?

#We can now import from local lib dir
#Need to think about whether this fudging is a good thing
import utilities
from datapointapi import Datapoint

WEATHER_WINDOW_ID = 12600
WEATHER_WINDOW  = xbmcgui.Window(WEATHER_WINDOW_ID)
API_KEY = __addon__.getSetting('ApiKey')
weather = Datapoint(API_KEY)

def set_window_locations():
    locations = 0
    for count in range(1, 4):
        loc_name = __addon__.getSetting('Location%s' % count)
        if loc_name != '':
            locations += 1
        else:
            __addon__.setSetting('Location%sid' % count, '')
        WEATHER_WINDOW.setProperty('Location%s' % count, loc_name)
    WEATHER_WINDOW.setProperty('Locations', str(locations))

def display_forecast(location):
    set_window_locations()
    #clear display
    clear = utilities.clear()
    for field, value in clear.iteritems():
        WEATHER_WINDOW.setProperty(field, value)
    
    #Get five day forecast:
    locationid = __addon__.getSetting('Location%sid' % location)    
    data = weather.get_json_forecast(locationid)
    report = utilities.parse_json_day_forecast(data)
    for day, forecast in report.iteritems():
        for field, value in forecast.iteritems():
            WEATHER_WINDOW.setProperty('%s.%s' % (day, field), value)
    
    #get current forecast based on the same data
    report = utilities.parse_json_current_forecast(data)
    for field, value in report.iteritems():
        WEATHER_WINDOW.setProperty(field, value)

    #Get observations:
    #data = weather.get_json_observations(OBSERVATION_ID)
    #observation = utilities.parse_json_observations(data)
    #for field, value in observation.iteritems():
    #    WEATHER_WINDOW.setProperty(field, value)
    
def match_name(text, sitelist):
    locations = list()
    ids = list()
    for x in sitelist['Locations']['Location']:
        if x['name'].lower().find(text.lower()) != -1:
            locations.append(x['name'])
            ids.append(x['id'])
    return locations, ids
    
def find_location():
    keyboard = xbmc.Keyboard()
    keyboard.doModal()
    if (keyboard.isConfirmed() and keyboard.getText() != ''):
        text = keyboard.getText()
        xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        sitelist = weather.get_json_forecast_sitelist()
        locations, ids = match_name(text, sitelist)
        xbmc.executebuiltin( "Dialog.Close(busydialog)" )
        
        dialog = xbmcgui.Dialog()
        if locations != []:
            selected = dialog.select("Matching Locations", locations)
            if selected != -1:
                __addon__.setSetting(sys.argv[1], locations[selected])
                __addon__.setSetting(sys.argv[1] + 'id', ids[selected])
        else:
            dialog.ok("No Matches", "No locations found containing '%s'" % text)
    
if sys.argv[1].startswith('Location'):
    find_location()
else:
    #assume sys.arv[1] is string(int) representing desired location
    display_forecast(sys.argv[1])

WEATHER_WINDOW.setProperty('WeatherProvider', __addonname__)
