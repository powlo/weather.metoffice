import sys
import socket
socket.setdefaulttimeout(20)
import utilities, properties
from constants import WINDOW, ADDON, API_KEY, CURRENT_VIEW

@utilities.failgracefully
def main():
    if not API_KEY:
        raise Exception('No API Key. Enter your Met Office API Key under settings.')

    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        #TODO: Examine Window.Property(Weather.CurrentView) to see what should be refreshed
        properties.observation()
        properties.daily()
    elif not CURRENT_VIEW:
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