import json
import time
from datetime import timedelta

import pytz
from PIL import Image

from . import astronomy, urlcache, utilities
from .constants import (
    ADDON_DATA_PATH,
    CROP_HEIGHT,
    CROP_WIDTH,
    DAILY_LOCATION_FORECAST_URL,
    DATAPOINT_DATE_FORMAT,
    DATAPOINT_DATETIME_FORMAT,
    FORECAST_LOCATION,
    FORECAST_LOCATION_ID,
    HOURLY_LOCATION_OBSERVATION_URL,
    ISSUEDAT_FORMAT,
    LATITUDE,
    LONGITUDE,
    OBSERVATION_LOCATION,
    OBSERVATION_LOCATION_ID,
    RAW_DATAPOINT_IMG_WIDTH,
    REGIONAL_LOCATION,
    REGIONAL_LOCATION_ID,
    SHORT_DATE_FORMAT,
    SHORT_DAY_FORMAT,
    TEMPERATUREUNITS,
    TEXT_FORECAST_URL,
    THREEHOURLY_LOCATION_FORECAST_URL,
    TIME_FORMAT,
    TZ,
    WEATHER_CODES,
    WINDOW,
)


def observation():
    utilities.log(
        "Fetching Hourly Observation for '%s (%s)' from the Met Office..."
        % (OBSERVATION_LOCATION, OBSERVATION_LOCATION_ID)
    )
    with urlcache.URLCache(ADDON_DATA_PATH) as cache:
        filename = cache.get(HOURLY_LOCATION_OBSERVATION_URL, observation_expiry)
        with open(filename) as fh:
            data = json.load(fh)
    try:
        dv = data["SiteRep"]["DV"]
        dataDate = utilities.strptime(
            dv.get("dataDate").rstrip("Z"), DATAPOINT_DATETIME_FORMAT
        ).replace(tzinfo=pytz.utc)
        WINDOW.setProperty(
            "HourlyObservation.IssuedAt",
            dataDate.astimezone(TZ).strftime(ISSUEDAT_FORMAT),
        )
        try:
            latest_period = dv["Location"]["Period"][-1]
        except KeyError:
            latest_period = dv["Location"]["Period"]
        try:
            latest_obs = latest_period["Rep"][-1]
        except KeyError:
            latest_obs = latest_period["Rep"]
        WINDOW.setProperty(
            "Current.Condition", WEATHER_CODES[latest_obs.get("W", "na")][1]
        )
        WINDOW.setProperty("Current.Visibility", latest_obs.get("V", "n/a"))
        WINDOW.setProperty("Current.Pressure", latest_obs.get("P", "n/a"))
        WINDOW.setProperty(
            "Current.Temperature",
            str(round(float(latest_obs.get("T", "n/a")))).split(".")[0],
        )
        WINDOW.setProperty("Current.FeelsLike", "n/a")
        # if we get Wind, then convert it to kmph.
        WINDOW.setProperty("Current.Wind", utilities.mph_to_kmph(latest_obs, "S"))
        WINDOW.setProperty("Current.WindDirection", latest_obs.get("D", "n/a"))
        WINDOW.setProperty("Current.WindGust", latest_obs.get("G", "n/a"))
        WINDOW.setProperty(
            "Current.OutlookIcon",
            "%s.png" % WEATHER_CODES[latest_obs.get("W", "na")][0],
        )
        WINDOW.setProperty(
            "Current.FanartCode", "%s.png" % WEATHER_CODES[latest_obs.get("W", "na")][0]
        )
        WINDOW.setProperty(
            "Current.DewPoint",
            str(round(float(latest_obs.get("Dp", "n/a")))).split(".")[0],
        )
        WINDOW.setProperty(
            "Current.Humidity",
            str(round(float(latest_obs.get("H", "n/a")))).split(".")[0],
        )

        WINDOW.setProperty("HourlyObservation.IsFetched", "true")

    except KeyError as e:
        e.args = (
            "Key Error in JSON File",
            "Key '{0}' not found while processing file from url:".format(e.args[0]),
            HOURLY_LOCATION_OBSERVATION_URL,
        )
        raise


