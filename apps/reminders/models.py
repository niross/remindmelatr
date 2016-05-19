from datetime import datetime, time, timedelta
import pytz
import os
from email.mime.image import MIMEImage

from django.db import models
from django.conf import settings
from django.template import Context
from django.template.loader import get_template
from django.core.mail import EmailMultiAlternatives
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.utils.text import Truncator
from django.utils.crypto import get_random_string

from dateutil.relativedelta import *

from base.models import TimeStampedModel
from accounts.models import LocalUser

REMINDER_STATUS = (
    (1, 'Paused'),
    (2, 'Live'),
    (3, 'Snoozed'),
    (4, 'Overdue'),
    (5, 'Completed'),
    (6, 'Cancelled'),
    (7, 'Deleted'),
)

REMINDER_INTERVALS = (
    (1, 'Minutes'),
    (2, 'Hours'),
    (3, 'Days'),
    (4, 'Months'),
    (5, 'Years'),
)

WEEKDAYS = {
    0: 'Monday',
    1: 'Tuesday',
    2: 'Wednesday',
    3: 'Thursday',
    4: 'Friday',
    5: 'Saturday',
    6: 'Sunday',
}

MONTHS = {
    1: 'January',
    2: 'February',
    3: 'March',
    4: 'April',
    5: 'May',
    6: 'June',
    7: 'July',
    8: 'August',
    9: 'September',
    10: 'October',
    11: 'November',
    12: 'December',
}


class RemindOn(TimeStampedModel):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'remindmelatr_remindon'

    def __unicode__(self):
        return self.name


class RemindAt(TimeStampedModel):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'remindmelatr_remindat'

    def __unicode__(self):
        return self.name


class ReminderManager(models.Manager):

    def _current_datetime(self):
        utc = pytz.timezone('UTC')
        date_now = datetime.now(utc)
        return date_now.replace(second=0, microsecond=0)

    def overdue(self, user=None):
        qs = super(ReminderManager, self).get_queryset().filter(
           deleted=False, status__in=[2, 4],
           full_start_datetime__lt=self._current_datetime()
        )
        if user is not None:
            qs = qs.filter(user=user)
        return qs.order_by('full_start_datetime')

    def outstanding(self, user=None):
        qs = super(
            ReminderManager, self).get_queryset().filter(
            deleted=False, status__in=[2, 3, 4],
            full_start_datetime__gte=self._current_datetime()
        )
        if user is not None:
            qs = qs.filter(user=user)
        return qs

    def valid(self, user=None):
        qs = super(ReminderManager, self).get_queryset().filter(
            deleted=False, status__in=[2,3], in_progress=False,
            full_start_datetime__lte=self._current_datetime(),
            completion_date=None
        )
        if user is not None:
            qs = qs.filter(user=user)
        return qs

    def completed(self, user=None):
        qs = super(ReminderManager, self).get_queryset().filter(
            deleted=False, status__in=[5]
        )
        if user is not None:
            qs = qs.filter(user=user)
        return qs.order_by('-completion_date')

    def paused(self, user=None):
        qs = super(ReminderManager, self).get_queryset().filter(
                     deleted=False, status=1)
        if user is not None:
            qs = qs.filter(user=user)
        return qs

    def incomplete(self, user=None):
        qs = super(ReminderManager, self).get_queryset().filter(
                     deleted=False, status__in=[2, 4])
        if user is not None:
            qs = qs.filter(user=user)
        return qs

    def all(self, user=None):
        qs = super(ReminderManager, self).get_queryset().filter(deleted=False)
        if user is not None:
            qs = qs.filter(user=user)
        return qs


