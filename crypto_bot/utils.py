import datetime
import re


def get_timestamp(time):
    """Date format must be mm-dd-yyyy"""
    if not re.match("$\d{2}-\d{2}-\d{4}$", time):
        return False
    year, month, day = [int(x) for x in time.split("-")]
    try:
        date = datetime.datetime(year=year, month=month, day=day)
    except ValueError:
        return False
    return date.timestamp() / 1000