def daily():
    utilities.log(
        "Fetching Daily Forecast for '%s (%s)' from the Met Office..."
        % (FORECAST_LOCATION, FORECAST_LOCATION_ID)
    )
    with urlcache.URLCache(ADDON_DATA_PATH) as cache:
        filename = cache.get(DAILY_LOCATION_FORECAST_URL, daily_expiry)
        with open(filename) as fh:
            data = json.load(fh)
    try:
        dv = data["SiteRep"]["DV"]
        dataDate = utilities.strptime(
            dv.get("dataDate").rstrip("Z"), DATAPOINT_DATETIME_FORMAT
        ).replace(tzinfo=pytz.utc)
        WINDOW.setProperty(
            "DailyForecast.IssuedAt", dataDate.astimezone(TZ).strftime(ISSUEDAT_FORMAT)
        )
        for p, period in enumerate(dv["Location"]["Period"]):
            WINDOW.setProperty(
                "Day%d.Title" % p,
                time.strftime(
                    SHORT_DAY_FORMAT,
                    time.strptime(period.get("value"), DATAPOINT_DATE_FORMAT),
                ),
            )
            WINDOW.setProperty(
                "Daily.%d.ShortDay" % (p + 1),
                time.strftime(
                    SHORT_DAY_FORMAT,
                    time.strptime(period.get("value"), DATAPOINT_DATE_FORMAT),
                ),
            )
            WINDOW.setProperty(
                "Daily.%d.ShortDate" % (p + 1),
                time.strftime(
                    SHORT_DATE_FORMAT,
                    time.strptime(period.get("value"), DATAPOINT_DATE_FORMAT),
                ),
            )
            for rep in period["Rep"]:
                weather_type = rep.get("W", "na")
                if rep.get("$") == "Day":
                    WINDOW.setProperty("Day%d.HighTemp" % p, rep.get("Dm", "na"))
                    WINDOW.setProperty("Day%d.HighTempIcon" % p, rep.get("Dm"))
                    WINDOW.setProperty(
                        "Day%d.Outlook" % p, WEATHER_CODES.get(weather_type)[1]
                    )
                    WINDOW.setProperty(
                        "Day%d.OutlookIcon" % p,
                        "%s.png" % WEATHER_CODES.get(weather_type, "na")[0],
                    )
                    WINDOW.setProperty("Day%d.WindSpeed" % p, rep.get("S", "na"))
                    WINDOW.setProperty(
                        "Day%d.WindDirection" % p, rep.get("D", "na").lower()
                    )

                    # "Extended" properties used by some skins.
                    WINDOW.setProperty(
                        "Daily.%d.HighTemperature" % (p + 1),
                        utilities.localised_temperature(rep.get("Dm", "na"))
                        + TEMPERATUREUNITS,
                    )
                    WINDOW.setProperty("Daily.%d.HighTempIcon" % (p + 1), rep.get("Dm"))
                    WINDOW.setProperty(
                        "Daily.%d.Outlook" % (p + 1), WEATHER_CODES.get(weather_type)[1]
                    )
                    WINDOW.setProperty(
                        "Daily.%d.OutlookIcon" % (p + 1),
                        "%s.png" % WEATHER_CODES.get(weather_type, "na")[0],
                    )
                    WINDOW.setProperty(
                        "Daily.%d.FanartCode" % (p + 1),
                        WEATHER_CODES.get(weather_type, "na")[0],
                    )
                    WINDOW.setProperty(
                        "Daily.%d.WindSpeed" % (p + 1), rep.get("S", "na")
                    )
                    WINDOW.setProperty(
                        "Daily.%d.WindDirection" % (p + 1), rep.get("D", "na").lower()
                    )

                elif rep.get("$") == "Night":
                    WINDOW.setProperty("Day%d.LowTemp" % p, rep.get("Nm", "na"))
                    WINDOW.setProperty("Day%d.LowTempIcon" % p, rep.get("Nm"))

                    WINDOW.setProperty(
                        "Daily.%d.LowTemperature" % (p + 1),
                        utilities.localised_temperature(rep.get("Nm", "na"))
                        + TEMPERATUREUNITS,
                    )
                    WINDOW.setProperty("Daily.%d.LowTempIcon" % (p + 1), rep.get("Nm"))

    except KeyError as e:
        e.args = (
            "Key Error in JSON File",
            "Key '{0}' not found while processing file from url:".format(e.args[0]),
            DAILY_LOCATION_FORECAST_URL,
        )
        raise

    WINDOW.setProperty("Daily.IsFetched", "true")


