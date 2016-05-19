from datetime import datetime, timedelta

from freezegun import freeze_time

from django.test import TestCase, Client
from django.core.urlresolvers import reverse

from accounts.models import LocalUser
from reminders.models import Reminder, WEEKDAYS, MONTHS
from timezones.models import Timezone

FROZEN_TIME = '2014-01-05 07:43:22'


class BaseTest(TestCase):
    fixtures = ['socialapp.json', 'timezones.json']

    @freeze_time(FROZEN_TIME)
    def setUp(self):
        self.client = Client()
        self.user = self.create_user('testuser', 'test@test.com')
        self.user.save()
        self.now = datetime.now()
        self.today = self.now.date()
        self.tomorrow = self.today + timedelta(days=1)
        self.user_login(username='testuser')

    def create_user(self, username, email, password='password'):
        timezone = Timezone.objects.get(name='Europe/London')
        return LocalUser.objects.create_user(
            username, email, password, timezone=timezone
        )

    @freeze_time(FROZEN_TIME)
    def user_login(self, username=None, password='password'):
        if username is None:
            username = self.user.username
        self.client.login(username=username, password=password)

    def user_logout(self):
        self.client.logout()

    def build_message(self, start_time, start_date):
        remind_on = 'on %s' % WEEKDAYS[start_date.weekday()]
        remind_at = start_time.strftime('%H:%M')
        tomorrow = self.today + timedelta(days=1)
        if start_date == self.today.date():
            remind_on = 'today'
        elif start_date == tomorrow.date():
            remind_on = 'tomorrow'
        elif start_date.isocalendar()[1] > self.today.isocalendar()[1] \
                or start_date.year > self.today.year:
            remind_on += ' %s %s' % (start_date.day, MONTHS[start_date.month])

        if start_date.year > self.today.year:
            remind_on += ' %s' % start_date.year

        return remind_at + ' ' + remind_on

    def create_reminder(self, start_date,
                        start_time, content='Test', status=2, user=None):
        if user is None:
            user = self.user

        r = Reminder(user=user, content=content, status=status,
                     start_date=start_date, start_time=start_time)
        r.save()
        return r


