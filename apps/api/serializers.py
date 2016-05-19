from datetime import datetime, timedelta

import pytz

from django.utils import timezone
from django.conf import settings

from rest_framework import serializers
from rest_framework import fields
from rest_framework.authtoken.models import Token

from utils.date_parser import match_date
from utils.time_parser import match_time
from utils.delta_parser import match_delta

from reminders.models import Reminder
from accounts.models import LocalUser
from timezones.models import Timezone


class ReminderSerializer(serializers.ModelSerializer):
    user = fields.ReadOnlyField(source='user.id')
    url = fields.CharField(source='get_full_url')
    localised_start = fields.SerializerMethodField()

    class Meta:
        model = Reminder
        fields = (
            'id', 'status', 'content', 'start_date', 'start_time',
            'interval_type', 'interval_value', 'max_recurrances',
            'scheduled_end_date', 'completion_date', 'snooze_count',
            'hash_digest', 'total_reminders', 'total_snoozes',
            'full_start_datetime', 'user', 'url', 'short_content',
            'last_update', 'localised_start', 'deleted'
        )

    def get_localised_start(self, obj):
        return obj.localised_start()


class ErrorHandler(object):
    """
    Forms require a proper error class and serialisers
    use a dict for holding field errors. This is a hack to share
    logic between forms and serializers
    """
    def return_error(self, message):
        return [message]


class QuickReminderSerializer(serializers.ModelSerializer, ErrorHandler):

    class Meta:
        model = Reminder
        fields = ('id', 'content', 'start_date', 'start_time', 'user')

    def __init__(self, *args, **kwargs):
        super(QuickReminderSerializer, self).__init__(*args, **kwargs)
        self.fields['start_date'].required = False
        self.fields['start_time'].required = False

    def validate(self, attrs):
        usertz = pytz.timezone(timezone.get_current_timezone_name())

        if 'content' not in attrs:
            err = 'Please enter something we can remind you about'
            raise serializers.ValidationError(detail={'content': err})

        # Try to work out a reminder time
        time_match = match_time(attrs['content'])
        if time_match is None:
            err = 'Please enter a reminder time'
            raise serializers.ValidationError(detail={'content': err})

        remind_at = time_match[0]
        attrs['content'] = time_match[1]

        # Try to find a reminder date (fall back to today if none found)
        date_match = match_date(attrs['content'])
        if date_match is None:
            # if the time is > now set the date to today
            date_match = [datetime.now(usertz).date(), attrs['content']]

        remind_on = date_match[0]
        attrs['content'] = date_match[1]

        ro = remind_on
        ra = remind_at.split(':')

        dstr = '%s/%s/%s %s:%s:00' % (ro.day, ro.month, ro.year, ra[0], ra[1])
        dt = datetime.strptime(dstr, '%d/%m/%Y %H:%M:%S')

        dt = usertz.localize(dt)

        if dt > datetime.now(usertz):
            # Save the dates as UTC
            attrs['start_date'] = dt.astimezone(pytz.timezone('UTC')).date()
            attrs['start_time'] = dt.astimezone(pytz.timezone('UTC')).time()
        else:
            err = 'Please pick a date in the future'
            raise serializers.ValidationError(detail={'content': err})

        return attrs