def threehourly():
    utilities.log(
        "Fetching 3 Hourly Forecast for '%s (%s)' from the Met Office..."
        % (FORECAST_LOCATION, FORECAST_LOCATION_ID)
    )
    with urlcache.URLCache(ADDON_DATA_PATH) as cache:
        filename = cache.get(THREEHOURLY_LOCATION_FORECAST_URL, threehourly_expiry)
        with open(filename) as fh:
            data = json.load(fh)
    try:
        dv = data["SiteRep"]["DV"]
        dataDate = utilities.strptime(
            dv.get("dataDate").rstrip("Z"), DATAPOINT_DATETIME_FORMAT
        ).replace(tzinfo=pytz.utc)
        WINDOW.setProperty(
            "3HourlyForecast.IssuedAt",
            dataDate.astimezone(TZ).strftime(ISSUEDAT_FORMAT),
        )
        count = 1
        for period in dv["Location"]["Period"]:
            for rep in period["Rep"]:
                # extra xbmc targeted info:
                weather_type = rep.get("W", "na")
                WINDOW.setProperty(
                    "Hourly.%d.Outlook" % count, WEATHER_CODES.get(weather_type)[1]
                )
                WINDOW.setProperty("Hourly.%d.WindSpeed" % count, rep.get("S", "n/a"))
                WINDOW.setProperty(
                    "Hourly.%d.WindDirection" % count, rep.get("D", "na").lower()
                )
                WINDOW.setProperty("Hourly.%d.GustSpeed" % count, rep.get("G", "n/a"))
                WINDOW.setProperty("Hourly.%d.UVIndex" % count, rep.get("U", "n/a"))
                WINDOW.setProperty(
                    "Hourly.%d.Precipitation" % count, rep.get("Pp") + "%"
                )
                WINDOW.setProperty(
                    "Hourly.%d.OutlookIcon" % count,
                    "%s.png" % WEATHER_CODES.get(weather_type, "na")[0],
                )
                WINDOW.setProperty(
                    "Hourly.%d.ShortDate" % count,
                    time.strftime(
                        SHORT_DATE_FORMAT,
                        time.strptime(period.get("value"), DATAPOINT_DATE_FORMAT),
                    ),
                )
                WINDOW.setProperty(
                    "Hourly.%d.Time" % count,
                    utilities.minutes_as_time(int(rep.get("$"))),
                )
                WINDOW.setProperty(
                    "Hourly.%d.Temperature" % count,
                    utilities.rownd(utilities.localised_temperature(rep.get("T", "na")))
                    + TEMPERATUREUNITS,
                )
                WINDOW.setProperty(
                    "Hourly.%d.ActualTempIcon" % count, rep.get("T", "na")
                )
                WINDOW.setProperty(
                    "Hourly.%d.FeelsLikeTemp" % count,
                    utilities.rownd(
                        utilities.localised_temperature(rep.get("F", "na"))
                    ),
                )
                WINDOW.setProperty(
                    "Hourly.%d.FeelsLikeTempIcon" % count, rep.get("F", "na")
                )
                count += 1
    except KeyError as e:
        e.args = (
            "Key Error in JSON File",
            "Key '{0}' not found while processing file from url:".format(e.args[0]),
            THREEHOURLY_LOCATION_FORECAST_URL,
        )
        raise
    WINDOW.setProperty("Hourly.IsFetched", "true")