class Reminder(TimeStampedModel):
    user = models.ForeignKey(LocalUser, related_name='reminders')
    status = models.IntegerField(choices=REMINDER_STATUS, default=2)
    content = models.TextField()
    start_date = models.DateField()
    start_time = models.TimeField()
    interval_type = models.IntegerField(choices=REMINDER_INTERVALS, null=True)
    interval_value = models.IntegerField(null=True)
    max_recurrances = models.IntegerField(default=0)
    scheduled_end_date = models.DateTimeField(null=True)
    completion_date = models.DateTimeField(null=True)
    snooze_count = models.IntegerField(default=0)
    snooze_timeout_value = models.IntegerField(default=1)
    snooze_timeout_interval = models.IntegerField(choices=REMINDER_INTERVALS,
                                                  default=2)
    hash_digest = models.CharField(max_length=150, unique=True)

    next_fire = models.DateTimeField(null=True)
    in_progress = models.BooleanField(default=False)

    total_reminders = models.IntegerField(default=0)
    total_snoozes = models.IntegerField(default=0)

    full_start_datetime = models.DateTimeField()

    desktop_notification_sent = models.BooleanField(default=False)

    last_update = models.DateTimeField()

    objects = ReminderManager()

    class Meta:
        ordering = ('full_start_datetime',)
        db_table = 'remindmelatr_reminder'

    def save(self, *args, **kwargs):
        if self.id is None:
            self.hash_digest = get_random_string(20)
        utc = pytz.timezone('UTC')
        self.full_start_datetime = datetime.combine(
                self.start_date, self.start_time).replace(tzinfo=utc)
        if self.last_update is None:
            self.last_update = datetime.now().replace(tzinfo=utc)
        super(Reminder, self).save(*args, **kwargs)

    def long_id(self):
        return str(self.id).zfill(6)

    def short_content(self, length=40):
        return Truncator(self.content).chars(length)

    def as_timestamp(self):
        import time
        return int(time.mktime(self.full_start_datetime.timetuple()))

    def localised_start(self):
        tz = pytz.timezone(self.user.timezone.name)
        return self.full_start_datetime.astimezone(tz)

    def localised_created(self):
        tz = pytz.timezone(self.user.timezone.name)
        return self.created.astimezone(tz)

    def localised_updated(self):
        tz = pytz.timezone(self.user.timezone.name)
        return self.updated.astimezone(tz)

    def soft_delete(self):
        self.deleted = True
        self.status = 7
        self.last_update = datetime.now().replace(tzinfo=pytz.timezone('UTC'))
        self.save()
        self.add_history_entry('Reminder permanently deleted.')

    def complete(self):
        utc = pytz.timezone('UTC')
        self.completion_date = datetime.now(utc)
        self.status = 5
        self.last_update = datetime.now().replace(tzinfo=pytz.timezone('UTC'))
        self.save()
        self.add_history_entry('Reminder marked as complete.')

    def pause(self):
        utc = pytz.timezone('UTC')
        self.completion_date = datetime.now(utc)
        self.status = 1
        self.desktop_notification_sent = False
        self.last_update = datetime.now().replace(tzinfo=pytz.timezone('UTC'))
        self.save()
        self.add_history_entry('Reminder status set to PAUSED.')

    def unpause(self):
        utc = pytz.timezone('UTC')
        self.completion_date = datetime.now(utc)
        self.status = 2
        self.last_update = datetime.now().replace(tzinfo=pytz.timezone('UTC'))
        self.save()
        self.add_history_entry('Reminder status set to LIVE.')

    def overdue(self):
        self.status = 4
        self.desktop_notification_sent = False
        self.last_update = datetime.now().replace(tzinfo=pytz.timezone('UTC'))
        self.save()
        self.add_history_entry('Reminder marked as OVERDUE.')

    def set_next_fire_time(self):
        utc = pytz.timezone('UTC')
        if self.completion_date <= datetime.now(utc):
            self.complete()
        elif self.total_reminders >= self.max_recurrances:
            self.complete()
        else:
            self.next_fire = self.get_interval_timedelta(
                self.interval_type,
                self.interval_value
            )
        self.in_progress = False
        self.save()

    def get_interval_timedelta(self, interval_type, interval_value):
        utc = pytz.timezone('UTC')
        now = datetime.now(utc)

        if interval_type == 1:
            return now + timedelta(minutes=interval_value)
        if interval_type == 2:
            return now + timedelta(hours=interval_value)
        if interval_type == 3:
            return now + timedelta(days=interval_value)
        if interval_type == 4:
            return now + relativedelta(months=1)
        if interval_type == 5:
            return now + relativedelta(years=1)

    def get_human_readable(self):
        start = self.localised_start()
        remind_on = 'on %s' % WEEKDAYS[start.weekday()]
        remind_at = time.strftime(start.time(), '%H:%M')
        today = datetime.now(pytz.timezone(self.user.timezone.name))
        tomorrow = today + timedelta(days=1)
        if start.date() == today.date():
            remind_on = 'today'
        elif start.date() == tomorrow.date():
            remind_on = 'tomorrow'
        elif start.date().month > today.date().month \
                or start.date().year > today.year:
            remind_on += ' %s %s' % (
                start.date().day, MONTHS[start.date().month]
            )
        # if the week is not this week
        elif today.date().isocalendar()[1] < start.date().isocalendar()[1]:
            remind_on += ' %s %s' % (
                start.date().day, MONTHS[start.date().month]
            )
        elif start.date() == today.date() - timedelta(days=1):
            remind_on = 'yesterday'

        if start.date().year > today.year or start.date().year < today.year:
            remind_on += ' %s' % start.date().year

        return remind_on, remind_at

    def success_message(self):
        on, at = self.get_human_readable()
        url = '<a href="%s">reminder</a>' % self.get_absolute_url()
        return '<strong>Woo!</strong> New %s set for %s %s.' % (url, at, on)

    def edited_message(self):
        on, at = self.get_human_readable()
        url = '<a href="%s">Reminder</a>' % self.get_absolute_url()
        return '<strong>Sweet!</strong> %s edited and set for %s %s.' % (
            url, at, on
        )

    def snooze_message(self):
        on, at = self.get_human_readable()
        url = '<a href="%s">Reminder</a>' % self.get_absolute_url()
        return '<strong>Zzzzz!</strong> %s snoozed until %s %s.' % (
            url, at, on
        )

    def pause_message(self):
        url = '<a href="%s">reminder</a>' % self.get_absolute_url()
        return '<strong>Done!</strong> Your %s has now been paused.' % url

    def unpause_message(self):
        url = '<a href="%s">reminder</a>' % self.get_absolute_url()
        return '<strong>Done!</strong> Your %s has been reactivated.' % url

    def listing_message(self):
        on, at = self.get_human_readable()
        if on.startswith('on '):
            on = on[3:]
        return '%s at %s' % (on, at)

    def get_absolute_url(self):
        return reverse('reminder', kwargs={'reminder_id': self.id})

    def get_full_url(self):
        site = Site.objects.get_current()
        return 'https://' + site.domain + self.get_absolute_url()

    def remind(self):

        self.in_progress = True
        self.save()

        html = get_template('email/reminder.html')
        text = get_template('email/reminder.txt')

        subject = 'A new reminder from remindmelatr.com [RML%s]' % (
            self.long_id())
        context = Context({
            'reminder': self,
            'site': Site.objects.get_current(),
            'subject': subject,
        })

        text_content = text.render(context)
        html_content = html.render(context)

        msg = EmailMultiAlternatives(subject, text_content,
                                     settings.FROM_EMAIL, [self.user.email])
        msg.attach_alternative(html_content, 'text/html')

        msg.mixed_subtype = 'related'
        logo_path = settings.EMAIL_LOGO
        with open(logo_path, 'rb') as fp:
            msg_img = MIMEImage(fp.read())
            msg_img.add_header('Content-ID', '<%s>' % (
               os.path.basename(logo_path)
            ))
            msg.attach(msg_img)

        msg.send()

        self.add_history_entry('Reminder sent.')

        self.overdue()

    def snooze(self, snooze_date, snooze_time):
        self.start_date = snooze_date
        self.start_time = snooze_time
        self.status = 3
        self.in_progress = False
        self.completion_date = None
        self.snooze_count += 1
        self.last_update = datetime.now().replace(tzinfo=pytz.timezone('UTC'))
        self.save()
        on, at = self.get_human_readable()
        self.add_history_entry('Reminder snoozed until %s %s.' % (at, on))

    def initial_form_values(self):
        start = self.localised_start()
        return {
            'remind_on': start.strftime('%d %B %Y'),
            'remind_at': start.strftime('%H:%M'),
        }

    def refresh_status(self):
        if datetime.combine(self.start_date, self.start_time) > datetime.now():
            self.status = 2
            self.in_progress = False

    def add_history_entry(self, description, internal=False, extra=None):
        r = ReminderHistory(
            reminder=self, internal=internal,
            description=description, status=self.status,
            content=self.content,
            snooze_count=self.snooze_count,
            total_reminders=self.total_reminders,
            total_snoozes=self.total_snoozes,
            full_start_datetime=self.full_start_datetime
        )
        if extra is not None:
            r.extra_info = extra
        r.save()

    def history(self, include_internal=False):
        history = ReminderHistory.objects.filter(reminder=self)
        if not include_internal:
            history = history.filter(internal=False)
        return history


class ReminderHistory(TimeStampedModel):
    """
    Holds the state of the reminder and a description of the historic event
    """
    reminder = models.ForeignKey(Reminder)
    internal = models.BooleanField(default=False)
    description = models.TextField()
    status = models.IntegerField(choices=REMINDER_STATUS)
    content = models.TextField()
    snooze_count = models.IntegerField(default=0)
    total_reminders = models.IntegerField(default=0)
    total_snoozes = models.IntegerField(default=0)
    full_start_datetime = models.DateTimeField()
    extra_info = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'remindmelatr_reminderhistory'
        ordering = ('-created',)
