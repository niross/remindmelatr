from datetime import datetime, timedelta
import pytz

from django import forms
from django.forms import widgets
from django.utils import timezone

from bootstrap_toolkit.widgets import BootstrapTextInput

from .models import Reminder
from utils.date_parser import match_date
from utils.time_parser import match_time
from utils.delta_parser import match_delta

class QuickReminderForm(forms.ModelForm):
    class Meta:
        model = Reminder
        fields = ('content',)
        widgets = {
            'content': BootstrapTextInput(attrs={
                'class': 'form-control',
                'tabindex': 0,
                'autocomplete': 'off',
            })
        }

    def __init__(self, *args, **kwargs):
        super(QuickReminderForm, self).__init__(*args, **kwargs)
        err = 'Please enter some content for the reminder'
        self.fields['content'].error_messages['required'] = err
        self.fields['content'].error_messages['blank'] = err

    def clean(self):
        cleaned = super(QuickReminderForm, self).clean()
        usertz = pytz.timezone(timezone.get_current_timezone_name())

        if 'content' not in cleaned:
            self._errors['content'] = self.error_class([
                    'Please enter something we can remind you about'])
            return cleaned

        # Try to work out a reminder time
        time_match = match_time(cleaned['content'])
        if time_match is None:
            msg = 'Please enter a reminder time'
            self._errors['content'] = self.error_class([msg])
            return cleaned
        cleaned['remind_at'] = time_match[0]
        cleaned['content'] = time_match[1]

        # Try to find a reminder date (fall back to today if none found)
        date_match = match_date(cleaned['content'])
        if date_match is None:
            # if the time is > now set the date to today
            date_match = [datetime.now(usertz).date(), cleaned['content']]

        cleaned['remind_on'] = date_match[0]
        cleaned['content'] = date_match[1]

        ro = cleaned['remind_on']
        ra = cleaned['remind_at'].split(':')

        dstr = '%s/%s/%s %s:%s:00' % (ro.day, ro.month, ro.year, ra[0], ra[1])
        dt = datetime.strptime(dstr, '%d/%m/%Y %H:%M:%S')

        dt = usertz.localize(dt)

        if dt > datetime.now(usertz):
            # Save the dates as UTC
            cleaned['remind_on'] = dt.astimezone(pytz.timezone('UTC')).date()
            cleaned['remind_at'] = dt.astimezone(pytz.timezone('UTC')).time()
        else:
            msg = 'Please pick a date in the future'
            self._errors['content'] = self.error_class([msg])

        return cleaned

    def save(self, commit=True):
        reminder = super(QuickReminderForm, self).save(commit=False)
        reminder.start_date = self.cleaned_data['remind_on']
        reminder.start_time = self.cleaned_data['remind_at']
        reminder.refresh_status()
        if commit:
            reminder.save()
        return reminder