class ReminderSnoozeSerializer(serializers.ModelSerializer, ErrorHandler):
    snooze_until = fields.CharField()
    content = fields.ReadOnlyField()

    class Meta:
        model = Reminder
        fields = ('start_date', 'start_time', 'snooze_until', 'content')

    def __init__(self, *args, **kwargs):
        super(ReminderSnoozeSerializer, self).__init__(*args, **kwargs)
        self.fields['start_date'].required = False
        self.fields['start_time'].required = False

    def validate(self, attrs):
        usertz = pytz.timezone(timezone.get_current_timezone_name())
        snooze_time, snooze_date = None, None

        # Check if the snooze format is a timedelta
        delta_match = match_delta(attrs['snooze_until'])
        if delta_match is not None:
            return {
                'snooze_until': delta_match,
                'start_date': delta_match.date(),
                'start_time': delta_match.time(),
            }

        # Check if the snooze format is a time
        time_match = match_time(attrs['snooze_until'])
        if time_match is not None:
            snooze_time = datetime.strptime(time_match[0], '%H:%M:%S')
            dt = usertz.localize(datetime.combine(
                                 self.instance.start_date,
                                 snooze_time.time()))
            if time_match[1] == '':
                if dt < datetime.now(usertz):
                    dt = dt + timedelta(days=1)

                if dt > datetime.now(usertz):
                    target = dt.astimezone(pytz.timezone('UTC'))
                    return {
                        'snooze_until': target,
                        'start_date': target.date(),
                        'start_time': target.time(),
                    }

                err = 'Please enter a snooze time/date in the future'
                raise serializers.ValidationError(detail={'snooze_until': err})

        # Check if the snooze format is a date
        date_match = match_date(attrs['snooze_until'])
        if date_match is not None:
            if snooze_time is not None:
                dt = datetime.combine(date_match[0], snooze_time.time())
            else:
                dt = datetime.combine(date_match[0],
                                      self.instance.localised_start().time())

            usertz = pytz.timezone(timezone.get_current_timezone_name())
            dt = usertz.localize(dt)

            if dt > datetime.now(usertz):
                target = dt.astimezone(pytz.timezone('UTC'))
                return {
                    'snooze_until': target,
                    'start_date': target.date(),
                    'start_time': target.time(),
                }

        err = 'Please enter a snooze time/date in the future'
        raise serializers.ValidationError(detail={'snooze_until': err})


class ReminderEditSerializer(serializers.ModelSerializer, ErrorHandler):

    class Meta:
        model = Reminder
        fields = (
            'id', 'content', 'start_date', 'start_time', 'status', 'last_update'
        )

    def __init__(self, *args, **kwargs):
        super(ReminderEditSerializer, self).__init__(*args, **kwargs)
        self.fields['last_update'].required = False

    def validate(self, attrs):
        usertz = pytz.timezone(timezone.get_current_timezone_name())

        # Make the dates utc
        dt = datetime.combine(
            attrs['start_date'], attrs['start_time']
        ).replace(tzinfo=pytz.timezone('UTC'))
        attrs['start_date'] = dt.date()
        attrs['start_time'] = dt.time()

        if 'last_update' in attrs:
            attrs['last_update'] = attrs['last_update'].replace(
                tzinfo=pytz.timezone('UTC')
            )

        return attrs


class UserRegisterSerializer(serializers.ModelSerializer, ErrorHandler):
    confirm_password = serializers.CharField(required=True)
    timezone_name = serializers.CharField(required=True)

    class Meta:
        model = LocalUser
        fields = ('reminders', 'email', 'timezone', 'timezone_name',
                  'confirm_password', 'password')

    def __init__(self, *args, **kwargs):
        super(UserRegisterSerializer, self).__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['timezone'].required = False
        self.fields['password'].required = True

    def validate(self, attrs):

        if attrs['password'] != attrs['confirm_password']:
            err = 'Please ensure both passwords match'
            raise serializers.ValidationError(detail={'password': err})

        return attrs

    def validate_password(self, password):
        if hasattr(settings, 'ACCOUNT_PASSWORD_MIN_LENGTH') \
                and len(password) < settings.ACCOUNT_PASSWORD_MIN_LENGTH:
            err = 'Password must be at least %s characters.' % (
                settings.ACCOUNT_PASSWORD_MIN_LENGTH)
            raise serializers.ValidationError(err)
        return password

    def validate_email(self, email):

        if email == '':
            err = 'This field may not be blank.'
            raise serializers.ValidationError(err)

        try:
            LocalUser.objects.get(email__iexact=email)
        except LocalUser.DoesNotExist:
            return email

        err = 'This email address is already in use.'
        raise serializers.ValidationError(err)

    def validate_timezone_name(self, timezone_name):
        try:
            return Timezone.objects.get(name=timezone_name).name
        except Timezone.DoesNotExist:
            # FIXME - This is a bad guess
            return Timezone.objects.get(name='Europe/London').name


class UserSerializer(serializers.ModelSerializer, ErrorHandler):
    reminders = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    token = serializers.SerializerMethodField('get_auth_token')

    class Meta:
        model = LocalUser
        fields = ('id', 'reminders', 'email', 'timezone',
                  'created', 'token')

    def get_auth_token(self, obj):
        try: return Token.objects.get(user=obj).key
        except Token.DoesNotExist:
            return None

