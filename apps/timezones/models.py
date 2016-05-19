import pytz
from datetime import datetime

from django.db import models

from base.models import TimeStampedModel


class Timezone(TimeStampedModel):
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=200)
    offset_hours = models.IntegerField()
    offset_minutes = models.IntegerField()
    country_code = models.CharField(max_length=3)
    country_name = models.CharField(max_length=200)

    class Meta:
        ordering = ('offset_hours', 'offset_minutes', 'name')

    def __unicode__(self):
        return self.pretty()

    def pretty(self):
        return '(GMT %s) %s' % (
            datetime.now(pytz.timezone(self.name)).strftime('%z'),
            self.short_name
        )