class BasicReminderForm(forms.ModelForm):
    remind_on  = forms.CharField(
        error_messages = {
            'required': 'Please enter a reminder date',
        },
        widget=BootstrapTextInput(attrs={
            'class': 'reminder-on form-control input-hg',
            'tabindex': 1,
            'placeholder': 'Reminder Date',
            'autocomplete': 'off',
        })
    )
    remind_at = forms.CharField(
        error_messages = {
            'required': 'Please enter a reminder time',
        },
        widget=BootstrapTextInput(attrs={
            'class': 'reminder-at form-control input-hg',
            'tabindex': 2,
            'placeholder': 'Reminder Time',
            'autocomplete': 'off',
        })
    )

    class Meta:
        model = Reminder
        fields = ('content',)
        widgets = {
            'content': widgets.Textarea(attrs={
                'class': 'form-control',
                'tabindex': 3,
                'placeholder': 'Reminder Content',
            })
        }

    def clean_remind_on(self):
        data = self.cleaned_data['remind_on']
        dt = match_date(self.cleaned_data['remind_on'])
        if dt is not None:
            return dt[0]
        msg = 'Please enter a valid reminder date'
        self._errors['remind_on'] = self.error_class([msg])

    def clean_remind_at(self):
        data = self.cleaned_data['remind_at']
        dt = match_time(self.cleaned_data['remind_at'])
        if dt is not None:
            return dt[0]
        msg = 'Please enter a valid reminder time'
        self._errors['remind_at'] = self.error_class([msg])

    def clean(self):
        cleaned = super(BasicReminderForm, self).clean()
        usertz = pytz.timezone(timezone.get_current_timezone_name())

        if 'remind_at' in cleaned and 'remind_on' in cleaned \
                and cleaned['remind_at'] is not None \
                and cleaned['remind_on'] is not None:
            ro = cleaned['remind_on']
            ra = cleaned['remind_at'].split(':')
            dt = usertz.localize(datetime(ro.year, ro.month, ro.day,
                                          int(ra[0]), int(ra[1]), 0))

            if dt > datetime.now(usertz):
                cleaned['remind_on'] = dt.astimezone(
                    pytz.timezone('UTC')
                ).date()
                cleaned['remind_at'] = dt.astimezone(
                    pytz.timezone('UTC')
                ).time()
            else:
                msg = 'Please pick a date in the future'
                self._errors['remind_at'] = self.error_class([msg])

        return cleaned

    def save(self, commit=True):
        reminder = super(BasicReminderForm, self).save(commit=False)
        reminder.start_date = self.cleaned_data['remind_on']
        reminder.start_time = self.cleaned_data['remind_at']
        reminder.refresh_status()
        if commit:
            reminder.save()

        return reminder


class ExternalSnoozeForm(forms.ModelForm):
    snooze_until = forms.CharField(
        required=True,
        error_messages={
            'required': 'Please enter a valid snooze interval '
                        'or date/time in the future',
        },
        widget=BootstrapTextInput(attrs={
            'class': 'reminder-on form-control input-hg',
            'tabindex': 1,
            'placeholder': 'Snooze until',
            'autocomplete': 'off',
        })
    )

    class Meta:
        model = Reminder
        fields = ('id',)
        widgets = {
            'id': widgets.HiddenInput()
        }

    def clean_snooze_until(self):
        data = self.cleaned_data['snooze_until']
        usertz = pytz.timezone(timezone.get_current_timezone_name())
        snooze_time, snooze_date = None, None

        # Check if the snooze format is a time delta
        delta_match = match_delta(data)
        if delta_match is not None:
            return delta_match

        # Check if the snooze format is a time
        time_match = match_time(data)
        if time_match is not None:
            snooze_time = datetime.strptime(time_match[0], '%H:%M:%S')
            dt = usertz.localize(
                datetime.combine(
                    self.instance.start_date,
                    snooze_time.time()
                )
            )
            if time_match[1] == '':
                if dt < datetime.now(usertz):
                    dt = dt + timedelta(days=1)

                if dt > datetime.now(usertz):
                    return dt.astimezone(pytz.timezone('UTC'))

                msg = 'Please enter a snooze time/date in the future'
                self._errors['snooze_until'] = self.error_class([msg])

        # Check if the snooze format is a date
        date_match = match_date(data)
        if date_match is not None:
            if snooze_time is not None:
                dt = datetime.combine(date_match[0], snooze_time.time())
            else:
                dt = datetime.combine(
                    date_match[0], self.instance.localised_start().time()
                )

            usertz = pytz.timezone(timezone.get_current_timezone_name())
            dt = usertz.localize(dt)

            if dt > datetime.now(usertz):
                return dt.astimezone(pytz.timezone('UTC'))

        msg = 'Please enter a snooze time/date in the future'
        self._errors['snooze_until'] = self.error_class([msg])

    def save(self, commit=True):
        reminder = super(ExternalSnoozeForm, self).save(commit=False)
        reminder.snooze(self.cleaned_data['snooze_until'].date(),
                        self.cleaned_data['snooze_until'].time())
        return reminder
