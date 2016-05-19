from django.core.management.base import NoArgsCommand

from reminders.models import RemindAt

twelve = [i+1 for i in range(12)]
twentyfour = [i for i in range(24)]
minutes = [i for i in range(60)]


class Command(NoArgsCommand):

    def handle_noargs(self, **options):

        print 'Creating RemindAts'

        RemindAt.objects.all().delete()

        # Special Names
        remindats = ['Midday', 'Midnight', 'Lunch', 'Lunchtime']

        # 6
        for t in twelve:
            remindats.append(str(t))

        # 11am
        for t in twelve:
            remindats.append('%sam' % t)

        # 11pm
        for t in twelve:
            remindats.append('%spm' % t)

        # 11:30am
        for t in twelve:
            for m in minutes:
                remindats.append(
                    '%s:%sam' % (str(t).zfill(2), str(m).zfill(2)))

        # 11:30pm
        for t in twelve:
            for m in minutes:
                remindats.append(
                    '%s:%spm' % (str(t).zfill(2), str(m).zfill(2)))

        # 11:30 or 18:30
        for t in twentyfour:
            for m in minutes:
                remindats.append('%s:%s' % (str(t).zfill(2), str(m).zfill(2)))

        for r in remindats:
            RemindAt(name=r).save()

        print "Created %s new remind ats" % len(remindats)
