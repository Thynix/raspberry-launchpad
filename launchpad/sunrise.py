from skyfield import api

ts = api.load.timescale()
e = api.load('de421.bsp')

from skyfield import almanac


def get_sunrise_sunset(latitude, longitude, date, timezone):
    """
    :type timezone: datetime.tzinfo
    :type date: datetime.date
    :type latitude: float
    :type longitude: float
    :return Tuple of datetime (sunrise, sunset), or None instead of a datetime
            if it doesn't occur that day.
    """
    # TODO: 4 AM is used in the documentation, but does it work everywhere?
    #       https://rhodesmill.org/skyfield/almanac.html#sunrise-and-sunset
    t0 = ts.utc(date.year, date.month, date.day, 4)
    t1 = ts.utc(date.year, date.month, date.day + 1, 4)

    location = api.Topos(latitude_degrees=latitude, longitude=longitude)

    # The result t will be an array of times, and y will be True if the sun
    # rises at the corresponding time and False if it sets.
    times, are_sunrise = almanac.find_discrete(t0, t1, almanac.sunrise_sunset(e, location))

    sunrise = None
    sunset = None
    for time, is_sunrise in zip(times, are_sunrise):
        if is_sunrise:
            # Not expecting multiple sunrises per day.
            assert sunrise is None
            sunrise = time.astimezone(timezone)
        else:
            # Not expecting multiple sunsets per day.
            assert sunset is None
            sunset = time.astimezone(timezone)

    return sunrise, sunset
