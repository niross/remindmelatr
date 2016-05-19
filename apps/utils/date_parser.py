import calendar
import traceback
from dateutil.relativedelta import *
import dateutil.parser
from dateutil.easter import easter
from datetime import datetime, timedelta
import pytz
import re

from django.utils import timezone

DATE_FORMAT = '%a, %d %b %Y %H:%M:%S %Z'
WEEKDAYS = [
    'monday', 'tuesday', 'wednesday', 'thursday',
    'friday', 'saturday', 'sunday'
]
SHORT_WEEKDAYS = {
    'mon': 'monday',
    'tue': 'tuesday',
    'tues': 'tuesday',
    'wed': 'wednesday',
    'weds': 'wednesday',
    'thur': 'thursday',
    'thurs': 'thursday',
    'fri': 'friday',
    'sat': 'saturday',
    'satday': 'saturday',
    'sun': 'sunday',
}
WEEK_TO_NUM = {
    'monday': 0, 'mon': 0, 'tuesday': 1, 'tue': 1, 'tues': 1, 'wednesday': 2,
    'wed': 2, 'weds': 2, 'thursday': 3, 'thur': 3, 'thurs': 3, 'friday': 4,
    'fri': 4, 'saturday': 5, 'sat': 5, 'satday': 5, 'sunday': 6, 'sun': 6
}
MONTH_TO_NUM = {
    'january': 1,
    'jan': 1,
    'february': 2,
    'feb': 2,
    'march': 3,
    'mar': 3,
    'april': 4,
    'apr': 4,
    'may': 5,
    'june': 6,
    'jun': 6,
    'july': 7,
    'jul': 7,
    'august': 8,
    'aug': 9,
    'september': 9,
    'sep': 9,
    'sept': 9,
    'october': 10,
    'oct': 10,
    'november': 11,
    'nov': 11,
    'december': 12,
    'dec': 12
}
NUM_STRINGS = {
    'one': 1,
    'first': 1,
    'two': 2,
    'second': 2,
    'three': 3,
    'third': 3,
    'four': 4,
    'fourth': 5,
    'five': 5,
    'fifth': 5,
    'six': 6,
    'sixth': 6,
    'seven': 7,
    'seventh': 8,
    'eight': 8,
    'eighth': 8,
    'nine': 9,
    'ninth': 9,
    'ten': 10,
    'tenth': 10,
}


