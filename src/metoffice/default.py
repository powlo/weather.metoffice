import sys
import socket
socket.setdefaulttimeout(20)
import utilities, properties, urlcache
from constants import WINDOW, ADDON, API_KEY, CURRENT_VIEW, ADDON_DATA_PATH

@utilities.failgracefully
def main():
    if ADDON.getSetting('EraseCache') == 'true':
        try:
            urlcache.URLCache(ADDON_DATA_PATH).erase()
        finally:
            ADDON.setSetting('EraseCache', 'false')#@UndefinedVariable

    if not API_KEY:
        raise Exception('No API Key. Enter your Met Office API Key under settings.')

    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        properties.observation()
    if not CURRENT_VIEW:
        properties.daily()
    elif CURRENT_VIEW == '3hourly':
        properties.threehourly()
    elif CURRENT_VIEW == 'forecastmap':
        properties.forecastlayer()
    elif CURRENT_VIEW == 'observationmap':
        properties.observationlayer()
    elif CURRENT_VIEW == 'text':
        properties.text()

    WINDOW.setProperty('WeatherProvider', ADDON.getAddonInfo('name'))#@UndefinedVariable
    WINDOW.setProperty('ObservationLocation', ADDON.getSetting('ObservationLocation'))#@UndefinedVariable
    WINDOW.setProperty('ForecastLocation', ADDON.getSetting('ForecastLocation'))#@UndefinedVariable
    WINDOW.setProperty('RegionalLocation', ADDON.getSetting('RegionalLocation'))#@UndefinedVariable
    WINDOW.setProperty('Location1', ADDON.getSetting('ObservationLocation'))#@UndefinedVariable
    WINDOW.setProperty('Locations', '1')#@UndefinedVariable

if __name__ == '__main__':
    main()