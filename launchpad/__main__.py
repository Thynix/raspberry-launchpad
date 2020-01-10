from papirus import PapirusTextPos
from dateutil.tz import tzlocal
from html.parser import HTMLParser
import datetime
import time
import requests
import defusedxml.ElementTree
from launchpad.sunrise import get_sunrise_sunset


def main():
    # TODO: load config from somewhere - config.py? Path from environment variable?
    # TODO: concept of ... pages? tabs? that are loaded in and registered.
    # TODO: instead of trying to use the tiny buttons on the papirus, is there
    #       like a row of 5 keyboard keys? maybe nice cherry switches.

    # TODO: Parameterize lat/long in config; this is Ann Arbor, MI.
    latitude = 42.22
    longitude = -83.74

    timezone = tzlocal()

    rotation = 180
    text = PapirusTextPos(autoUpdate=False, rotation=rotation)

    # TODO: Bitmap support requires using PapirusComposite instead of
    #       PapirusTextPos.
    text.AddText("Today is", 0, 0, size=17, Id="date")
    text.AddText("Startup...", 93, 20, size=19, Id="startup")
    text.AddText("\u2600rise:", 0, 35, size=23, Id="sunrise_label")
    text.AddText("\u2600set:", 0, 57, size=23, Id="sunset_label")
    text.AddText("", 87, 35, size=23, Id="sunrise")
    text.AddText("", 87, 57, size=23, Id="sunset")
    text.AddText("Temp", 0, 80, size=14, Id="temp")
    text.WriteAll()

    text.RemoveText("startup")

    first_display = True
    while True:
        today = datetime.date.today()

        # TODO: Accommodate lack of sunrise/sunset like as far north as
        #       Utqiaġvik - the city formerly known as Barrow, Alaska.
        #       get_sunrise_sunset() returns those as None.
        sunrise_time, sunset_time = get_sunrise_sunset(latitude, longitude,
                                                       today, timezone)

        text.UpdateText("date", "Today is {}".format(today.strftime("%A, %Y-%m-%d")))
        text.UpdateText("sunrise", sunrise_time.strftime("%I:%M %p"))
        text.UpdateText("sunset", sunset_time.strftime("%I:%M %p"))
        # For testing the longest English day name.
        #text.UpdateText("date", "Today is {}".format(today.strftime("Wednesday, %Y-%m-%d")))

        text.UpdateText("temp", "Temp {}".format(
            get_temperature_forecast(latitude, longitude)
        ))

        # Do a partial update on startup, and a full update each following hour.
        text.WriteAll(first_display)
        first_display = False

        # Wait until the next hour.
        now = datetime.datetime.now()
        next_hour = (now + datetime.timedelta(hours=1)).replace(microsecond=0, second=0, minute=0)
        wait_seconds = (next_hour - now).total_seconds()
        print("waiting {} seconds until next hour".format(wait_seconds))
        time.sleep(wait_seconds)
        # TODO: wait for button press?


def get_temperature_forecast(latitude, longitude):
    try:
        r = requests.get("https://forecast.weather.gov/MapClick.php",
                         params={
                             "lat": str(latitude),
                             "lon": str(longitude),
                             "unit": "0",
                             "lg": "english",
                             "FcstType": "dwml",
                         })
        if r.status_code != 200:
            print("failed to fetch forecast: {}".format(r.reason))
            return "?/?"

        root = defusedxml.ElementTree.fromstring(r.text)
        forecast = root.find("./data[@type='forecast']/parameters[@applicable-location='point1']")
        return "{}/{}/{}".format(
            todays_forecast(forecast, "minimum"),
            current_temperature(root),
            todays_forecast(forecast, "maximum"),
        )
    except requests.exceptions.RequestException as e:
        print("failed to fetch forecast: {}".format(e))
        return "!/!"


def todays_forecast(forecast, temp_type):
    return format_temp(forecast.find(
        "./temperature[@type='{}']".format(temp_type)
    ))


def current_temperature(root):
    current = root.find("./data[@type='current observations']"
                        "/parameters[@applicable-location='point1']")
    return format_temp(current.find("./temperature[@type='apparent']"))


def format_temp(temp):
    # Use first letter of unit as abbreviation.
    unit = temp.get("units")[0]
    value = temp.find("./value").text
    return "{} {}".format(value, unit)


def parse_time(time_in):
    time_int = int(time_in)
    return datetime.time(time_int // 100, time_int % 100)


class PreExtractor(HTMLParser):

    def __init__(self, convert_charrefs=True):
        super().__init__(convert_charrefs=convert_charrefs)
        self.is_pre = False
        self.pre_data = None

    def handle_starttag(self, tag, attrs):
        self.is_pre = (tag == "pre")

    def handle_data(self, data):
        # Take the contents of the first <pre> section.
        if not self.is_pre:
            return
        
        if self.pre_data is None:
            self.pre_data = data
        elif data.rstrip():
            print("Warn: found multiple non-empty <pre> sections")

    def error(self, message):
        print("Parsing error: {}".format(message))
        exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Display abnormal errors, but not SystemExit or KeyboardInterrupt.
        # TODO: how to get config from here?
        text = PapirusTextPos(autoUpdate=False, rotation=180)
        text.AddText("Error {} {}: {}".format(
            datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p"),
            type(e).__name__,
            e,
        ))
        text.WriteAll(partialUpdate=True)
        raise
