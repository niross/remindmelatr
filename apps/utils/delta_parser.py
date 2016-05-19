from dateutil.relativedelta import *
from datetime import datetime, timedelta
import pytz
import re

PADDED = ["%02d" % x for x in range(0, 10)]
HOURS = PADDED + [x for x in range(0, 24)]
MORNING_HOURS = PADDED + [str(x) for x in HOURS if x < 13]
SECONDS = PADDED + [x for x in range(0, 60)]

def match_delta(term):
    """
    Find a time in a string

    Tries to match the following date styles

        * 1 minute
        * 1 hour
        * 1 day
        * 1 week
        * 1 month
        * 1 year
    """

    utc = pytz.timezone('UTC')
    now = datetime.now(utc)

    # 1 minute, 5 minutes
    str_match = re.compile(r'(\d+) minute(?:s)?', re.I)
    if str_match.match(term) is not None:
        match_group = str_match.match(term).group(1)
        return now + timedelta(minutes=int(match_group))

    # 1 hour, 5 hours
    str_match = re.compile(r'(\d+) hour(?:s)?', re.I)
    if str_match.match(term) is not None:
        match_group = str_match.match(term).group(1)
        return now + timedelta(hours=int(match_group))

    # 1 day, 5 days
    str_match = re.compile(r'(\d+) day(?:s)?', re.I)
    if str_match.match(term) is not None:
        match_group = str_match.match(term).group(1)
        return now + timedelta(days=int(match_group))

    # 1 week, 5 weeks
    str_match = re.compile(r'(\d+) week(?:s)?', re.I)
    if str_match.match(term) is not None:
        match_group = str_match.match(term).group(1)
        return now + timedelta(weeks=int(match_group))

    # 1 month, 5 months
    str_match = re.compile(r'(\d+) month(?:s)?', re.I)
    if str_match.match(term) is not None:
        match_group = str_match.match(term).group(1)
        return now + relativedelta(months=+int(match_group))

    # 1 year, 5 years
    str_match = re.compile(r'(\d+) year(?:s)?', re.I)
    if str_match.match(term) is not None:
        match_group = str_match.match(term).group(1)
        return now + relativedelta(years=+int(match_group))

    return None
