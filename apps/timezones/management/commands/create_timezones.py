from datetime import datetime
import pytz
from django.core.management.base import NoArgsCommand
from timezones.models import Timezone



class Command(NoArgsCommand):

    def handle_noargs(self, **options):
        print 'Creating timezones'
        Timezone.objects.all().delete()
        countries = pytz.country_names
        country_timezones = pytz.country_timezones
        common_timezones = pytz.common_timezones
        timezones = {}
        for code, tzs in country_timezones.iteritems():
            for tz in tzs:
                if tz in common_timezones:
                    if code not in timezones:
                        timezones[code] = []
                    timezones[code].append(tz)

        for country_code, country_name in countries.iteritems():
            if country_code in timezones:
                dt = datetime.utcnow()
                for ctz in timezones[country_code]:
                    short_name = ctz.split('/')[-1]
                    delta = pytz.timezone(ctz).utcoffset(dt)
                    days, seconds = delta.days, delta.seconds
                    hours = days * 24 + seconds // 3600
                    minutes = (seconds % 3600) // 60
                    print 'Adding {} -> {}'.format(
                        ctz, datetime.now(pytz.timezone(ctz)).strftime('%z')
                    )
                    t = Timezone(
                        name=ctz,
                        short_name=short_name,
                        offset_hours=hours,
                        offset_minutes=minutes,
                        country_code=country_code,
                        country_name=country_name,
                    )
                    t.save()
        print 'Done!'