def sunrisesunset():
    sun = astronomy.Sun(lat=float(LATITUDE), lng=float(LONGITUDE))
    WINDOW.setProperty("Today.Sunrise", sun.sunrise().strftime(TIME_FORMAT))
    WINDOW.setProperty("Today.Sunset", sun.sunset().strftime(TIME_FORMAT))


def text():
    utilities.log(
        "Fetching Text Forecast for '%s (%s)' from the Met Office..."
        % (REGIONAL_LOCATION, REGIONAL_LOCATION_ID)
    )
    with urlcache.URLCache(ADDON_DATA_PATH) as cache:
        filename = cache.get(TEXT_FORECAST_URL, text_expiry)
        with open(filename) as fh:
            data = json.load(fh)
    try:
        rf = data["RegionalFcst"]
        issuedat = utilities.strptime(
            rf["issuedAt"].rstrip("Z"), DATAPOINT_DATETIME_FORMAT
        ).replace(tzinfo=pytz.utc)
        WINDOW.setProperty(
            "TextForecast.IssuedAt", issuedat.astimezone(TZ).strftime(ISSUEDAT_FORMAT)
        )
        count = 0
        for period in rf["FcstPeriods"]["Period"]:
            # have to check type because json can return list or dict here
            if isinstance(period["Paragraph"], list):
                for paragraph in period["Paragraph"]:
                    WINDOW.setProperty(
                        "Text.Paragraph%d.Title" % count,
                        paragraph["title"].rstrip(":").lstrip("UK Outlook for"),
                    )
                    WINDOW.setProperty(
                        "Text.Paragraph%d.Content" % count, paragraph["$"]
                    )
                    count += 1
            else:
                WINDOW.setProperty(
                    "Text.Paragraph%d.Title" % count,
                    period["Paragraph"]["title"].rstrip(":").lstrip("UK Outlook for"),
                )

                WINDOW.setProperty(
                    "Text.Paragraph%d.Content" % count, period["Paragraph"]["$"]
                )
                count += 1
    except KeyError as e:
        e.args = (
            "Key Error in JSON File",
            "Key '{0}' not found while processing file from url:".format(e.args[0]),
            TEXT_FORECAST_URL,
        )
        raise
    WINDOW.setProperty("TextForecast.IsFetched", "true")


def daily_expiry(filename):
    with open(filename) as fh:
        data = json.load(fh)
    dataDate = data["SiteRep"]["DV"]["dataDate"].rstrip("Z")
    return utilities.strptime(dataDate, DATAPOINT_DATETIME_FORMAT) + timedelta(
        hours=1.5
    )


def threehourly_expiry(filename):
    with open(filename) as fh:
        data = json.load(fh)
    dataDate = data["SiteRep"]["DV"]["dataDate"].rstrip("Z")
    return utilities.strptime(dataDate, DATAPOINT_DATETIME_FORMAT) + timedelta(
        hours=1.5
    )


def text_expiry(filename):
    with open(filename) as fh:
        data = json.load(fh)
    issuedAt = data["RegionalFcst"]["issuedAt"].rstrip("Z")
    return utilities.strptime(issuedAt, DATAPOINT_DATETIME_FORMAT) + timedelta(hours=12)


def observation_expiry(filename):
    with open(filename) as fh:
        data = json.load(fh)
    dataDate = data["SiteRep"]["DV"]["dataDate"].rstrip("Z")
    return utilities.strptime(dataDate, DATAPOINT_DATETIME_FORMAT) + timedelta(
        hours=1.5
    )


def image_resize(filename):
    # remove the 'cone' from the image
    with Image.open(filename) as img:
        (width, height) = img.size
        if width == RAW_DATAPOINT_IMG_WIDTH:
            img.crop(
                (CROP_WIDTH, CROP_HEIGHT, width - CROP_WIDTH, height - CROP_HEIGHT)
            ).save(filename, img.format)