class ReminderDateTest(BaseTest):
    """
    Test all date formats are created successfully
    """

    def setUp(self):
        super(ReminderDateTest, self).setUp()
        self.url = reverse('new')
        self.start_time = self.now.replace(hour=23, minute=0, second=0).time()

    def get_form(self, remind_on):
        return {
            'content': 'test content',
            'remind_at': '11pm',
            'remind_on': remind_on,
        }

    @freeze_time(FROZEN_TIME)
    def test_today(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('today')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 today', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_tonight(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('tonight')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 today', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_this_evening(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('this evening')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 today', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_tonite(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('tonite')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 today', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_tomorrow(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('tomorrow')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 tomorrow', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_tmrw(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('tmrw')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 tomorrow', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_2morrow(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('2morrow')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 tomorrow', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_2mrw(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('2mrw')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 tomorrow', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_next_monday(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('next monday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 on Monday 13 January', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_next_tuesday(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('next tuesday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 on Tuesday 14 January', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_next_wednesday(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('next wednesday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 on Wednesday 15 January', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_next_thursday(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('next thursday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 on Thursday 16 January', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_next_friday(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('next friday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 on Friday 17 January', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_next_saturday(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('next saturday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('set for 23:00 on Saturday 18 January', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_next_sunday(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('next sunday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 on Sunday 12 January', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_this_monday(self):
        rcount = Reminder.objects.all().count()
        day = self.tomorrow + timedelta(days=1)
        form = self.get_form('this monday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('set for 23:00 tomorrow', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_this_tuesday(self):
        rcount = Reminder.objects.all().count()
        day = self.tomorrow + timedelta(days=1)
        form = self.get_form('this tuesday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('set for 23:00 on Tuesday', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_this_wednesday(self):
        rcount = Reminder.objects.all().count()
        day = self.tomorrow + timedelta(days=1)
        form = self.get_form('this wednesday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('set for 23:00 on Wednesday', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_this_thursday(self):
        rcount = Reminder.objects.all().count()
        day = self.tomorrow + timedelta(days=1)
        form = self.get_form('this thursday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('set for 23:00 on Thursday', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_this_friday(self):
        rcount = Reminder.objects.all().count()
        day = self.tomorrow + timedelta(days=1)
        form = self.get_form('this friday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('set for 23:00 on Friday', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_this_saturday(self):
        rcount = Reminder.objects.all().count()
        day = self.tomorrow + timedelta(days=1)
        form = self.get_form('this saturday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('set for 23:00 on Saturday', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_month_string1(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('25 April')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 on Friday 25 April', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_month_string2(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('April 25')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 on Friday 25 April', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_month_string3_past_date(self):
        rcount = Reminder.objects.all().count()
        yesterday = self.today - timedelta(days=1)
        form = self.get_form('4 January 2014')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('Please pick a date in the future', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_month_string3_future_date(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('6 January 2014')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 tomorrow', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_month_string1_this_year(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('25 April 2014')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 on Friday 25 April', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_month_string2_this_year(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('April 25 2014')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 on Friday 25 April', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_month_string1_next_year(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('25 April 2015')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 on Saturday 25 April 2015', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_month_string2_next_year(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('April 25 2015')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 on Saturday 25 April 2015', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_date_numbers_full_date(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('25/04/14')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 on Friday 25 April', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_monday(self):
        rcount = Reminder.objects.all().count()
        day = self.tomorrow + timedelta(days=1)
        form = self.get_form('monday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 tomorrow', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_tuesday(self):
        rcount = Reminder.objects.all().count()
        day = self.tomorrow + timedelta(days=1)
        form = self.get_form('tuesday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 on Tuesday 7 January', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_wednesday(self):
        rcount = Reminder.objects.all().count()
        day = self.tomorrow + timedelta(days=1)
        form = self.get_form('wednesday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 on Wednesday 8 January', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_thursday(self):
        rcount = Reminder.objects.all().count()
        day = self.tomorrow + timedelta(days=1)
        form = self.get_form('thursday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 on Thursday 9 January', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_friday(self):
        rcount = Reminder.objects.all().count()
        day = self.tomorrow + timedelta(days=1)
        form = self.get_form('friday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 on Friday 10 January', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_saturday(self):
        rcount = Reminder.objects.all().count()
        day = self.tomorrow + timedelta(days=1)
        form = self.get_form('saturday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 on Saturday 11 January', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_sunday(self):
        rcount = Reminder.objects.all().count()
        day = self.tomorrow + timedelta(days=1)
        form = self.get_form('sunday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 on Sunday 12 January', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_us_date_numbers(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('12/25')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 on Thursday 25 December', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_uk_date_numbers(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('25/12')
        date = datetime(day=25, month=12, year=self.today.year)
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 on Thursday 25 December', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_day_as_string_first(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('tenth january')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 on Friday 10 January', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_day_as_string_second(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('january first')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 on Thursday 1 January 2015', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_new_years_day(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('new years day')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 on Thursday 1 January 2015', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_new_years(self):
        form = self.get_form('new years')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 on Wednesday 31 December', response.content)

    @freeze_time(FROZEN_TIME)
    def test_christmas_day(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('christmas day')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 on Thursday 25 December', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_xmas_day(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('xmas day')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 on Thursday 25 December', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_christmas_eve(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('christmas eve')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 on Wednesday 24 December', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_xmas_eve(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('xmas eve')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 on Wednesday 24 December', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_boxing_day(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('boxing day')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 on Friday 26 December', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_valentines_day(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('valentines day')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 on Friday 14 February', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_april_fools(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('april fools day')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 on Tuesday 1 April', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_single_number(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('25th')
        response = self.client.post(self.url, form, follow=True)
        r = Reminder.objects.all().latest('created')
        self.assertIn('23:00 on Saturday 25 January', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_easter_sunday(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('easter sunday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 on Sunday 20 April', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_good_friday(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('good friday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('23:00 on Friday 18 April', response.content)
        self.assertEqual(rcount+1, Reminder.objects.all().count())


class ReminderSnoozeTest(BaseTest):
    """
    Test snoozing an already created reminder
    """

    @freeze_time(FROZEN_TIME)
    def setUp(self):
        super(ReminderSnoozeTest, self).setUp()
        time_now = self.now-timedelta(minutes=1)
        self.reminder = Reminder(user=self.user, content="test test",
                                 start_date=self.today,
                                 start_time=time_now.time())
        self.reminder.save()
        self.url = reverse('snooze', args=(self.reminder.id,))

    def get_form(self, until):
        return {
            'reminder_id': self.reminder.id,
            'snooze_until': until,
        }

    @freeze_time(FROZEN_TIME)
    def test_page_load(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    @freeze_time(FROZEN_TIME)
    def test_external_snooze_page_load(self):
        response = self.client.get(
            reverse('snooze_external',
            args=(self.reminder.hash_digest,)), follow=True
        )
        self.assertEqual(response.status_code, 200)

    @freeze_time(FROZEN_TIME)
    def test_1_minute(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('1 minute')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('snoozed until 07:44 today', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_5_minute(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('5 minutes')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('snoozed until 07:48 today', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_1_hour(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('1 hour')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('snoozed until 08:43 today', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_5_hours(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('5 hours')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('snoozed until 12:43', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_1_day(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('1 day')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('snoozed until 07:43 tomorrow', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_5_days(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('5 days')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn(
            'snoozed until 07:43 on Friday 10 January', response.content
        )
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_1_month(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('1 month')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn(
            'snoozed until 07:43 on Wednesday 5 February', response.content
        )
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_5_months(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('5 months')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn(
            'snoozed until 08:43 on Thursday 5 June', response.content
        )
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_1_year(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('1 year')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn(
            'snoozed until 07:43 on Monday 5 January 2015', response.content
        )
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_5_years(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('5 years')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('snoozed until 07:43 on Saturday 5 January 2019',
                      response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_am(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('8am')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('snoozed until 08:00 today', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_pm(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('11pm')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('snoozed until 23:00 today', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_full_time(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('11:59pm')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('snoozed until 23:59 today', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_full_time_twenty_four_hour(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('23:59')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('snoozed until 23:59 today', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_tomorrow(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('tomorrow')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 tomorrow', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_tmrw(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('tmrw')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 tomorrow', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_2morrow(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('2morrow')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 tomorrow', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_2mrw(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('2mrw')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 tomorrow', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_next_monday(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('next monday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 on Monday 13 January', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_next_tuesday(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('next tuesday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 on Tuesday 14 January', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_next_wednesday(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('next wednesday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 on Wednesday 15 January', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_next_thursday(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('next thursday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 on Thursday 16 January', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_next_friday(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('next friday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 on Friday 17 January', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_next_saturday(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('next saturday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 on Saturday 18 January', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_next_sunday(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('next sunday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 on Sunday 12 January', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_this_monday(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('this monday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 tomorrow', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_this_tuesday(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('this tuesday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 on Tuesday 7 January', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_this_wednesday(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('this wednesday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 on Wednesday 8 January', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_this_thursday(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('this thursday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 on Thursday 9 January', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_this_friday(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('this friday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 on Friday 10 January', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_this_saturday(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('this saturday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 on Saturday 11 January', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_this_sunday(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('this sunday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 on Sunday 12 January', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_month_string1(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('25 April')
        response = self.client.post(self.url, form, follow=True)
        st = self.reminder.localised_start()
        self.assertIn('07:42 on Friday 25 April', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_month_string2(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('April 25')
        response = self.client.post(self.url, form, follow=True)
        st = self.reminder.localised_start()
        self.assertIn('07:42 on Friday 25 April', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_date_numbers_full_date(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('25/04/14')
        response = self.client.post(self.url, form, follow=True)
        st = self.reminder.localised_start()
        self.assertIn('07:42 on Friday 25 April', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_monday(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('Monday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 tomorrow', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_tuesday(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('Tuesday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 on Tuesday 7 January', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_wednesday(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('Wednesday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 on Wednesday 8 January', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_thursday(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('Thursday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 on Thursday 9 January', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_friday(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('Friday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 on Friday 10 January', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_saturday(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('Saturday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 on Saturday 11 January', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_sunday(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('Sunday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 on Sunday 12 January', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_us_date_numbers(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('12/25')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 on Thursday 25 December', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_uk_date_numbers(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('25/12')
        date = datetime(day=25, month=12, year=self.today.year)
        response = self.client.post(self.url, form, follow=True)
        st = self.reminder.localised_start()
        self.assertIn('07:42 on Thursday 25 December', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_day_as_string_first(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('first january')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 on Thursday 1 January 2015', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_day_as_string_second(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('january first')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 on Thursday 1 January 2015', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_new_years_day(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('new years day')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 on Thursday 1 January 2015', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_new_years(self):
        form = self.get_form('new years')
        date = datetime(self.today.year, 12, 31)
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 on Wednesday 31 December', response.content)

    @freeze_time(FROZEN_TIME)
    def test_christmas_day(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('christmas day')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 on Thursday 25 December', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_xmas_day(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('xmas day')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 on Thursday 25 December', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_christmas_eve(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('christmas eve')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 on Wednesday 24 December', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_xmas_eve(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('xmas eve')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 on Wednesday 24 December', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_boxing_day(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('boxing day')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 on Friday 26 December', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_valentines_day(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('valentines day')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 on Friday 14 February', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_april_fools(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('april fools day')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 on Tuesday 1 April', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_single_number(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('25th')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 on Saturday 25 January', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_easter_sunday(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('easter sunday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 on Sunday 20 April', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_good_friday(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('good friday')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('07:42 on Friday 18 April', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    # Test bug where snoozing till 06:58 at 06:56 failed
    @freeze_time('2014-01-05 06:56:02')
    def test_two_minute_snooze(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('06:58')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('06:58 today', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())
        updated = Reminder.objects.get(pk=self.reminder.id)
        self.assertEqual(updated.localised_start().day, 5)
        self.assertEqual(updated.localised_start().month, 1)
        self.assertEqual(updated.localised_start().year, 2014)
        self.assertEqual(updated.localised_start().hour, 6)
        self.assertEqual(updated.localised_start().minute, 58)

    @freeze_time(FROZEN_TIME)
    def test_snooze_4pm(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('4pm')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('snoozed until 16:00 today', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_snooze_7pm(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('7pm')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('snoozed until 19:00 today', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_1_hour(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('1 hour')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('snoozed until 08:43', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_2_hours(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('2 hours')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('snoozed until 09:43', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_1_day(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('1 day')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn('snoozed until 07:43 tomorrow', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_2_days(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('2 days')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn(
            'snoozed until 07:43 on Tuesday 7 January', response.content
        )
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_1_week(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('1 week')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn(
            'snoozed until 07:43 on Sunday 12 January', response.content
        )
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_2_weeks(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('2 weeks')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn(
            'snoozed until 07:43 on Sunday 19 January', response.content
        )
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_2_months(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form('2 months')
        response = self.client.post(self.url, form, follow=True)
        self.assertIn(
            'snoozed until 07:43 on Wednesday 5 March', response.content
        )
        self.assertEqual(rcount, Reminder.objects.all().count())


class RemindersTest(BaseTest):
    """
    Test reminder listings
    """

    def setUp(self):
        super(RemindersTest, self).setUp()
        self.url = reverse('reminders')

    @freeze_time(FROZEN_TIME)
    def test_overdue_redirect(self):
        st = datetime.now() - timedelta(days=1)
        r = self.create_reminder(st.date(), st.time(), content='test overdue')
        r.overdue()
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, reverse('overdue'))
        datestr = r.full_start_datetime.strftime('%d %b %Y')
        self.assertIn(datestr, response.content)

    @freeze_time(FROZEN_TIME)
    def test_upcoming_redirect(self):
        st = datetime.now() + timedelta(days=1)
        r = self.create_reminder(st.date(), st.time(),
                                 content='test outstanding', status=2)
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, reverse('upcoming'))
        self.assertIn('Tomorrow', response.content)

    @freeze_time(FROZEN_TIME)
    def test_overdue(self):
        st = datetime.now() - timedelta(days=1)
        r = self.create_reminder(st.date(), st.time(), content='test overdue')
        r.overdue()
        response = self.client.get(reverse('overdue'))
        self.assertEqual(response.status_code, 200)
        datestr = r.full_start_datetime.strftime('%d %b %Y')
        self.assertIn(datestr, response.content)
        self.assertIn('test overdue', response.content)

    @freeze_time(FROZEN_TIME)
    def test_overdue_none_exist(self):
        Reminder.objects.filter(user=self.user).delete()
        response = self.client.get(reverse('overdue'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'You don\'t have any overdue reminders', response.content
        )

    @freeze_time(FROZEN_TIME)
    def test_upcoming(self):
        st = datetime.now() + timedelta(days=1)
        r = self.create_reminder(st.date(), st.time(),
                                 content='test upcoming')
        response = self.client.get(reverse('upcoming'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Tomorrow', response.content)
        self.assertIn('test upcoming', response.content)

    @freeze_time(FROZEN_TIME)
    def test_upcoming_none_exist(self):
        Reminder.objects.filter(user=self.user).delete()
        response = self.client.get(reverse('upcoming'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'You don\'t have any upcoming reminders', response.content
        )

    @freeze_time(FROZEN_TIME)
    def test_paused(self):
        st = datetime.now() + timedelta(days=1)
        r = self.create_reminder(st.date(), st.time(),
                                 content='test paused', status=1)
        r.pause()
        response = self.client.get(reverse('paused'))
        self.assertEqual(response.status_code, 200)
        datestr = r.full_start_datetime.strftime('%d %b %Y')
        self.assertIn(datestr, response.content)
        self.assertIn('test paused', response.content)

    @freeze_time(FROZEN_TIME)
    def test_paused_none_exist(self):
        Reminder.objects.filter(user=self.user).delete()
        response = self.client.get(reverse('paused'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('You don\'t have any paused reminders', response.content)

    @freeze_time(FROZEN_TIME)
    def test_completed(self):
        st = datetime.now() - timedelta(days=1)
        r = self.create_reminder(st.date(), st.time(),
                                 content='test completed')
        r.complete()
        response = self.client.get(reverse('completed'))
        self.assertEqual(response.status_code, 200)
        datestr = r.completion_date.strftime('%d %b %Y')
        self.assertIn(datestr, response.content)
        self.assertIn('test completed', response.content)

    @freeze_time(FROZEN_TIME)
    def test_completed_none_exist(self):
        Reminder.objects.filter(user=self.user).delete()
        response = self.client.get(reverse('completed'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'You don\'t have any completed reminders', response.content
        )

    @freeze_time(FROZEN_TIME)
    def test_overdue_edit(self):
        st = datetime.now() - timedelta(hours=1)
        r = self.create_reminder(st.date(), st.time(), content='test overdue')
        response = self.client.get(reverse('edit', args=(r.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertIn('test overdue', response.content)
        self.assertIn('Update Reminder', response.content)

    @freeze_time(FROZEN_TIME)
    def test_overdue_edit_update(self):
        st = datetime.now() - timedelta(hours=1)
        r = self.create_reminder(st.date(), st.time(), content='test overdue')
        r.overdue()
        rcount = Reminder.objects.filter(deleted=False).count()
        r.complete()
        form = {
            'id': r.id,
            'remind_on': 'tomorrow',
            'remind_at': '10pm',
            'content': 'updated reminder',
        }
        response = self.client.post(
            reverse('edit', args=(r.id,)), form, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('edited and set for 22:00 tomorrow', response.content)
        self.assertIn('updated reminder', response.content)
        self.assertEqual(
            rcount, Reminder.objects.filter(deleted=False).count()
        )

    @freeze_time(FROZEN_TIME)
    def test_overdue_confirm_delete(self):
        st = datetime.now() - timedelta(hours=1)
        r = self.create_reminder(st.date(), st.time())
        rcount = Reminder.objects.filter(deleted=False).count()
        response = self.client.get(
            reverse('delete', args=(r.id,)), follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'Are you sure you want to delete the below reminder?',
            response.content
        )
        self.assertIn(r.content, response.content)
        self.assertEqual(
            rcount, Reminder.objects.filter(deleted=False).count()
        )

    @freeze_time(FROZEN_TIME)
    def test_overdue_delete(self):
        st = datetime.now() - timedelta(hours=1)
        r = self.create_reminder(st.date(), st.time())
        rcount = Reminder.objects.filter(deleted=False).count()
        response = self.client.post(
            reverse('delete', args=(r.id,)), {}, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('Reminder deleted successfully', response.content)
        self.assertEqual(
            rcount-1, Reminder.objects.filter(deleted=False).count()
        )

    @freeze_time(FROZEN_TIME)
    def test_overdue_complete(self):
        st = datetime.now() - timedelta(hours=1)
        r = self.create_reminder(st.date(), st.time())
        rcount = Reminder.objects.all().count()
        response = self.client.get(
            reverse('complete', args=(r.id,)), follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'Are you sure you want to complete the below reminder',
            response.content
        )
        self.assertIn(r.content, response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_upcoming_edit(self):
        st = datetime.now() + timedelta(hours=1)
        r = self.create_reminder(st.date(), st.time(), content='test upcoming')
        response = self.client.get(reverse('edit', args=(r.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertIn('test upcoming', response.content)
        self.assertIn('Update Reminder', response.content)

    @freeze_time(FROZEN_TIME)
    def test_upcoming_edit_update(self):
        st = datetime.now() + timedelta(hours=1)
        r = self.create_reminder(st.date(), st.time(), content='test updated')
        rcount = Reminder.objects.filter(deleted=False).count()
        r.complete()
        form = {
            'id': r.id,
            'remind_on': 'tomorrow',
            'remind_at': '10pm',
            'content': 'updated reminder',
        }
        response = self.client.post(
            reverse('edit', args=(r.id,)), form, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('edited and set for 22:00 tomorrow', response.content)
        self.assertIn('updated reminder', response.content)
        self.assertEqual(rcount, Reminder.objects.filter(deleted=False).count())

    @freeze_time(FROZEN_TIME)
    def test_upcoming_confirm_delete(self):
        st = datetime.now() + timedelta(hours=1)
        r = self.create_reminder(st.date(), st.time())
        rcount = Reminder.objects.filter(deleted=False).count()
        response = self.client.get(reverse('delete', args=(r.id,)), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'Are you sure you want to delete the below reminder?',
            response.content
        )
        self.assertIn(r.content, response.content)
        self.assertEqual(rcount, Reminder.objects.filter(deleted=False).count())

    @freeze_time(FROZEN_TIME)
    def test_upcoming_delete(self):
        st = datetime.now() + timedelta(hours=1)
        r = self.create_reminder(st.date(), st.time())
        rcount = Reminder.objects.filter(deleted=False).count()
        response = self.client.post(
            reverse('delete', args=(r.id,)), {}, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('Reminder deleted successfully', response.content)
        self.assertEqual(
            rcount-1, Reminder.objects.filter(deleted=False).count()
        )

    @freeze_time(FROZEN_TIME)
    def test_completed_edit(self):
        st = datetime.now() + timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(), content='test completed'
        )
        r.complete()
        response = self.client.get(reverse('edit', args=(r.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertIn('test completed', response.content)
        self.assertIn('Update Reminder', response.content)

    @freeze_time(FROZEN_TIME)
    def test_completed_edit_update(self):
        st = datetime.now() + timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(), content='test completed'
        )
        rcount = Reminder.objects.filter(deleted=False).count()
        r.complete()
        form = {
            'id': r.id,
            'remind_on': 'tomorrow',
            'remind_at': '10pm',
            'content': 'updated reminder',
        }
        response = self.client.post(
            reverse('edit', args=(r.id,)), form, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('edited and set for 22:00 tomorrow', response.content)
        self.assertIn('updated reminder', response.content)
        self.assertEqual(
            rcount, Reminder.objects.filter(deleted=False).count()
        )

    @freeze_time(FROZEN_TIME)
    def test_completed_confirm_delete(self):
        st = datetime.now() + timedelta(hours=1)
        r = self.create_reminder(st.date(), st.time())
        r.complete()
        rcount = Reminder.objects.filter(deleted=False).count()
        response = self.client.get(
            reverse('delete', args=(r.id,)), follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'Are you sure you want to delete the below reminder?',
            response.content
        )
        self.assertIn(r.content, response.content)
        self.assertEqual(
            rcount, Reminder.objects.filter(deleted=False).count()
        )

    @freeze_time(FROZEN_TIME)
    def test_completed_delete(self):
        st = datetime.now() + timedelta(hours=1)
        r = self.create_reminder(st.date(), st.time())
        r.complete()
        rcount = Reminder.objects.filter(deleted=False).count()
        response = self.client.post(
            reverse('delete', args=(r.id,)), {}, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('Reminder deleted successfully', response.content)
        self.assertEqual(
            rcount-1, Reminder.objects.filter(deleted=False).count()
        )

    @freeze_time(FROZEN_TIME)
    def test_paused_edit(self):
        st = datetime.now() + timedelta(hours=1)
        r = self.create_reminder(st.date(), st.time(), content='test paused')
        r.pause()
        response = self.client.get(reverse('edit', args=(r.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertIn('test paused', response.content)
        self.assertIn('Update Reminder', response.content)

    @freeze_time(FROZEN_TIME)
    def test_paused_edit_update(self):
        st = datetime.now() + timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(), content='test completed'
        )
        rcount = Reminder.objects.filter(deleted=False).count()
        r.pause()
        form = {
            'id': r.id,
            'remind_on': 'tomorrow',
            'remind_at': '10pm',
            'content': 'updated reminder',
        }
        response = self.client.post(
            reverse('edit', args=(r.id,)), form, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('edited and set for 22:00 tomorrow', response.content)
        self.assertIn('updated reminder', response.content)
        self.assertEqual(
            rcount, Reminder.objects.filter(deleted=False).count()
        )

    @freeze_time(FROZEN_TIME)
    def test_paused_confirm_delete(self):
        st = datetime.now() + timedelta(hours=1)
        r = self.create_reminder(st.date(), st.time())
        r.pause()
        rcount = Reminder.objects.filter(deleted=False).count()
        response = self.client.get(
            reverse('delete', args=(r.id,)), follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'Are you sure you want to delete the below reminder?',
            response.content
        )
        self.assertIn(r.content, response.content)
        self.assertEqual(
            rcount, Reminder.objects.filter(deleted=False).count()
        )

    @freeze_time(FROZEN_TIME)
    def test_paused_delete(self):
        st = datetime.now() + timedelta(hours=1)
        r = self.create_reminder(st.date(), st.time())
        r.pause()
        rcount = Reminder.objects.filter(deleted=False).count()
        response = self.client.post(
            reverse('delete', args=(r.id,)), {}, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('Reminder deleted successfully', response.content)
        self.assertEqual(
            rcount-1, Reminder.objects.filter(deleted=False).count()
        )


class ReminderDetailTest(BaseTest):
    """
    Test reminder listings
    """
    def setUp(self):
        super(ReminderDetailTest, self).setUp()
        self.now = datetime.now()
        self.today = datetime.today()
        self.tomorrow = self.today + timedelta(days=1)

    @freeze_time(FROZEN_TIME)
    def test_non_existent_reminder(self):
        response = self.client.get(reverse('reminder', args=(999,)))
        self.assertEqual(response.status_code, 404)

    @freeze_time(FROZEN_TIME)
    def test_other_users_reminder(self):
        st = datetime.now() + timedelta(hours=1)
        user = self.create_user('test2', 'test2@test.com')
        r = self.create_reminder(st.date(), st.time(), user=user)
        response = self.client.get(reverse('reminder', args=(r.id,)))
        self.assertEqual(response.status_code, 404)

    @freeze_time(FROZEN_TIME)
    def test_not_logged_in_reminder(self):
        self.user_logout()
        st = datetime.now() + timedelta(hours=1)
        r = self.create_reminder(st.date(), st.time())
        url = reverse('reminder', args=(r.id,))
        response = self.client.get(url, follow=True)
        self.assertRedirects(
            response, reverse('account_login') + '?next=' + url
        )

    @freeze_time(FROZEN_TIME)
    def test_outstanding_reminder(self):
        st = datetime.now() + timedelta(hours=1)
        r = self.create_reminder(st.date(), st.time())
        response = self.client.get(reverse('reminder', args=(r.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Live', response.content)

    @freeze_time(FROZEN_TIME)
    def test_overdue_reminder(self):
        st = datetime.now() - timedelta(hours=1)
        r = self.create_reminder(st.date(), st.time())
        r.overdue()
        response = self.client.get(reverse('reminder', args=(r.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Overdue', response.content)

    @freeze_time(FROZEN_TIME)
    def test_completed_reminder(self):
        st = datetime.now() - timedelta(hours=1)
        r = self.create_reminder(st.date(), st.time())
        r.complete()
        response = self.client.get(reverse('reminder', args=(r.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Completed', response.content)

    @freeze_time(FROZEN_TIME)
    def test_deleted_reminder(self):
        st = datetime.now() - timedelta(hours=1)
        r = self.create_reminder(st.date(), st.time())
        r.soft_delete()
        response = self.client.get(reverse('reminder', args=(r.id,)))
        self.assertEqual(response.status_code, 404)


class ReminderMultiDeleteTest(BaseTest):
    """
    Test deleting 1 or more reminders
    """

    @freeze_time(FROZEN_TIME)
    def test_delete_invalid_id(self):
        rcount = Reminder.objects.filter(deleted=False).count()
        st = datetime.now() + timedelta(hours=1)
        form = {'reminder_ids': '9999,8888'}
        response = self.client.post(
            reverse('delete_multiple'), form, follow=True
        )
        self.assertEqual(response.status_code, 404)

    @freeze_time(FROZEN_TIME)
    def test_delete_non_owned_reminders(self):
        user = self.create_user('test2', 'test2@test.com')
        st = datetime.now() + timedelta(hours=1)
        with freeze_time('2014-01-05 07:43:23'):
            r1 = self.create_reminder(st.date(), st.time(), user=user)
            with freeze_time('2014-01-05 07:43:24'):
                r2 = self.create_reminder(st.date(), st.time(), user=user)
                rcount = Reminder.objects.filter(deleted=False).count()
                form = {'reminder_ids': ','.join([str(r1.id), str(r2.id)])}
                response = self.client.post(
                    reverse('delete_multiple'), form, follow=True
                )
                self.assertEqual(response.status_code, 404)

    @freeze_time(FROZEN_TIME)
    def test_completed_delete(self):
        rcount = Reminder.objects.filter(deleted=False).count()
        st = datetime.now() + timedelta(hours=1)
        with freeze_time('2014-01-05 07:43:23'):
            r1 = self.create_reminder(st.date(), st.time())
            r1.complete()
            with freeze_time('2014-01-05 07:43:24'):
                r2 = self.create_reminder(st.date(), st.time())
                r2.complete()
                form = {'reminder_ids': ','.join([str(r1.id), str(r2.id)])}
                response = self.client.post(
                    reverse('delete_multiple'), form, follow=True
                )
                self.assertEqual(response.status_code, 200)
                self.assertIn(
                    '2 reminders deleted successfully', response.content
                )
                self.assertEqual(
                    rcount, Reminder.objects.filter(deleted=False).count()
                )

    @freeze_time(FROZEN_TIME)
    def test_upcoming_delete(self):
        rcount = Reminder.objects.filter(deleted=False).count()
        st = datetime.now() + timedelta(hours=1)
        with freeze_time('2014-01-05 07:43:23'):
            r1 = self.create_reminder(st.date(), st.time())
            with freeze_time('2014-01-05 07:43:24'):
                r2 = self.create_reminder(st.date(), st.time())
                form = {'reminder_ids': ','.join([str(r1.id), str(r2.id)])}
                response = self.client.post(
                    reverse('delete_multiple'), form, follow=True
                )
                self.assertEqual(response.status_code, 200)
                self.assertIn(
                    '2 reminders deleted successfully', response.content
                )
                self.assertEqual(
                    rcount, Reminder.objects.filter(deleted=False).count()
                )

    @freeze_time(FROZEN_TIME)
    def test_overdue_delete(self):
        rcount = Reminder.objects.filter(deleted=False).count()
        st = datetime.now() - timedelta(hours=1)
        with freeze_time('2014-01-05 07:43:23'):
            r1 = self.create_reminder(st.date(), st.time())
            r1.overdue()
            with freeze_time('2014-01-05 07:43:24'):
                r2 = self.create_reminder(st.date(), st.time())
                r2.overdue()
                form = {'reminder_ids': ','.join([str(r1.id), str(r2.id)])}
                response = self.client.post(
                    reverse('delete_multiple'), form, follow=True
                )
                self.assertEqual(response.status_code, 200)
                self.assertIn(
                    '2 reminders deleted successfully', response.content
                )
                self.assertEqual(
                    rcount, Reminder.objects.filter(deleted=False).count()
                )


class GenericPagesTest(BaseTest):
    """
    Test generic pages
    """

    def test_about_page(self):
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)

    def test_privacy_page(self):
        response = self.client.get(reverse('privacy'))
        self.assertEqual(response.status_code, 200)

    def test_terms_page(self):
        response = self.client.get(reverse('terms'))
        self.assertEqual(response.status_code, 200)


class QuickAddReminderTest(BaseTest):
    """
    Test quick added reminders are created as expected
    """

    def setUp(self):
        super(QuickAddReminderTest, self).setUp()
        self.url = reverse('dashboard')
        self.start_time = self.now.replace(hour=23, minute=0, second=0).time()
        self.content = 'Test Reminder Content'

    def _make_request(self, content):
        form = {'content': content}
        return self.client.post(self.url, form, follow=True)

    @freeze_time(FROZEN_TIME)
    def test_no_date_or_time(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertIn('Please enter a reminder time', response.content)

    @freeze_time(FROZEN_TIME)
    def test_no_date(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 11:59pm')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        self.assertIn('set for 23:59 today', response.content)

    @freeze_time(FROZEN_TIME)
    def test_no_time(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' Friday')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertIn('Please enter a reminder time', response.content)

    @freeze_time(FROZEN_TIME)
    def test_easter_sunday_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('2pm easter sunday ' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 14:00 on Sunday 20 April', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_easter_sunday_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 2pm easter sunday')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 14:00 on Sunday 20 April', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_good_friday_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('2pm good friday' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 14:00 on Friday 18 April', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_good_friday_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 2pm good friday')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 14:00 on Friday 18 April', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_today_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('23:59 today' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 23:59 today', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_today_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 23:59 today')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 23:59 today', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_tonight_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('11:59pm tonight' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 23:59 today', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_tonight_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 11:59pm tonight')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 23:59 today', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_tomorrow_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('1:59pm tomorrow ' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 tomorrow', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_tomorrow_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 1:59pm tomorrow')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 tomorrow', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_monday_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('1:59pm monday ' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 tomorrow', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_monday_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 1:59pm monday')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 tomorrow', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_tuesday_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('1:59pm tuesday ' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Tuesday 7 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_tuesday_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 1:59pm tuesday')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Tuesday 7 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_wednesday_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('1:59pm wednesday ' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Wednesday 8 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_wednesday_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 1:59pm wednesday')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Wednesday 8 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_thursday_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('1:59pm thursday ' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Thursday 9 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_thursday_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 1:59pm thursday')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Thursday 9 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_friday_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('1:59pm friday ' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Friday 10 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_friday_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 1:59pm friday')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Friday 10 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_saturday_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('1:59pm saturday ' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Saturday 11 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_saturday_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 1:59pm saturday')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Saturday 11 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_sunday_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('1:59pm sunday ' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Sunday 12 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_sunday_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 1:59pm sunday')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Sunday 12 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_this_monday_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('1:59pm this monday ' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 tomorrow', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_this_monday_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 1:59pm this monday')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 tomorrow', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_this_tuesday_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('1:59pm this tuesday ' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Tuesday 7 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_this_tuesday_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 1:59pm this tuesday')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Tuesday 7 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_this_wednesday_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('1:59pm this wednesday ' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Wednesday 8 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_this_wednesday_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 1:59pm this wednesday')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Wednesday 8 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_this_thursday_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('1:59pm this thursday ' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Thursday 9 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_this_thursday_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 1:59pm this thursday')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Thursday 9 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_this_friday_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('1:59pm this friday ' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Friday 10 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_this_friday_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 1:59pm this friday')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Friday 10 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_this_saturday_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('1:59pm this saturday ' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Saturday 11 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_this_saturday_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 1:59pm this saturday')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Saturday 11 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_this_sunday_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('1:59pm this sunday ' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Sunday 12 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_this_sunday_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 1:59pm this sunday')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Sunday 12 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_month_full_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('1:59pm 25 April' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Friday 25 April', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_month_full_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 1:59pm 25 December')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Thursday 25 December', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_us_month_full_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('1:59pm April 25' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Friday 25 April', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_us_month_full_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 1:59pm December 25')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn(
            'set for 13:59 on Thursday 25 December', response.content
        )
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_full_date_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('1:59pm 25/04/2015' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn(
            'set for 13:59 on Saturday 25 April 2015',
            response.content
        )
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_full_date_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 1:59pm 25/12/2015')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn(
            'set for 13:59 on Friday 25 December 2015', response.content
        )
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_short_month_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('1:59pm 1 May' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59', response.content)
        self.assertIn('set for 13:59 on Thursday 1 May', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_short_month_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 1:59pm 22 May')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Thursday 22 May', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_month_year_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('1:59pm 25/04' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59', response.content)
        self.assertIn('set for 13:59 on Friday 25 April', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_month_year_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 1:59pm 25/12')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn(
            'set for 13:59 on Thursday 25 December', response.content
        )
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_us_month_year_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('1:59pm 04/25' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Friday 25 April', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_us_month_year_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 1:59pm 12/20')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn(
            'set for 13:59 on Saturday 20 December', response.content
        )
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_us_short_month_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('1:59pm Jan 1' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn(
            'set for 13:59 on Thursday 1 January 2015', response.content
        )
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_us_short_month_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 1:59pm Jan 22')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Wednesday 22 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_new_years_day_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('1:59pm new years day' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn(
            'set for 13:59 on Thursday 1 January 2015', response.content
        )
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_new_years_day_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 1:59pm new years day')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn(
            'set for 13:59 on Thursday 1 January 2015', response.content
        )
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_new_years_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('1:59pm new years' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn(
            'set for 13:59 on Wednesday 31 December', response.content
        )
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_new_years_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 1:59pm new years')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn(
            'set for 13:59 on Wednesday 31 December', response.content
        )
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_christmas_day_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('1:59pm christmas day' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn(
            'set for 13:59 on Thursday 25 December', response.content
        )
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_christmas_day_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 1:59pm christmas day')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn(
            'set for 13:59 on Thursday 25 December', response.content
        )
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_xmas_day_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('1:59pm xmas day' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn(
            'set for 13:59 on Thursday 25 December', response.content
        )
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_xmas_day_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 1:59pm xmas day')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn(
            'set for 13:59 on Thursday 25 December', response.content
        )
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_christmas_eve_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('1:59pm christmas eve' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn(
            'set for 13:59 on Wednesday 24 December', response.content
        )
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_christmas_eve_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 1:59pm christmas eve')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn(
            'set for 13:59 on Wednesday 24 December', response.content
        )
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_xmas_eve_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('1:59pm xmas eve' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn(
            'set for 13:59 on Wednesday 24 December', response.content
        )
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_xmas_eve_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 1:59pm xmas eve')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn(
            'set for 13:59 on Wednesday 24 December', response.content
        )
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_boxing_day_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('1:59pm boxing day' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Friday 26 December', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_boxing_day_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 1:59pm boxing day')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Friday 26 December', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_valentines_day_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('1:59pm valentines day' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Friday 14 February', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_valentines_day_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 1:59pm valentines day')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Friday 14 February', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_april_fools_day_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('1:59pm april fools day' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Tuesday 1 April', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_april_fools_day_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 1:59pm april fools day')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Tuesday 1 April', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_single_number_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('1:59pm 25th' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Saturday 25 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_single_number_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 1:59pm 25th')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Saturday 25 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_single_number_dotted_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('1.59pm 25th' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Saturday 25 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_single_number_dotted_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 1.59pm 25th')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 13:59 on Saturday 25 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_double_digit_am_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('22 April 8am ' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 08:00 on Tuesday 22 April', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.localised_start().day, 22)
        self.assertEqual(r.localised_start().month, 4)
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_double_digit_am_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 22 April 8am')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 08:00 on Tuesday 22 April', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.localised_start().day, 22)
        self.assertEqual(r.localised_start().month, 4)
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_double_digit_pm_before(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('tomorrow 12pm ' + self.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 12:00 tomorrow', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.localised_start().day, 6)
        self.assertEqual(r.localised_start().month, 1)
        self.assertEqual(r.content, self.content)

    @freeze_time(FROZEN_TIME)
    def test_double_digit_pm_after(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request(self.content + ' 12pm tomorrow')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 12:00 tomorrow', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.localised_start().day, 6)
        self.assertEqual(r.localised_start().month, 1)
        self.assertEqual(r.content, self.content)


    @freeze_time(FROZEN_TIME)
    def test_call_the_bank(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('2pm call the bank')
        r = Reminder.objects.latest('created')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 14:00 today', response.content)
        self.assertEqual(r.localised_start().day, self.today.day)
        self.assertEqual(r.localised_start().month, self.today.month)
        self.assertEqual(r.content, 'call the bank')

    # 15:00 take the kids to the pool
    @freeze_time(FROZEN_TIME)
    def test_kids_to_pool(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('15:00 take the kids to the pool')
        r = Reminder.objects.latest('created')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 15:00 today', response.content)
        self.assertEqual(r.localised_start().day, self.today.day)
        self.assertEqual(r.localised_start().month, self.today.month)
        self.assertEqual(r.content, 'take the kids to the pool')

    # Midday put the dinner on
    @freeze_time(FROZEN_TIME)
    def test_put_the_dinner_on(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('Midday put the dinner on')
        r = Reminder.objects.latest('created')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 12:00 today', response.content)
        self.assertEqual(r.localised_start().day, self.today.day)
        self.assertEqual(r.localised_start().month, self.today.month)
        self.assertEqual(r.content, 'put the dinner on')

    # Email Bob Monday 10am
    @freeze_time(FROZEN_TIME)
    def test_email_bob_on_monday(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('Email Bob Monday 10am')
        r = Reminder.objects.latest('created')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 10:00 tomorrow', response.content)
        self.assertEqual(r.localised_start().day, self.tomorrow.day)
        self.assertEqual(r.localised_start().month, self.tomorrow.month)
        self.assertEqual(r.content, 'Email Bob')

    # Call Cindy 18:30 next Monday
    @freeze_time(FROZEN_TIME)
    def test_next_monday(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('Call Cindy 18:30 next Monday')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 18:30 on Monday 13 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.localised_start().day, 13)
        self.assertEqual(r.localised_start().month, 1)
        self.assertEqual(r.content, 'Call Cindy')

    @freeze_time(FROZEN_TIME)
    def test_next_tuesday(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('Call Cindy 07:00 next Tuesday')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 07:00 on Tuesday 14 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.localised_start().day, 14)
        self.assertEqual(r.localised_start().month, 1)
        self.assertEqual(r.content, 'Call Cindy')

    @freeze_time(FROZEN_TIME)
    def test_next_wednesday(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('Call Cindy 22:53 next Wednesday')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 22:53 on Wednesday 15 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.localised_start().day, 15)
        self.assertEqual(r.localised_start().month, 1)
        self.assertEqual(r.content, 'Call Cindy')

    @freeze_time(FROZEN_TIME)
    def test_next_thursday(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('Call Cindy 11:13 next Thursday')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 11:13 on Thursday 16 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.localised_start().day, 16)
        self.assertEqual(r.localised_start().month, 1)
        self.assertEqual(r.content, 'Call Cindy')

    @freeze_time(FROZEN_TIME)
    def test_next_friday(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('Call Cindy 1:17 next Friday')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 01:17 on Friday 17 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.localised_start().day, 17)
        self.assertEqual(r.localised_start().month, 1)
        self.assertEqual(r.content, 'Call Cindy')

    @freeze_time(FROZEN_TIME)
    def test_next_saturday(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('Call Cindy 1:17 next Saturday')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 01:17 on Saturday 18 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.localised_start().day, 18)
        self.assertEqual(r.localised_start().month, 1)
        self.assertEqual(r.content, 'Call Cindy')

    @freeze_time(FROZEN_TIME)
    def test_next_sunday(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('Call Cindy 3:33 next Sunday')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 03:33 on Sunday 12 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.localised_start().day, 12)
        self.assertEqual(r.localised_start().month, 1)
        self.assertEqual(r.content, 'Call Cindy')

    # 02/12/14 6am walk the dog
    @freeze_time(FROZEN_TIME)
    def test_2_december(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('02/12/14 6am walk the dog')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 06:00 on Tuesday 2 December', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.localised_start().day, 2)
        self.assertEqual(r.localised_start().month, 12)
        self.assertEqual(r.content, 'walk the dog')

    # Start dancing 8pm new years eve
    @freeze_time(FROZEN_TIME)
    def test_8pm_new_years_eve(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('Start dancing 8pm new years eve')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn(
            'set for 20:00 on Wednesday 31 December', response.content
        )
        r = Reminder.objects.latest('created')
        self.assertEqual(r.localised_start().day, 31)
        self.assertEqual(r.localised_start().month, 12)
        self.assertEqual(r.content, 'Start dancing')

    @freeze_time(FROZEN_TIME)
    def test_dotted_time(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('Call Cindy 11.13am next Thursday')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 11:13 on Thursday 16 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.localised_start().day, 16)
        self.assertEqual(r.localised_start().month, 1)
        self.assertEqual(r.content, 'Call Cindy')

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_mon(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('Short date test 18:30 mon')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 18:30 tomorrow', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.localised_start().day, 6)
        self.assertEqual(r.localised_start().month, 1)
        self.assertEqual(r.content, 'Short date test')

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_tue(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('Short date test 18:30 tue')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 18:30 on Tuesday 7 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.localised_start().day, 7)
        self.assertEqual(r.localised_start().month, 1)
        self.assertEqual(r.content, 'Short date test')

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_tues(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('Short date test 18:30 tues')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 18:30 on Tuesday 7 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.localised_start().day, 7)
        self.assertEqual(r.localised_start().month, 1)
        self.assertEqual(r.content, 'Short date test')

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_wed(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('Short date test 18:30 wed')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 18:30 on Wednesday 8 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.localised_start().day, 8)
        self.assertEqual(r.localised_start().month, 1)
        self.assertEqual(r.content, 'Short date test')

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_weds(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('Short date test 18:30 weds')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 18:30 on Wednesday 8 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.localised_start().day, 8)
        self.assertEqual(r.localised_start().month, 1)
        self.assertEqual(r.content, 'Short date test')

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_thur(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('Short date test 18:30 thur')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 18:30 on Thursday 9 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.localised_start().day, 9)
        self.assertEqual(r.localised_start().month, 1)
        self.assertEqual(r.content, 'Short date test')

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_thurs(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('Short date test 18:30 thur')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 18:30 on Thursday 9 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.localised_start().day, 9)
        self.assertEqual(r.localised_start().month, 1)
        self.assertEqual(r.content, 'Short date test')

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_fri(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('Short date test 18:30 fri')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 18:30 on Friday 10 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.localised_start().day, 10)
        self.assertEqual(r.localised_start().month, 1)
        self.assertEqual(r.content, 'Short date test')

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_sat(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('Short date test 18:30 sat')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 18:30 on Saturday 11 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.localised_start().day, 11)
        self.assertEqual(r.localised_start().month, 1)
        self.assertEqual(r.content, 'Short date test')

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_satday(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('Short date test 18:30 satday')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 18:30 on Saturday 11 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.localised_start().day, 11)
        self.assertEqual(r.localised_start().month, 1)
        self.assertEqual(r.content, 'Short date test')

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_sun(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('Short date test 18:30 sun')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 18:30 on Sunday 12 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.localised_start().day, 12)
        self.assertEqual(r.localised_start().month, 1)
        self.assertEqual(r.content, 'Short date test')

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_next_mon(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('Short date test 18:30 next mon')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 18:30 on Monday 13 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.localised_start().day, 13)
        self.assertEqual(r.localised_start().month, 1)
        self.assertEqual(r.content, 'Short date test')

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_next_tue(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('Short date test 18:30 next tue')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 18:30 on Tuesday 14 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.localised_start().day, 14)
        self.assertEqual(r.localised_start().month, 1)
        self.assertEqual(r.content, 'Short date test')

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_next_tues(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('Short date test 18:30 next tues')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 18:30 on Tuesday 14 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.localised_start().day, 14)
        self.assertEqual(r.localised_start().month, 1)
        self.assertEqual(r.content, 'Short date test')

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_next_wed(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('Short date test 18:30 next wed')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 18:30 on Wednesday 15 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.localised_start().day, 15)
        self.assertEqual(r.localised_start().month, 1)
        self.assertEqual(r.content, 'Short date test')

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_next_weds(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('Short date test 18:30 next weds')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 18:30 on Wednesday 15 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.localised_start().day, 15)
        self.assertEqual(r.localised_start().month, 1)
        self.assertEqual(r.content, 'Short date test')

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_next_thur(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('Short date test 18:30 next thur')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 18:30 on Thursday 16 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.localised_start().day, 16)
        self.assertEqual(r.localised_start().month, 1)
        self.assertEqual(r.content, 'Short date test')

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_next_thurs(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('Short date test 18:30 next thur')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 18:30 on Thursday 16 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.localised_start().day, 16)
        self.assertEqual(r.localised_start().month, 1)
        self.assertEqual(r.content, 'Short date test')

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_next_fri(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('Short date test 18:30 next fri')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 18:30 on Friday 17 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.localised_start().day, 17)
        self.assertEqual(r.localised_start().month, 1)
        self.assertEqual(r.content, 'Short date test')

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_next_sat(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('Short date test 18:30 next sat')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 18:30 on Saturday 18 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.localised_start().day, 18)
        self.assertEqual(r.localised_start().month, 1)
        self.assertEqual(r.content, 'Short date test')

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_next_satday(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('Short date test 18:30 next satday')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 18:30 on Saturday 18 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.localised_start().day, 18)
        self.assertEqual(r.localised_start().month, 1)
        self.assertEqual(r.content, 'Short date test')

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_next_sun(self):
        rcount = Reminder.objects.all().count()
        response = self._make_request('Short date test 18:30 next sun')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount+1, Reminder.objects.all().count())
        self.assertIn('set for 18:30 on Sunday 12 January', response.content)
        r = Reminder.objects.latest('created')
        self.assertEqual(r.localised_start().day, 12)
        self.assertEqual(r.localised_start().month, 1)
        self.assertEqual(r.content, 'Short date test')


WEEKDAYS = ['thur', 'thurs', 'fri', 'sat', 'sun', 'satday']

class ReminderUserNotOwnerPrivacyTest(BaseTest):
    """
    Test viewing and preforming actions on reminders not owned by user
    """

    @freeze_time(FROZEN_TIME)
    def setUp(self):
        super(ReminderUserNotOwnerPrivacyTest, self).setUp()
        self.now = datetime.now()
        self.user1 = self.create_user('user1', 'user1@test.com')
        self.user2 = self.create_user('user2', 'user2@test.com')
        self.client.login(username=self.user1.username, password='password')
        self.content = 'Privacy Test'

    # Test overdue
    @freeze_time(FROZEN_TIME)
    def test_reminders_overdue(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        r.overdue()
        response = self.client.get(reverse('overdue'))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.content, response.content)

    # Test upcoming
    @freeze_time(FROZEN_TIME)
    def test_reminders_upcoming(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        response = self.client.get(reverse('upcoming'))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.content, response.content)

    # Test paused
    @freeze_time(FROZEN_TIME)
    def test_reminders_paused(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        r.pause()
        response = self.client.get(reverse('paused'))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.content, response.content)

    # Test completed
    @freeze_time(FROZEN_TIME)
    def test_reminders_completed(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        r.complete()
        response = self.client.get(reverse('completed'))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.content, response.content)

    # Test reminder
    @freeze_time(FROZEN_TIME)
    def test_reminder_overdue(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        r.overdue()
        response = self.client.get(reverse('reminder', args=(r.id,)))
        self.assertEqual(response.status_code, 404)

    @freeze_time(FROZEN_TIME)
    def test_reminder_upcoming(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        response = self.client.get(reverse('reminder', args=(r.id,)))
        self.assertEqual(response.status_code, 404)

    @freeze_time(FROZEN_TIME)
    def test_reminder_paused(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        r.pause()
        response = self.client.get(reverse('reminder', args=(r.id,)))
        self.assertEqual(response.status_code, 404)

    @freeze_time(FROZEN_TIME)
    def test_reminder_completed(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        r.complete()
        response = self.client.get(reverse('reminder', args=(r.id,)))
        self.assertEqual(response.status_code, 404)

    @freeze_time(FROZEN_TIME)
    def test_reminder_delete(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        r.soft_delete()
        response = self.client.get(reverse('reminder', args=(r.id,)))
        self.assertEqual(response.status_code, 404)

    # Test snooze
    @freeze_time(FROZEN_TIME)
    def test_snooze(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        form = {
            'reminder_id': r.id,
            'snooze_until': 'tomorrow',
        }

        response = self.client.post(
            reverse('snooze',
            args=(r.id,)), form, follow=True
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            r.full_start_datetime,
            Reminder.objects.get(pk=r.id).full_start_datetime
        )

    # Test confirm complete
    @freeze_time(FROZEN_TIME)
    def test_confirm_complete(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        r.soft_delete()
        response = self.client.get(reverse('confirm_complete', args=(r.id,)))
        self.assertEqual(response.status_code, 404)

    # Test complete
    @freeze_time(FROZEN_TIME)
    def test_complete(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        response = self.client.post(
            reverse('complete', args=(r.id,)), {}, follow=True
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            r.full_start_datetime,
            Reminder.objects.get(pk=r.id).full_start_datetime
        )

    # Test edit
    @freeze_time(FROZEN_TIME)
    def test_edit(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        form = {
            'remind_at': '10am',
            'remind_on': 'tomorrow',
            'content': 'edited content',
        }
        response = self.client.post(
            reverse('edit', args=(r.id,)), form, follow=True
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            self.content,
            Reminder.objects.get(pk=r.id).content
        )

    # Test delete
    @freeze_time(FROZEN_TIME)
    def test_delete(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        response = self.client.get(
            reverse('delete', args=(r.id,)), follow=True
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(Reminder.objects.get(pk=r.id).deleted)

    # Test pause
    @freeze_time(FROZEN_TIME)
    def test_pause(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        response = self.client.get(reverse('pause', args=(r.id,)), follow=True)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(r.status, Reminder.objects.get(pk=r.id).status)

    # Test activate
    @freeze_time(FROZEN_TIME)
    def test_activate(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        response = self.client.get(
            reverse('unpause', args=(r.id,)), follow=True
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(r.status, Reminder.objects.get(pk=r.id).status)

    # Test complete multiple
    @freeze_time(FROZEN_TIME)
    def test_complete_multiple(self):
        st = self.now - timedelta(hours=1)
        with freeze_time('2014-01-05 07:43:23'):
            r1 = self.create_reminder(
                st.date(), st.time(),
                user=self.user2, content=self.content
            )
            with freeze_time('2014-01-05 07:43:24'):
                r2 = self.create_reminder(
                    st.date(), st.time(),
                    user=self.user2, content=self.content
                )
                form = {
                    'reminder_ids': ','.join([str(r1.id), str(r2.id)])
                }
                response = self.client.post(
                    reverse('complete_multiple'), form, follow=True
                )
                self.assertEqual(response.status_code, 404)
                self.assertEqual(
                    r1.status,
                    Reminder.objects.get(pk=r1.id).status
                )
                self.assertEqual(
                    r2.status,
                    Reminder.objects.get(pk=r2.id).status
                )

    # Test delete multiple
    @freeze_time(FROZEN_TIME)
    def test_delete_multiple(self):
        st = self.now - timedelta(hours=1)
        with freeze_time('2014-01-05 07:43:23'):
            r1 = self.create_reminder(
                st.date(), st.time(),
                user=self.user2, content=self.content
            )
            with freeze_time('2014-01-05 07:43:24'):
                r2 = self.create_reminder(
                    st.date(), st.time(),
                    user=self.user2, content=self.content
                )
                form = {
                    'reminder_ids': ','.join([str(r1.id), str(r2.id)])
                }
                response = self.client.post(
                    reverse('delete_multiple'), form, follow=True
                )
                self.assertEqual(response.status_code, 404)
                self.assertEqual(
                    r1.status,
                    Reminder.objects.get(pk=r1.id).status
                )
                self.assertEqual(
                    r2.status,
                    Reminder.objects.get(pk=r2.id).status
                )

    # Test pause multiple
    @freeze_time(FROZEN_TIME)
    def test_pause_multiple(self):
        st = self.now - timedelta(hours=1)
        with freeze_time('2014-01-05 07:43:23'):
            r1 = self.create_reminder(
                st.date(), st.time(),
                user=self.user2, content=self.content
            )
            with freeze_time('2014-01-05 07:43:24'):
                r2 = self.create_reminder(
                    st.date(), st.time(),
                    user=self.user2, content=self.content
                )
                form = {
                    'reminder_ids': ','.join([str(r1.id), str(r2.id)])
                }
                response = self.client.post(
                    reverse('pause_multiple'), form, follow=True
                )
                self.assertEqual(response.status_code, 404)
                self.assertEqual(
                    r1.status,
                    Reminder.objects.get(pk=r1.id).status
                )
                self.assertEqual(
                    r2.status,
                    Reminder.objects.get(pk=r2.id).status
                )

    # Test activate multiple
    @freeze_time(FROZEN_TIME)
    def test_activate_multiple(self):
        st = self.now - timedelta(hours=1)
        with freeze_time('2014-01-05 07:43:23'):
            r1 = self.create_reminder(
                st.date(), st.time(),
                user=self.user2, content=self.content
            )
            with freeze_time('2014-01-05 07:43:24'):
                r2 = self.create_reminder(
                    st.date(), st.time(),
                    user=self.user2, content=self.content
                )
                form = {
                    'reminder_ids': ','.join([str(r1.id), str(r2.id)])
                }
                response = self.client.post(
                    reverse('unpause_multiple'), form, follow=True
                )
                self.assertEqual(response.status_code, 404)
                self.assertEqual(
                    r1.status,
                    Reminder.objects.get(pk=r1.id).status
                )
                self.assertEqual(
                    r2.status,
                    Reminder.objects.get(pk=r2.id).status
                )


class ReminderLoggedOutUserPrivacyTest(BaseTest):
    """
    Test viewing and preforming actions on reminders not owned by user
    """

    @freeze_time(FROZEN_TIME)
    def setUp(self):
        super(ReminderLoggedOutUserPrivacyTest, self).setUp()
        self.now = datetime.now()
        self.user1 = self.create_user('user1', 'user1@test.com')
        self.user2 = self.create_user('user2', 'user2@test.com')
        self.content = 'Privacy Test'
        self.user_logout()

    # Test overdue
    @freeze_time(FROZEN_TIME)
    def test_reminders_overdue(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        r.overdue()
        response = self.client.get(reverse('overdue'), follow=True)
        redir = '%s?next=%s' % (reverse('account_login'), reverse('overdue'))
        self.assertRedirects(response, redir)
        self.assertNotIn(self.content, response.content)

    # Test upcoming
    @freeze_time(FROZEN_TIME)
    def test_reminders_upcoming(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        response = self.client.get(reverse('upcoming'))
        redir = '%s?next=%s' % (reverse('account_login'), reverse('upcoming'))
        self.assertRedirects(response, redir)
        self.assertNotIn(self.content, response.content)

    # Test paused
    @freeze_time(FROZEN_TIME)
    def test_reminders_paused(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        r.pause()
        response = self.client.get(reverse('paused'))
        redir = '%s?next=%s' % (reverse('account_login'), reverse('paused'))
        self.assertRedirects(response, redir)
        self.assertNotIn(self.content, response.content)

    # Test completed
    @freeze_time(FROZEN_TIME)
    def test_reminders_completed(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        r.complete()
        response = self.client.get(reverse('completed'))
        redir = '%s?next=%s' % (reverse('account_login'), reverse('completed'))
        self.assertRedirects(response, redir)
        self.assertNotIn(self.content, response.content)

    # Test reminder
    @freeze_time(FROZEN_TIME)
    def test_reminder_overdue(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        r.overdue()
        url = reverse('reminder', args=(r.id,))
        response = self.client.get(url)
        redir = '%s?next=%s' % (reverse('account_login'), url)
        self.assertRedirects(response, redir)

    @freeze_time(FROZEN_TIME)
    def test_reminder_upcoming(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        url = reverse('reminder', args=(r.id,))
        response = self.client.get(url)
        redir = '%s?next=%s' % (reverse('account_login'), url)
        self.assertRedirects(response, redir)

    @freeze_time(FROZEN_TIME)
    def test_reminder_paused(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        r.pause()
        url = reverse('reminder', args=(r.id,))
        response = self.client.get(url)
        redir = '%s?next=%s' % (reverse('account_login'), url)
        self.assertRedirects(response, redir)

    @freeze_time(FROZEN_TIME)
    def test_reminder_completed(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        r.complete()
        url = reverse('reminder', args=(r.id,))
        response = self.client.get(url)
        redir = '%s?next=%s' % (reverse('account_login'), url)
        self.assertRedirects(response, redir)

    @freeze_time(FROZEN_TIME)
    def test_reminder_delete(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        r.soft_delete()
        url = reverse('reminder', args=(r.id,))
        response = self.client.get(url)
        redir = '%s?next=%s' % (reverse('account_login'), url)
        self.assertRedirects(response, redir)

    # Test snooze
    @freeze_time(FROZEN_TIME)
    def test_snooze(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        form = {
            'reminder_id': r.id,
            'snooze_until': 'tomorrow',
        }

        url = reverse('snooze', args=(r.id,))
        response = self.client.post(url, form, follow=True)
        redir = '%s?next=%s' % (reverse('account_login'), url)
        self.assertRedirects(response, redir)
        self.assertEqual(
            r.full_start_datetime,
            Reminder.objects.get(pk=r.id).full_start_datetime
        )

    # Test confirm complete
    @freeze_time(FROZEN_TIME)
    def test_confirm_complete(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        r.soft_delete()
        url = reverse('confirm_complete', args=(r.id,))
        response = self.client.get(url)
        redir = '%s?next=%s' % (reverse('account_login'), url)
        self.assertRedirects(response, redir)

    # Test complete
    @freeze_time(FROZEN_TIME)
    def test_complete(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        url = reverse('complete', args=(r.id,))
        response = self.client.post(url, {}, follow=True)
        redir = '%s?next=%s' % (reverse('account_login'), url)
        self.assertRedirects(response, redir)
        self.assertEqual(
            r.full_start_datetime,
            Reminder.objects.get(pk=r.id).full_start_datetime
        )

    # Test edit
    @freeze_time(FROZEN_TIME)
    def test_edit(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        form = {
            'remind_at': '10am',
            'remind_on': 'tomorrow',
            'content': 'edited content',
        }
        url = reverse('edit', args=(r.id,))
        response = self.client.post(url, form, follow=True)
        redir = '%s?next=%s' % (reverse('account_login'), url)
        self.assertRedirects(response, redir)
        self.assertEqual(self.content,
                         Reminder.objects.get(pk=r.id).content)

    # Test delete
    @freeze_time(FROZEN_TIME)
    def test_delete(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        url = reverse('delete', args=(r.id,))
        response = self.client.get(url, follow=True)
        redir = '%s?next=%s' % (reverse('account_login'), url)
        self.assertRedirects(response, redir)
        self.assertFalse(Reminder.objects.get(pk=r.id).deleted)

    # Test pause
    @freeze_time(FROZEN_TIME)
    def test_pause(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        url = reverse('pause', args=(r.id,))
        response = self.client.get(url, follow=True)
        redir = '%s?next=%s' % (reverse('account_login'), url)
        self.assertRedirects(response, redir)
        self.assertEqual(r.status, Reminder.objects.get(pk=r.id).status)

    # Test activate
    @freeze_time(FROZEN_TIME)
    def test_activate(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        url = reverse('unpause', args=(r.id,))
        response = self.client.get(url, follow=True)
        redir = '%s?next=%s' % (reverse('account_login'), url)
        self.assertRedirects(response, redir)
        self.assertEqual(r.status, Reminder.objects.get(pk=r.id).status)

    # Test complete multiple
    @freeze_time(FROZEN_TIME)
    def test_complete_multiple(self):
        st = self.now - timedelta(hours=1)
        r1 = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        with freeze_time('2014-01-05 07:43:23'):
            r2 = self.create_reminder(
                st.date(), st.time(),
                user=self.user2, content=self.content
            )
            form = {
                'reminder_ids': ','.join([str(r1.id), str(r2.id)])
            }
            response = self.client.post(
                reverse('complete_multiple'), form, follow=True
            )
            redir = '%s?next=%s' % (
                reverse('account_login'), reverse('complete_multiple')
            )
            self.assertRedirects(response, redir)
            self.assertEqual(
                r1.status,
                Reminder.objects.get(pk=r1.id).status
            )
            self.assertEqual(
                r2.status,
                Reminder.objects.get(pk=r2.id).status
            )

    # Test delete multiple
    @freeze_time(FROZEN_TIME)
    def test_delete_multiple(self):
        st = self.now - timedelta(hours=1)
        r1 = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        with freeze_time('2014-01-05 07:43:23'):
            r2 = self.create_reminder(
                st.date(), st.time(),
                user=self.user2, content=self.content
            )
            form = {
                'reminder_ids': ','.join([str(r1.id), str(r2.id)])
            }
            response = self.client.post(
                reverse('delete_multiple'), form, follow=True
            )
            redir = '%s?next=%s' % (
                reverse('account_login'), reverse('delete_multiple')
            )
            self.assertRedirects(response, redir)
            self.assertEqual(
                r1.status,
                Reminder.objects.get(pk=r1.id).status
            )
            self.assertEqual(
                r2.status,
                Reminder.objects.get(pk=r2.id).status
            )

    # Test pause multiple
    @freeze_time(FROZEN_TIME)
    def test_pause_multiple(self):
        st = self.now - timedelta(hours=1)
        r1 = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        with freeze_time('2014-01-05 07:43:23'):
            r2 = self.create_reminder(
                st.date(), st.time(),
                user=self.user2, content=self.content
            )
            form = {
                'reminder_ids': ','.join([str(r1.id), str(r2.id)])
            }
            response = self.client.post(
                reverse('pause_multiple'), form, follow=True
            )
            redir = '%s?next=%s' % (
                reverse('account_login'), reverse('pause_multiple')
            )
            self.assertRedirects(response, redir)
            self.assertEqual(
                r1.status,
                Reminder.objects.get(pk=r1.id).status
            )
            self.assertEqual(
                r2.status,
                Reminder.objects.get(pk=r2.id).status
            )

    # Test activate multiple
    @freeze_time(FROZEN_TIME)
    def test_activate_multiple(self):
        st = self.now - timedelta(hours=1)
        r1 = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        with freeze_time('2014-01-05 07:43:23'):
            r2 = self.create_reminder(
                st.date(), st.time(),
                user=self.user2, content=self.content
            )
            form = {
                'reminder_ids': ','.join([str(r1.id), str(r2.id)])
            }
            response = self.client.post(
                reverse('unpause_multiple'), form, follow=True
            )
            redir = '%s?next=%s' % (
                reverse('account_login'), reverse('unpause_multiple')
            )
            self.assertRedirects(response, redir)
            self.assertEqual(
                r1.status,
                Reminder.objects.get(pk=r1.id).status
            )
            self.assertEqual(
                r2.status,
                Reminder.objects.get(pk=r2.id).status
            )


class ReminderMultiPauseTest(BaseTest):
    """
    Test unpausing 1 or more reminders
    """

    @freeze_time(FROZEN_TIME)
    def test_invalid_id(self):
        rcount = Reminder.objects.filter(deleted=False).count()
        form = {'reminder_ids': '9999,8888'}
        response = self.client.post(
            reverse('pause_multiple'), form, follow=True
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(rcount, Reminder.objects.filter(deleted=False).count())

    @freeze_time(FROZEN_TIME)
    def test_non_owned_reminders(self):
        user = self.create_user('test2', 'test2@test.com')
        st = datetime.now() + timedelta(hours=1)
        r1 = self.create_reminder(st.date(), st.time(), user=user)
        with freeze_time('2014-01-05 07:43:23'):
            r2 = self.create_reminder(st.date(), st.time(), user=user)
            r1.pause()
            r2.pause()
            form = {'reminder_ids': ','.join([str(r1.id), str(r2.id)])}
            response = self.client.post(
                reverse('pause_multiple'), form, follow=True
            )
            self.assertEqual(response.status_code, 404)

    @freeze_time(FROZEN_TIME)
    def test_completed(self):
        st = datetime.now() + timedelta(hours=1)
        r1 = self.create_reminder(st.date(), st.time())
        r1.complete()
        with freeze_time('2014-01-05 07:43:23'):
            r2 = self.create_reminder(st.date(), st.time())
            r2.complete()
            rcount = Reminder.objects.filter(deleted=False).count()
            form = {'reminder_ids': ','.join([str(r1.id), str(r2.id)])}
            response = self.client.post(
                reverse('pause_multiple'), form, follow=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn('2 reminders paused successfully', response.content)
            self.assertEqual(
                rcount,
                Reminder.objects.filter(deleted=False, status=1).count()
            )

    @freeze_time(FROZEN_TIME)
    def test_upcoming(self):
        st = datetime.now() + timedelta(hours=1)
        r1 = self.create_reminder(st.date(), st.time())
        with freeze_time('2014-01-05 07:43:23'):
            r2 = self.create_reminder(st.date(), st.time())
            rcount = Reminder.objects.filter(deleted=False).count()
            form = {'reminder_ids': ','.join([str(r1.id), str(r2.id)])}
            response = self.client.post(
                reverse('pause_multiple'), form, follow=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn('2 reminders paused successfully', response.content)
            self.assertEqual(
                rcount,
                Reminder.objects.filter(deleted=False, status=1).count()
            )

    @freeze_time(FROZEN_TIME)
    def test_overdue(self):
        st = datetime.now() - timedelta(hours=1)
        r1 = self.create_reminder(st.date(), st.time())
        r1.overdue()
        with freeze_time('2014-01-05 07:43:23'):
            r2 = self.create_reminder(st.date(), st.time())
            r2.overdue()
            rcount = Reminder.objects.filter(deleted=False).count()
            form = {'reminder_ids': ','.join([str(r1.id), str(r2.id)])}
            response = self.client.post(
                reverse('pause_multiple'), form, follow=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn('2 reminders paused successfully', response.content)
            self.assertEqual(
                rcount,
                Reminder.objects.filter(deleted=False, status=1).count()
            )


class ReminderMultiUnpauseTest(BaseTest):
    """
    Test unpausing 1 or more reminders
    """

    @freeze_time(FROZEN_TIME)
    def test_invalid_id(self):
        rcount = Reminder.objects.filter(deleted=False).count()
        form = {'reminder_ids': '9999,8888'}
        response = self.client.post(
            reverse('unpause_multiple'), form, follow=True
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            rcount, Reminder.objects.filter(deleted=False).count()
        )

    @freeze_time(FROZEN_TIME)
    def test_non_owned_reminders(self):
        user = self.create_user('test2', 'test2@test.com')
        st = datetime.now() + timedelta(hours=1)
        r1 = self.create_reminder(st.date(), st.time(), user=user)
        with freeze_time('2014-01-05 07:43:23'):
            r2 = self.create_reminder(st.date(), st.time(), user=user)
            r1.pause()
            r2.pause()
            form = {'reminder_ids': ','.join([str(r1.id), str(r2.id)])}
            response = self.client.post(
                reverse('unpause_multiple'), form, follow=True
            )
            self.assertEqual(response.status_code, 404)

    @freeze_time(FROZEN_TIME)
    def test_completed(self):
        st = datetime.now() + timedelta(hours=1)
        r1 = self.create_reminder(st.date(), st.time())
        r1.complete()
        with freeze_time('2014-01-05 07:43:23'):
            r2 = self.create_reminder(st.date(), st.time())
            r2.complete()
            rcount = Reminder.objects.filter(deleted=False).count()
            form = {'reminder_ids': ','.join([str(r1.id), str(r2.id)])}
            response = self.client.post(
                reverse('unpause_multiple'), form, follow=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn(
                '2 reminders activated successfully', response.content
            )
            self.assertEqual(
                rcount, Reminder.objects.filter(deleted=False).count()
            )

    @freeze_time(FROZEN_TIME)
    def test_upcoming(self):
        st = datetime.now() + timedelta(hours=1)
        r1 = self.create_reminder(st.date(), st.time())
        with freeze_time('2014-01-05 07:43:23'):
            r2 = self.create_reminder(st.date(), st.time())
            rcount = Reminder.objects.filter(deleted=False).count()
            form = {'reminder_ids': ','.join([str(r1.id), str(r2.id)])}
            response = self.client.post(
                reverse('unpause_multiple'), form, follow=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn('2 reminders activated successfully', response.content)
            self.assertEqual(rcount, Reminder.objects.filter(deleted=False).count())

    @freeze_time(FROZEN_TIME)
    def test_overdue(self):
        st = datetime.now() - timedelta(hours=1)
        r1 = self.create_reminder(st.date(), st.time())
        r1.overdue()
        with freeze_time('2014-01-05 07:43:23'):
            r2 = self.create_reminder(st.date(), st.time())
            r2.overdue()
            rcount = Reminder.objects.filter(deleted=False).count()
            form = {'reminder_ids': ','.join([str(r1.id), str(r2.id)])}
            response = self.client.post(
                reverse('unpause_multiple'), form, follow=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn('2 reminders activated successfully', response.content)
            self.assertEqual(rcount, Reminder.objects.filter(deleted=False).count())


class ReminderMultiCompleteTest(BaseTest):
    """
    Test completing 1 or more reminders
    """

    @freeze_time(FROZEN_TIME)
    def test_invalid_id(self):
        rcount = Reminder.objects.filter(deleted=False).count()
        form = {'reminder_ids': '9999,8888'}
        response = self.client.post(
            reverse('complete_multiple'), form, follow=True
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(rcount, Reminder.objects.filter(deleted=False).count())

    @freeze_time(FROZEN_TIME)
    def test_non_owned_reminders(self):
        user = self.create_user('test2', 'test2@test.com')
        self.user_login()
        st = self.now + timedelta(hours=1)
        with freeze_time('2014-01-05 07:43:23'):
            r1 = self.create_reminder(st.date(), st.time(), user=user)
            r1.pause()
            with freeze_time('2014-01-05 07:43:24'):
                r2 = self.create_reminder(st.date(), st.time(), user=user)
                r2.pause()
                form = {'reminder_ids': ','.join([str(r1.id), str(r2.id)])}
                response = self.client.post(
                    reverse('complete_multiple'), form, follow=True
                )
                self.assertEqual(response.status_code, 404)

    @freeze_time(FROZEN_TIME)
    def test_completed(self):
        st = datetime.now() + timedelta(hours=1)
        with freeze_time('2014-01-05 07:43:23'):
            r1 = self.create_reminder(st.date(), st.time())
            r1.complete()
            with freeze_time('2014-01-05 07:43:24'):
                r2 = self.create_reminder(st.date(), st.time())
                r2.complete()
                rcount = Reminder.objects.filter(deleted=False).count()
                form = {'reminder_ids': ','.join([str(r1.id), str(r2.id)])}
                response = self.client.post(
                    reverse('complete_multiple'), form, follow=True
                )
                self.assertEqual(response.status_code, 200)
                self.assertIn(
                    '2 reminders completed successfully', response.content
                )
                self.assertEqual(
                    rcount,
                    Reminder.objects.filter(deleted=False, status=5).count()
                )

    @freeze_time(FROZEN_TIME)
    def test_upcoming(self):
        st = datetime.now() + timedelta(hours=1)
        with freeze_time('2014-01-05 07:43:23'):
            r1 = self.create_reminder(st.date(), st.time())
            with freeze_time('2014-01-05 07:43:24'):
                r2 = self.create_reminder(st.date(), st.time())
                rcount = Reminder.objects.filter(deleted=False).count()
                form = {'reminder_ids': ','.join([str(r1.id), str(r2.id)])}
                response = self.client.post(
                    reverse('complete_multiple'), form, follow=True
                )
                self.assertEqual(response.status_code, 200)
                self.assertIn(
                    '2 reminders completed successfully', response.content
                )
                self.assertEqual(
                    rcount,
                    Reminder.objects.filter(deleted=False, status=5).count()
                )

    @freeze_time(FROZEN_TIME)
    def test_overdue(self):
        st = datetime.now() - timedelta(hours=1)
        with freeze_time('2014-01-05 07:43:23'):
            r1 = self.create_reminder(st.date(), st.time())
            r1.overdue()
            with freeze_time('2014-01-05 07:43:24'):
                r2 = self.create_reminder(st.date(), st.time())
                r2.overdue()
                rcount = Reminder.objects.filter(deleted=False).count()
                form = {'reminder_ids': ','.join([str(r1.id), str(r2.id)])}
                response = self.client.post(
                    reverse('complete_multiple'), form, follow=True
                )
                self.assertEqual(response.status_code, 200)
                self.assertIn(
                    '2 reminders completed successfully', response.content
                )
                self.assertEqual(
                    rcount,
                    Reminder.objects.filter(deleted=False, status=5).count()
                )


class ReminderEditTest(BaseTest):
    """
    Test reminders can be edited successfully
    """

    def setUp(self):
        super(ReminderEditTest, self).setUp()
        self.reminder = Reminder(
            user=self.user, content="test test",
            start_date=self.today + timedelta(days=10),
            start_time=self.now.time()
        )
        self.reminder.save()
        self.edit_url = reverse('edit', args=(self.reminder.id,))
        self.redirect_url = reverse('upcoming')

    def get_form(self):
        return {
            'content': self.reminder.content,
            'remind_on': self.reminder.localised_start().strftime('%d %B %Y'),
            'remind_at': self.reminder.localised_start().strftime('%H:%M'),
            'next': self.redirect_url,
        }

    @freeze_time(FROZEN_TIME)
    def test_edit_deleted(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form()
        response = self.client.post(self.edit_url, form, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_edit_empty_content(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form()
        form['content'] = ''
        response = self.client.post(self.edit_url, form, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('This field is required', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_edit_content(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form()
        form['content'] = 'New content'
        response = self.client.post(self.edit_url, form, follow=True)
        self.assertRedirects(response, self.redirect_url)
        self.assertIn(
            self.reminder.localised_start().strftime('%d %B'),
            response.content
        )
        self.assertIn(
            self.reminder.localised_start().strftime('%H:%M'),
            response.content
        )
        self.assertEqual(rcount, Reminder.objects.all().count())
        updated = Reminder.objects.get(pk=self.reminder.id)
        self.assertNotEqual(self.reminder.content, updated.content)
        self.assertEqual(
            self.reminder.localised_start().date(),
            updated.localised_start().date()
        )

    @freeze_time(FROZEN_TIME)
    def test_edit_empty_start_time(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form()
        form['remind_at'] = ''
        response = self.client.post(self.edit_url, form, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Please enter a reminder time', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_edit_invalid_start_time(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form()
        form['remind_at'] = 'TESTTESTTEST'
        response = self.client.post(self.edit_url, form, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Please enter a valid reminder time', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_edit_valid_start_time(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form()
        form['remind_at'] = '23:59'
        response = self.client.post(self.edit_url, form, follow=True)
        self.assertRedirects(response, self.redirect_url)
        self.assertIn('set for 23:59', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())
        updated = Reminder.objects.get(pk=self.reminder.id)
        self.assertEqual(self.reminder.content, updated.content)
        self.assertEqual(updated.localised_start().hour, 23)
        self.assertEqual(updated.localised_start().minute, 59)
        self.assertEqual(updated.localised_start().day, 15)
        self.assertEqual(updated.localised_start().month, 1)
        self.assertEqual(updated.localised_start().year, 2014)

    @freeze_time(FROZEN_TIME)
    def test_edit_empty_start_date(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form()
        form['remind_on'] = ''
        response = self.client.post(self.edit_url, form, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Please enter a reminder date', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_edit_invalid_start_date(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form()
        form['remind_on'] = 'TESTTESTTEST'
        response = self.client.post(self.edit_url, form, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Please enter a valid reminder date', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_edit_valid_start_date(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form()
        form['remind_on'] = self.tomorrow.strftime('%d/%m/%Y')
        response = self.client.post(self.edit_url, form, follow=True)
        self.assertRedirects(response, self.redirect_url)
        updated = Reminder.objects.get(pk=self.reminder.id)
        self.assertIn('set for 07:43 tomorrow', response.content)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(self.reminder.content, updated.content)
        self.assertEqual(updated.localised_start().hour, 7)
        self.assertEqual(updated.localised_start().minute, 43)
        self.assertEqual(updated.localised_start().day, self.tomorrow.day)
        self.assertEqual(
            updated.localised_start().weekday(),
            self.tomorrow.weekday()
        )
        self.assertEqual(
            updated.localised_start().date(),
            self.tomorrow
        )
