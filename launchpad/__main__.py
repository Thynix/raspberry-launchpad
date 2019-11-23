from papirus import PapirusTextPos
from html.parser import HTMLParser
from io import StringIO
import os.path
import pickle
import datetime
import time
import requests
import defusedxml.ElementTree


def main():
    # TODO: load config from somewhere - config.py? Path from environment variable?
    # TODO: concept of ... pages? tabs? that are loaded in and registered.
    # TODO: instead of trying to use the tiny buttons on the papirus, is there
    #       like a row of 5 keyboard keys? maybe nice cherry switches.

    # TODO: make data directory, state, place configurable.
    # TODO: break into sunrise/sunset launchpad page module
    state = "MI"
    city = "Ann Arbor"

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

    sun_data = None
    first_display = True
    while True:
        today = datetime.date.today()
        year = today.year
        if sun_data is None or today not in sun_data:
            sun_data = load_sun_data(year, state, city)
        
        # This all assumes the sun data is specified in a non-DST variant of
        # the local timezone.
        today_data = sun_data[today]
        sunrise_time = today_data["sunrise"]
        sunset_time = today_data["sunset"]

        # Add one hour for daylight savings time.
        #
        # From the struct_time documentation:
        # > tm_isdst may be set to 1 when daylight savings time is in effect, and 0 when it is not.
        is_dst = time.localtime().tm_isdst == 1
        if is_dst:
            sunrise_time = sunrise_time.replace(hour=sunrise_time.hour + 1)
            sunset_time = sunset_time.replace(hour=sunset_time.hour + 1)

        text.UpdateText("date", "Today is {}".format(today.strftime("%A, %Y-%m-%d")))
        text.UpdateText("sunrise", sunrise_time.strftime("%I:%M %p"))
        text.UpdateText("sunset", sunset_time.strftime("%I:%M %p"))
        # For testing the longest English day name.
        #text.UpdateText("date", "Today is {}".format(today.strftime("Wednesday, %Y-%m-%d")))

        text.UpdateText("temp", "Temp {}".format(get_temperature_forecast()))

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


def get_temperature_forecast():
    # TODO: Parameterize lat/long in config
    try:
        r = requests.get("https://forecast.weather.gov/MapClick.php",
                         params={
                             "lat": "42.2171",
                             "lon": "-83.7391",
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


def load_sun_data(year, state, city):
    sun_data_dir = "/home/pi/raspberry-launchpad/sun-data/"
    base_filename = "{year} {state} {city}".format(year=year, state=state, city=city)
    pickle_path = os.path.join(sun_data_dir, base_filename + ".pickle")
    raw_path = os.path.join(sun_data_dir, base_filename + ".txt")

    try:
        # TODO: logging library instead of printing?
        print("loading sun data from cache at {}".format(pickle_path))
        sun_data = pickle.load(open(pickle_path, "rb"))
    except FileNotFoundError:
        # TODO: Also handle pickle loading failure?
        print("sun data cache not found")
        sun_data = download_sun_data(year, state, city, raw_path)
        pickle.dump(sun_data, open(pickle_path, "wb"))

    print("loaded")
    return sun_data


def download_sun_data(year, state, city, raw_path):
    # TODO: download instead of taking raw_path
    parser = PreExtractor()
    # TODO: load data from online if file not already present. 
    parser.feed(open(raw_path).read())
    parser.close()

    if parser.pre_data is None:
        print("<pre> section with sun data not found.")
        # TODO: instead give ?s for values or something
        exit(1)

    # The expected <pre> section contains header and footer lines; omit them.
    pre_lines = parser.pre_data.splitlines(keepends=True)[10:-3]

    # Remove the first column - it is just day number.
    trimmed_pre = ""
    for line in pre_lines:
        trimmed_pre += line.split(maxsplit=1)[1]

    # This import takes a long time - (over 10 seconds on this Raspberry Pi
    # Zero W) - so only do it when necessary.
    print("importing pandas and numpy; hold on...")
    start = time.monotonic()
    import pandas as pd
    import numpy as np
    print("import took {}".format(time.monotonic() - start))

    # TODO: engine="c" and dtype=int raises an exception. What am I missing?
    sun_fwf = pd.read_fwf(StringIO(trimmed_pre), header=None)
    # Return as non-pandas datatype to allow loading it from the pickle cache
    # without loading pandas.
    # Each column has up to 31 rows, and alternates sunrise and sunset for
    # successive months of the year.
    sun_dict = sun_fwf.to_dict()
    sun_data = dict()
    for column_number in range(0, 24, 2):
        for row_number in range(31):
            # If a day doesn't exist in a month, it is specified as NaN. Assert
            # that the pair relationship between columns holds.
            if np.isnan(sun_dict[column_number][row_number]):
                assert np.isnan(sun_dict[column_number + 1][row_number])
                continue

            assert not np.isnan(sun_dict[column_number + 1][row_number])

            day_number = row_number + 1
            month_number = (column_number + 2) // 2
            try:
                sun_date = datetime.date(year, month_number, day_number)
            except ValueError as e:
                # TODO: resolve the isnan check - it's not working properly.
                # A day invalid for the month is NaN and raises an exception.
                print("Warning: input data defined times for month {} day {}, "
                      "which datetime.date considers invalid: {}".format(
                          month_number, day_number, e))
                continue

            sun_data[sun_date] = {
                "sunrise": parse_time(sun_dict[column_number][row_number]),
                "sunset": parse_time(sun_dict[column_number + 1][row_number]),
            }

    return sun_data


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
