import re

TIME_STRINGS = {
    'lunchtime': '12:00:00',
    'midnight': '00:00:00',
    'midday': '12:00:00',
}

NUM_STRINGS = {
    'one': 1,
    'two': 2,
    'three': 3,
    'four': 4,
    'five': 5,
    'six': 6,
    'seven': 7,
    'eight': 8,
    'nine': 9,
    'ten': 10,
    'eleven': 11,
    'twelve': 12,
}
PADDED = ["%02d" % x for x in range(0, 10)]
HOURS = PADDED + [x for x in range(0, 24)]
MORNING_HOURS = PADDED + [str(x) for x in HOURS if x < 13]
SECONDS = PADDED + [x for x in range(0, 60)]
ACTUAL_HOURS = r'\b%s' % r'|\b'.join(MORNING_HOURS)


def match_time(term):
    """
    Find a time in a string

    Tries to match the following date styles

        * 11
        * 11 am
        * 11 pm
        * 23
        * 23:59
        * one
        * ome pm
        * ome am
        * lunch
        * lunchtime
        * midnight
    """

    # lunchtime, midnight, etc.
    str_match = re.compile(r'.*?\b(%s)\b.*?' % '|'.join(TIME_STRINGS), re.I)
    if str_match.match(term.lower()) is not None:
        match = str_match.match(term).group(1)
        clean = trim(re.sub(match, '', term, re.I))
        return TIME_STRINGS[match.lower()], clean

    # 11:59, 23:59
    all_hours = r'\b%s' % r'\b|\b'.join([str(x) for x in reversed(HOURS)])
    all_seconds = r'\b%s' % r'\b|\b'.join([str(x) for x in reversed(SECONDS)])
    str_match = re.compile(
        r'.*?((%s):(%s)).*?' % (all_hours, all_seconds), re.I
    )
    if str_match.match(term.lower()) is not None:
        m = str_match.match(term.lower())
        clean = trim(re.sub(m.group(1), '', term, re.I))
        return "%02d:%02d:00" % (int(m.group(2)), int(m.group(3))), clean

    # 11:59am, 11:59 am, 11.59am, 11.59 am
    seconds = r'\b%s' % r'|\b'.join(reversed([str(x) for x in SECONDS]))
    str_match = re.compile(
        r'.*?((%s)(?:\.|\:)(%s)(\ *am\ *)).*?' % (ACTUAL_HOURS, seconds), re.I
    )
    if str_match.match(term.lower()) is not None:
        hour = int(str_match.match(term.lower()).group(2))
        minute = int(str_match.match(term.lower()).group(3))
        period = str_match.match(term.lower()).group(4)
        if int(hour) == 12:
            hour = 0
        clean = re.sub(str_match.match(term.lower()).group(1), '', term, re.I)
        return "%02d:%02d:00" % (hour, minute), clean

    # 11:59pm, 11:59 pm, 11.59pm, 11.59 pm
    seconds = r'\b%s' % r'|\b'.join([str(x) for x in SECONDS])
    str_match = re.compile(
        r'.*?((%s)(?:\.|\:)(%s)(\ *pm\ *)).*?' % (ACTUAL_HOURS, seconds), re.I
    )
    if str_match.match(term.lower()) is not None:
        hour = int(str_match.match(term.lower()).group(2))
        minute = int(str_match.match(term.lower()).group(3))
        if int(hour) == 12:
            hour = 0
        clean = re.sub(str_match.match(term.lower()).group(1), '', term, re.I)
        return "%02d:%02d:00" % (hour + 12, minute), clean

    # 11am, 11 am
    str_match = re.compile(r'.*?(%s)(\ *am\ *).*?' % ACTUAL_HOURS, re.I)
    if str_match.match(term.lower()) is not None:
        match_group = int(str_match.match(term.lower()).group(1))
        period = str_match.match(term.lower()).group(2)
        clean = re.sub('%s%s' % (match_group, period), '', term, re.I)
        return "%02d:00:00" % match_group, clean

    # 11pm, 11 pm
    str_match = re.compile(r'.*?(%s)(\ *pm\ *).*?' % ACTUAL_HOURS, re.I)
    if str_match.match(term.lower()) is not None:
        match_group = int(str_match.match(term.lower()).group(1))
        period = str_match.match(term.lower()).group(2)
        hour = match_group
        if match_group == 12:
            hour = 0
        hour += 12
        clean = re.sub('%s%s' % (match_group, period), '', term, re.I)
        return "%02d:00:00" % hour, clean

    # one am
    hour_strings = r'\b%s' % r'|\b'.join(NUM_STRINGS)
    str_match = re.compile(r'.*?(%s)(\ *am\ *).*?' % hour_strings, re.I)
    if str_match.match(term.lower()) is not None:
        match_group = str_match.match(term.lower()).group(1)
        period = str_match.match(term.lower()).group(2)
        clean = re.sub('%s%s' % (match_group, period), '', term, re.I)
        return "%02d:00:00" % int(NUM_STRINGS[match_group]), clean

    # one pm
    str_match = re.compile(r'.*?(%s)(\ *pm\ *).*?' % hour_strings, re.I)
    if str_match.match(term.lower()) is not None:
        match_group = str_match.match(term.lower()).group(1)
        hour = int(NUM_STRINGS[match_group])
        period = str_match.match(term.lower()).group(2)
        if int(hour) == 12:
            hour = 0
        clean = term.lower().replace('%s%s' % (hour, period), '')
        clean = re.sub('%s%s' % (match_group, period), '', term, re.I)
        return "%02d:00:00" % (hour + 12), clean

    return None

def trim(string):
    return string.replace('  ', ' ').lstrip(' ').rstrip(' ')
