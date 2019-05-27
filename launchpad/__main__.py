from papirus import PapirusTextPos
from html.parser import HTMLParser
from io import StringIO
import subprocess
import os.path
import pickle
import datetime
import time


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
    text.AddText("\u2600rise:", 0, 0, Id="sunrise_label")
    text.AddText("\u2600set:", 0, 20, Id="sunset_label")
    text.AddText("", 80, 0, Id="sunrise")
    text.AddText("", 80, 20, Id="sunset")
    text.AddText("Today is", 0, 42, size=17, Id="date")
    text.AddText("Starting up...", 0, 60, Id="startup")
    text.AddText("up", 0, 78, size=17, Id="uptime")
    text.WriteAll()

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

        text.RemoveText("startup")
        text.UpdateText("sunrise", sunrise_time.strftime("%I:%M %p"))
        text.UpdateText("sunset", sunset_time.strftime("%I:%M %p"))
        text.UpdateText("date", "Today is {}".format(today.strftime("%A, %Y-%m-%d")))
        # For testing the longest English day name.
        #text.UpdateText("date", "Today is {}".format(today.strftime("Wednesday, %Y-%m-%d")))

        try:
            uptime_process = subprocess.run(["uptime", "--pretty"], stdout=subprocess.PIPE)
            text.UpdateText("uptime", uptime_process.stdout.decode("utf8"))
        except subprocess.CalledProcessError as e:
            text.UpdateText("uptime", "uptime error {}".format(e.returncode))

        # Do a partial update on startup, and a full update each midnight.
        text.WriteAll(first_display)
        first_display = False

        # Wait until the next hour.
        now = datetime.datetime.now()
        next_hour = (now + datetime.timedelta(hours=1)).replace(microsecond=0, second=0, minute=0)
        wait_seconds = (next_hour - now).total_seconds()
        print("waiting {} seconds until next hour".format(wait_seconds))
        time.sleep(wait_seconds)
        # TODO: wait for button press?


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
        for day_number in range(31):
            # If a day doesn't exist in a month, it is specified as NaN. Assert
            # that the pair relationship between columns holds.
            if np.isnan(sun_dict[column_number][day_number]):
                assert np.isnan(sun_dict[column_number + 1][day_number])
                continue

            assert not np.isnan(sun_dict[column_number + 1][day_number])

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
                "sunrise": parse_time(sun_dict[column_number][day_number]),
                "sunset": parse_time(sun_dict[column_number + 1][day_number]),
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
