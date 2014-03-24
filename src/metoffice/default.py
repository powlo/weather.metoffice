import sys
import socket
socket.setdefaulttimeout(20)
import utilities, properties
from constants import WINDOW, ADDON, API_KEY

@utilities.failgracefully
def main():
    if not API_KEY:
        raise Exception('No API Key. Enter your Met Office API Key under settings.')

    if sys.argv[1].isdigit():
        properties.observation()
        properties.daily()
    elif sys.argv[1] == 'ForecastMap':
        properties.forecastlayer()
    elif sys.argv[1] == 'DailyForecast':
        properties.daily()
    elif sys.argv[1] == '3HourlyForecast':
        properties.threehourly()
    elif sys.argv[1] == 'TextForecast':
        properties.text()
    elif sys.argv[1] == 'HourlyObservation':
        properties.observation()

    WINDOW.setProperty('WeatherProvider', ADDON.getAddonInfo('name'))#@UndefinedVariable
    WINDOW.setProperty('ObservationLocation', ADDON.getSetting('ObservationLocation'))#@UndefinedVariable
    WINDOW.setProperty('ForecastLocation', ADDON.getSetting('ForecastLocation'))#@UndefinedVariable
    WINDOW.setProperty('RegionalLocation', ADDON.getSetting('RegionalLocation'))#@UndefinedVariable
    WINDOW.setProperty('Location1', ADDON.getSetting('ObservationLocation'))#@UndefinedVariable
    WINDOW.setProperty('Locations', '1')#@UndefinedVariable

if __name__ == '__main__':
    main()