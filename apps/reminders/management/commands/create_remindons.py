from django.core.management.base import NoArgsCommand
from django.utils import dates as date

from reminders.models import RemindOn

MONTH_LENGTHS = {
    1: 31,
    2: 29,
    3: 31,
    4: 30,
    5: 31,
    6: 30,
    7: 31,
    8: 31,
    9: 30,
    10: 31,
    11: 30,
    12: 31,
}


class Command(NoArgsCommand):

    def handle_noargs(self, **options):

        print 'Creating RemindOns'

        RemindOn.objects.all().delete()

        remindons = [
            'Today', 'Tonight', 'Tomorrow'
        ]

        # Weekday
        for index, weekday in date.WEEKDAYS.iteritems():
            remindons.append(unicode(weekday))

        # Next weekday
        for index, weekday in date.WEEKDAYS.iteritems():
            remindons.append('Next ' + unicode(weekday))

        # This weekday
        for index, weekday in date.WEEKDAYS.iteritems():
            remindons.append('This ' + unicode(weekday))

        # Short Months (25 apr)
        for index, month in date.MONTHS_3.iteritems():
            for i in range(MONTH_LENGTHS[index]):
                remindons.append('%s %s' % (i + 1, unicode(month)))

        # Months (25 April)
        for index, month in date.MONTHS.iteritems():
            for i in range(MONTH_LENGTHS[index]):
                remindons.append('%s %s' % (i + 1, unicode(month)))

        # Numeric Months (25/12 or 12/25)
        for index, month in date.MONTHS.iteritems():
            for i in range(MONTH_LENGTHS[index]):
                remindons.append('%s/%s' % (i + 1, index))
                remindons.append('%s/%s' % (index, i + 1))

        # Special days
        remindons += ['Easter Sunday', 'Good Friday', 'New Years Day',
                    'Christmas Day', 'Xmas Day', 'Christmas Eve',
                    'Xmas Eve', 'Boxing Day', 'Valentines', 'April Fools']

        for r in remindons:
            RemindOn(name=r).save()

        print "Created %s new remind ons" % len(remindons)