def match_date(term):
    """
    Match a string with a date range

    Returns start and end date (inclusive)

    Only works with an exact match for now but should
    look into matching the string partially

    If a match is found it returns the term with the matching values removed

    Tries to match the following date styles

        * today
        * tomorrow
        * 25 april or 25 apr
        * april 25 or 25 apr
        * 30/01/2001
        * 01/30/2001
        * 30/01/01
        * 01/30/01
        * 25th
        * any weekday
        * next weekend
        * next week
        * next WEEKDAY
    """

    tz = pytz.timezone(timezone.get_current_timezone_name())
    now = datetime.now(tz)
    one_day = timedelta(days=1)

    # sort the months by length descending for matching in the regex later on
    sorted_months = sorted(MONTH_TO_NUM, key=lambda m: -len(m))
    month_match = '(?:\.)?|'.join(sorted_months) + '(?:\.)?'

    week_match = '\\b' + '\\b|\\b'.join(WEEKDAYS) + '\\b'

    short_weekdays = [k for k, v in SHORT_WEEKDAYS.iteritems()]
    short_week_match = '\\b' + '\\b|\\b'.join(short_weekdays) + '\\b'

    # Easter Sunday
    if re.match('.*?easter sunday.*?', term.lower(), re.I) is not None:
        e = easter(now.year)
        clean = trim(re.sub('easter sunday', '', term, re.I))
        d = datetime(now.year, e.month, e.day).replace(tzinfo=pytz.UTC)
        return d.date(), clean

    # Good Friday
    str_match = re.compile('.*?(good friday).*?', re.I)
    if str_match.match(term.lower()) is not None:
        match_group = str_match.match(term.lower()).group(1)
        e = easter(now.year) - timedelta(days=2)
        clean = trim(re.sub('good friday', '', term, re.I))
        d = datetime(now.year, e.month, e.day).replace(tzinfo=pytz.UTC)
        return d.date(), clean

    # Today/Tonight
    str_match =  re.compile('.*?(today|tonight|this evening|tonite).*?', re.I)
    if str_match.match(term.lower()) is not None:
        match_group = str_match.match(term.lower()).group(1)
        clean = trim(re.sub(match_group, '', term, re.I))
        return now.date(), clean

    # Tomorrow
    str_match =  re.compile(
        r'.*?(\btomorrow\b|\btmrw\b|\b2morrow\b|\b2mrw\b).*?', re.I
    )
    if str_match.match(term.lower()) is not None:
        match_group = str_match.match(term.lower()).group(1)
        start = now+one_day
        clean = trim(re.sub(match_group, '', term, re.I))
        return start.date(), clean

    # Next weekday
    str_match = re.compile('.*?(next ('+week_match+')).*?', re.I)
    if str_match.match(term):
        match_group = str_match.match(term).group(2)
        clean = trim(re.sub(str_match.match(term).group(1), '', term, re.I))
        start = get_next_weekday(match_group.lower())
        return start.date(), clean

    # Next short weekday
    str_match = re.compile('.*?(next ('+short_week_match+')).*?', re.I)
    if str_match.match(term):
        match_group = str_match.match(term).group(2)
        clean = trim(re.sub(str_match.match(term).group(1), '', term, re.I))
        start = get_next_weekday(match_group.lower())
        return start.date(), clean

    # This weekday
    str_match = re.compile('.*?(?:this )?('+week_match+').*?', re.I)
    if str_match.match(term):
        match_group = str_match.match(term).group(1)
        clean = trim(re.sub('(?:this )?%s' % match_group, '', term, re.I))
        try:
            start = dateutil.parser.parse(
                match_group.lower()
            ).replace(tzinfo=tz)
            if start.date() == now.date():
                start = start + timedelta(days=7)
            return start.date(), clean
        except ValueError, e:
            print "Error creating date from string %s - %s" % (term, e)

    # This short weekday
    str_match = re.compile('.*?(?:this )?('+short_week_match+').*?', re.I)
    if str_match.match(term):
        match_group = str_match.match(term).group(1)
        clean = trim(re.sub('(?:this )?%s' % match_group, '', term, re.I))
        try:
            start = dateutil.parser.parse(
                SHORT_WEEKDAYS[match_group.lower()]
            ).replace(tzinfo=tz)
            if start.date() == now.date():
                start = start + timedelta(days=7)
            return start.date(), clean
        except ValueError, e:
            print "Error creating date from string %s - %s" % (term, e)

    # 25 April 2014
    str_match = re.compile(
        r'.*?((\d+)(?: +)(\b'+month_match+'\b)(?: +)(\d+)).*?', re.I
    )
    if str_match.match(term):
        m = str_match.match(term)
        year = m.group(4)
        clean = trim(re.sub(m.group(1), '', term, re.I))
        try:
            start = dateutil.parser.parse(
                m.group(1).lower()
            ).replace(tzinfo=tz)
        except ValueError, e:
            print "Error creating date from string %s - %s" % (term, e)
        else:
            if year == now.year and start < now:
                start = datetime(now.year + 1, now.month, now.day)
            return start.date(), clean

    # April 25 2014
    str_match = re.compile(
        r'.*?((\b'+month_match+'\b)(?: +)(\d+)(?: +)(\d+)).*?', re.I
    )
    if str_match.match(term):
        m = str_match.match(term)
        year = m.group(4)
        clean = trim(re.sub(m.group(1), '', term, re.I))
        try:
            start = dateutil.parser.parse(
                m.group(1).lower()
            ).replace(tzinfo=tz)
        except ValueError, e:
            print "Error creating date from string %s - %s" % (term, e)
        else:
            if year == now.year and start < now:
                start = datetime(now.year + 1, now.month, now.day)
            return start.date(), clean

    # 25 April
    str_match = re.compile(r'.*?((\d+)(?: +)(\b'+month_match+'\b)).*?', re.I)
    if str_match.match(term):
        m = str_match.match(term)
        day = int(m.group(2))
        month = int(MONTH_TO_NUM[m.group(3).lower()])
        year = now.year
        clean = trim(re.sub(m.group(1), '', term, re.I))
        try:
            start = dateutil.parser.parse(
                m.group(1).lower()
            ).replace(tzinfo=tz)
        except ValueError, e:
            print "Error creating date from string %s - %s" % (term, e)
        else:
            if year == now.year and start < now:
                start = datetime(now.year + 1, month, day)
            return start.date(), clean

    # April 25
    str_match = re.compile(r'.*?((\b'+month_match+'\b)(?: +)(\d+)).*?', re.I)
    if str_match.match(term):
        m = str_match.match(term)
        day = int(m.group(3))
        month = int(MONTH_TO_NUM[m.group(2).lower()])
        year = now.year
        clean = trim(re.sub(m.group(1), '', term, re.I))
        try:
            start = dateutil.parser.parse(
                m.group(1).lower()
            ).replace(tzinfo=tz)
        except ValueError, e:
            print "Error creating date from string %s - %s" % (term, e)
        else:
            if year == now.year and start < now:
                start = datetime(now.year + 1, month, day)
            return start.date(), clean

    # 25 April or April 25 or 25/04/12 or 25th
    str_match = re.compile(
        '.*?(\d+(?:th|nd|rd|st)?(?: +)(?:\b{}\b)(?: \d+)?).*?|'
        '.*?((?:\b{}\b) \d+(?: \d+)?).*?'.format(
            month_match, month_match
        ),
        re.I
    )
    if str_match.match(term):
        if str_match.match(term).group(1) is not None:
            match_group = str_match.match(term).group(1)
        else:
            match_group = str_match.match(term).group(2)

        clean = trim(re.sub(match_group, '', term, re.I))

        # Try parsing uk date first
        try:
            start = dateutil.parser.parse(
                match_group.lower(), dayfirst=True
            ).replace(tzinfo=tz)
        except ValueError:
            # If not try US style
            try:
                start = dateutil.parser.parse(
                    match_group.lower()
                ).replace(tzinfo=tz)
            except ValueError:
                start = None

        if start is not None:
            if start < now:
                start = datetime(now.year + 1, now.month, now.day)
            return start.date(), clean

    # 25/12 or 12/25
    str_match = re.compile('.*?((\d+)[/|-](\d+)(?:[/|-](\d+))?).*?', re.I)
    if str_match.match(term.lower()):
        match_group = str_match.match(term.lower())
        clean = trim(re.sub(match_group.group(1), '', term, re.I))
        try:
            start = dateutil.parser.parse(
                match_group.group(1), dayfirst=True
            ).replace(tzinfo=tz)
            return start.date(), clean
        except ValueError, e:
            try:
                start = dateutil.parser.parse(
                    match_group.group(1)
                ).replace(tzinfo=tz)
                return start.date(), clean
            except ValueError, e:
                print "Error creating date from string %s - %s" % (term, e)

    # First Jan or Jan First
    num_strings = '|'.join([x for x in NUM_STRINGS])
    str_match = re.compile(
        r'.*?(('+num_strings+') ('+month_match+').*?|'
        '.*?('+month_match+') ('+num_strings+')).*?',
        re.I
    )
    if str_match.match(term) is not None:
        match_group = str_match.match(term)
        if match_group.group(2) is not None:
            dayfirst = True
            day = NUM_STRINGS[match_group.group(2).lower()]
            month = MONTH_TO_NUM[match_group.group(3).lower()]
        else:
            dayfirst = False
            month = MONTH_TO_NUM[match_group.group(4).lower()]
            day = NUM_STRINGS[match_group.group(5).lower()]
        start = dateutil.parser.parse('%s/%s' % (day, month),
                                      dayfirst=dayfirst).replace(tzinfo=tz)
        clean = trim(re.sub(match_group.group(1), '', term, re.I))
        if start < now:
            start = datetime(day=start.day, month=start.month,
                             year=start.year + 1).replace(tzinfo=tz)
        return start.date(), clean

    # Special days
    if re.match('.*?new years day.*?', term.lower(), re.I) is not None:
        start = datetime(now.year+1, 1, 1).replace(tzinfo=pytz.UTC)
        clean = trim(re.sub('new years day', '', term, re.I))
        return start.date(), clean

    str_match = re.match('.*?(new years(?: eve)?).*?', term.lower(), re.I)
    if str_match is not None:
        start = datetime(now.year, 12, 31).replace(tzinfo=pytz.UTC)
        clean = trim(re.sub(str_match.group(1), '', term, re.I))
        return start.date(), clean

    str_match =  re.compile('.*?(christmas day|xmas day).*?', re.I)
    if str_match.match(term.lower()) is not None:
        match_group = str_match.match(term.lower()).group(1)
        start = datetime(now.year, 12, 25).replace(tzinfo=pytz.UTC)
        if start < datetime.now(pytz.UTC):
            start = datetime(day=start.day, month=start.month,
                             year=start.year + 1).replace(tzinfo=pytz.UTC)
        clean = trim(re.sub(match_group, '', term, re.I))
        return start.date(), clean

    str_match =  re.compile('.*?(christmas eve|xmas eve).*?', re.I)
    if str_match.match(term.lower()) is not None:
        match_group = str_match.match(term.lower()).group(1)
        start = datetime(now.year, 12, 24).replace(tzinfo=pytz.UTC)
        if start < datetime.now(pytz.UTC):
            start = datetime(day=start.day, month=start.month,
                             year=start.year + 1).replace(tzinfo=pytz.UTC)
        clean = trim(re.sub(match_group, '', term, re.I))
        return start.date(), clean

    if re.match('.*?boxing day.*?', term.lower(), re.I) is not None:
        start = datetime(now.year, 12, 26).replace(tzinfo=pytz.UTC)
        if start < datetime.now(pytz.UTC):
            start = datetime(day=start.day, month=start.month,
                             year=start.year + 1).replace(tzinfo=pytz.UTC)
        clean = trim(re.sub('boxing day', '', term, re.I))
        return start.date(), clean

    if re.match('.*?valentines day.*?', term.lower(), re.I) is not None:
        start = datetime(now.year, 02, 14).replace(tzinfo=pytz.UTC)
        if start < datetime.now(pytz.UTC):
            start = datetime(day=start.day, month=start.month,
                             year=start.year + 1).replace(tzinfo=pytz.UTC)
        clean = trim(re.sub('valentines day', '', term, re.I))
        return start.date(), clean

    if re.match('.*?april fools day.*?', term.lower(), re.I) is not None:
        start = datetime(now.year, 04, 1).replace(tzinfo=pytz.UTC)
        if start < datetime.now(pytz.UTC):
            start = datetime(day=start.day, month=start.month,
                             year=start.year + 1).replace(tzinfo=pytz.UTC)
        clean = trim(re.sub('april fools day', '', term, re.I))
        return start.date(), clean

    # Last resort: 25th 3rd
    str_match = re.compile('.*?(\d+(?:th|nd|rd|st)).*?', re.I)
    if str_match.match(term.lower()):
        match_group = str_match.match(term.lower()).group(1)
        clean = trim(re.sub(match_group, '', term, re.I))
        try:
            start = dateutil.parser.parse(match_group).replace(tzinfo=tz)
        except ValueError, e:
            print "Error creating date from string %s - %s" % (match_group, e)
        else:
            return start.date(), clean

    return None


def get_next_weekday(weekday):

    tz = pytz.timezone(timezone.get_current_timezone_name())
    now = datetime.now(tz)

    # target weekday is before today
    weekday_num = WEEK_TO_NUM[weekday]
    if now.weekday() < weekday_num:
        nearest = now + relativedelta(weekday=weekday_num)
        return nearest + relativedelta(days=+1, weekday=weekday_num)

    # target weekday is today
    elif weekday_num == now.weekday():
        return now + relativedelta(days=+1, weekday=weekday_num)

    # target is in the future
    else:
        return now + relativedelta(weekday=weekday_num) \
               + timedelta(days=1) + relativedelta(weekday=weekday_num)


def trim(string):
    return string.replace('  ', ' ').lstrip(' ').rstrip(' ')
