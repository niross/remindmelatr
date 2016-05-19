from datetime import datetime, timedelta
import json
import urllib

from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from django.core import mail

from freezegun import freeze_time
from rest_framework.authtoken.models import Token

from accounts.models import LocalUser
from reminders.models import Reminder
from timezones.models import Timezone


FROZEN_TIME = '2014-01-05 07:43:22'


class BaseTest(TestCase):
    fixtures = ['socialapp.json', 'timezones.json']

    freezer = freeze_time("2014-01-14 12:00:01")
    freezer.start()

    @freeze_time(FROZEN_TIME)
    def setUp(self):
        self.client = Client()
        self.user = self.create_user('test@test.com', 'test@test.com')
        self.user.save()
        self.now = datetime.now()
        self.today = self.now.date()
        self.tomorrow = self.today + timedelta(days=1)
        self.user_login(username='test@test.com')

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

    def create_reminder(self, start_date, start_time,
                        content='Test', status=2, user=None):
        if user is None:
            user = self.user

        r = Reminder(user=user, content=content, status=status,
                     start_date=start_date, start_time=start_time)
        r.save()
        return r

    def post(self, url, params, use_auth_token=True, headers=None, user=None):
        if headers is None:
            headers = {}

        if user is None:
            user = self.user

        if use_auth_token:
            token = Token.objects.get(user=user).key
            headers['Authorization'] = 'Token %s' % token

        response = self.client.post(url, params, **headers)
        content = response.content

        if response._headers['content-type'][1] == 'application/json':
            content = json.loads(response.content)

        return response.status_code, content

    def get(self, url, params=None, use_auth_token=True, headers=None,
            user=None):

        if headers is None:
            headers = {}

        if user is None:
            user = self.user

        if use_auth_token:
            token = Token.objects.get(user=user).key
            headers['Authorization'] = 'Token %s' % token

        response = self.client.get(url, params, **headers)
        content = response.content

        if response._headers['content-type'][1] == 'application/json':
            content = json.loads(response.content)

        return response.status_code, content

    def put(self, url, params, use_auth_token=True, headers=None, user=None):
        if headers is None:
            headers = {}

        if user is None:
            user = self.user

        if use_auth_token:
            token = Token.objects.get(user=user).key
            headers['Authorization'] = 'Token %s' % token

        response = self.client.put(
            url, data=urllib.urlencode(params),
            content_type='application/x-www-form-urlencoded', **headers
        )

        content = response.content
        if response._headers['content-type'][1] == 'application/json':
            content = json.loads(response.content)

        return response.status_code, content


class TokenAuthTest(BaseTest):

    def _get_form(self):
        return {
            'username': self.user.username,
            'password': 'password',
        }

    @freeze_time(FROZEN_TIME)
    def test_invalid_username(self):
        form = self._get_form()
        form['username'] = 'invalid'
        response = self.client.post(reverse('token-auth'), form)
        self.assertEqual(response.status_code, 400)

    @freeze_time(FROZEN_TIME)
    def test_invalid_password(self):
        form = self._get_form()
        form['password'] = 'invalid'
        response = self.client.post(reverse('token-auth'), form)
        self.assertEqual(response.status_code, 400)

    @freeze_time(FROZEN_TIME)
    def test_valid_request(self):
        form = self._get_form()
        response = self.client.post(reverse('token-auth'), form)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(
            Token.objects.get(user=self.user).key, content['token']
        )

    @freeze_time(FROZEN_TIME)
    def test_valid_request_with_email_address(self):
        form = self._get_form()
        form['username'] = self.user.email
        response = self.client.post(reverse('token-auth'), form)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(Token.objects.get(
            user=self.user).key, content['token']
         )

    @freeze_time(FROZEN_TIME)
    def test_request_with_valid_token(self):
        status, content = self.get(reverse('reminder_list'))
        self.assertEqual(status, 200)
        self.assertEqual(len(content), 0)


class BasicReminderTest(BaseTest):

    @freeze_time(FROZEN_TIME)
    def test_single_reminder(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(st.date(), st.time(), content='test detail')
        status, content = self.get(reverse('reminder_detail', args=(r.id,)))
        self.assertEqual(status, 200)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['status'], r.status)
        self.assertEqual(
            content['full_start_datetime'],
            r.full_start_datetime.strftime('2014-01-05T06:43:22Z')
        )

    @freeze_time(FROZEN_TIME)
    def test_single_reminder_not_owned_by_user(self):
        st = self.now - timedelta(hours=1)
        user2 = self.create_user('testuser2@test.com', 'testuser2@test.com')
        r = self.create_reminder(st.date(), st.time(), user=user2)
        status, _ = self.get(reverse('reminder_detail', args=(r.id,)))
        self.assertEqual(status, 404)


class QuickAddReminderTest(BaseTest):
    """
    Test quick added reminders are created as expected
    """

    def setUp(self):
        super(QuickAddReminderTest, self).setUp()
        self.url = reverse('reminder_list')
        self.start_time = self.now.replace(hour=23, minute=0, second=0).time()
        self.content = 'Test Reminder Content'

    def _make_request(self, content):
        form = {'content': content}
        self.client.login()
        return self.post(self.url, form)

    @freeze_time(FROZEN_TIME)
    def test_no_date_or_time(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request(self.content)
        self.assertEqual(status_code, 400)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'][0], 'Please enter a reminder time')

    @freeze_time(FROZEN_TIME)
    def test_no_date(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request(self.content + ' 11:59pm')
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], '23:59:00')
        self.assertEqual(content['start_date'], '2014-01-05')
        target = datetime(2014, 1, 5, 23, 59, 00)
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_no_time(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request(self.content + ' Friday')
        self.assertEqual(status_code, 400)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'][0], 'Please enter a reminder time')

    @freeze_time(FROZEN_TIME)
    def test_easter_sunday_before(self):
        rcount = Reminder.objects.all().count()
        req = '2pm easter sunday ' + self.content
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], '13:00:00')
        self.assertEqual(content['start_date'], '2014-04-20')
        target = datetime(2014, 4, 20, 14, 00, 00)
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_easter_sunday_after(self):
        rcount = Reminder.objects.all().count()
        req = self.content + ' 2pm easter sunday '
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], '13:00:00')
        self.assertEqual(content['start_date'], '2014-04-20')
        target = datetime(2014, 4, 20, 14, 00, 00)
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_good_friday_before(self):
        rcount = Reminder.objects.all().count()
        req = '2pm good friday ' + self.content
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], '13:00:00')
        self.assertEqual(content['start_date'], '2014-04-18')
        target = datetime(2014, 4, 18, 14, 00, 00)
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_good_friday_after(self):
        rcount = Reminder.objects.all().count()
        req = self.content + ' 2pm good friday'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], '13:00:00')
        self.assertEqual(content['start_date'], '2014-04-18')
        target = datetime(2014, 4, 18, 14, 00, 00)
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_today_before(self):
        rcount = Reminder.objects.all().count()
        req = '23:59 today' + self.content
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], '23:59:00')
        self.assertEqual(content['start_date'], '2014-01-05')
        target = self.now.replace(hour=23, minute=59, second=0)
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_today_after(self):
        rcount = Reminder.objects.all().count()
        req = self.content + ' 23:59 today'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], '23:59:00')
        self.assertEqual(content['start_date'], '2014-01-05')
        target = self.now.replace(hour=23, minute=59, second=0)
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_tonight_before(self):
        rcount = Reminder.objects.all().count()
        req = '11:59pm tonight' + self.content
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], '23:59:00')
        self.assertEqual(content['start_date'], '2014-01-05')
        target = self.now.replace(hour=23, minute=59, second=0)
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_tonight_after(self):
        rcount = Reminder.objects.all().count()
        req = self.content + ' 11:59pm tonight'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], '23:59:00')
        self.assertEqual(content['start_date'], '2014-01-05')
        target = self.now.replace(hour=23, minute=59, second=0)
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_tomorrow_before(self):
        rcount = Reminder.objects.all().count()
        req = '1:59pm tomorrow ' + self.content
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], '13:59:00')
        self.assertEqual(content['start_date'], '2014-01-06')
        target = (self.now + timedelta(days=1)).replace(
            hour=13, minute=59, second=0
        )
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_tomorrow_after(self):
        rcount = Reminder.objects.all().count()
        req = self.content + ' 1:59pm tomorrow'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], '13:59:00')
        self.assertEqual(content['start_date'], '2014-01-06')
        target = (self.now + timedelta(days=1)).replace(
            hour=13, minute=59, second=0
        )
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_monday_before(self):
        rcount = Reminder.objects.all().count()
        req = '1:59pm monday ' + self.content
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], '13:59:00')
        self.assertEqual(content['start_date'], '2014-01-06')
        target = (self.now + timedelta(days=1)).replace(
            hour=13, minute=59, second=0
        )
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_monday_after(self):
        rcount = Reminder.objects.all().count()
        req = self.content + ' 1:59pm monday'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], '13:59:00')
        self.assertEqual(content['start_date'], '2014-01-06')
        target = (self.now + timedelta(days=1)).replace(
            hour=13, minute=59, second=0
        )
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_tuesday_before(self):
        rcount = Reminder.objects.all().count()
        req = '1:59pm tuesday ' + self.content
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        self.assertEqual(content['content'], r.content)
        target = datetime(2014, 1, 7, 13, 59, 0)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_tuesday_after(self):
        rcount = Reminder.objects.all().count()
        req = self.content + ' 1:59pm tuesday'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        self.assertEqual(content['content'], r.content)
        target = datetime(2014, 1, 7, 13, 59, 0)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_wednesday_before(self):
        rcount = Reminder.objects.all().count()
        req = '1:59pm wednesday ' + self.content
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        self.assertEqual(content['content'], r.content)
        target = datetime(2014, 1, 8, 13, 59, 0)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_wednesday_after(self):
        rcount = Reminder.objects.all().count()
        req = self.content + ' 1:59pm wednesday'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        self.assertEqual(content['content'], r.content)
        target = datetime(2014, 1, 8, 13, 59, 0)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_thursday_before(self):
        rcount = Reminder.objects.all().count()
        req = '1:59pm thursday ' + self.content
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        self.assertEqual(content['content'], r.content)
        target = datetime(2014, 1, 9, 13, 59, 0)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_thursday_after(self):
        rcount = Reminder.objects.all().count()
        req = self.content + ' 1:59pm thursday'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        self.assertEqual(content['content'], r.content)
        target = datetime(2014, 1, 9, 13, 59, 0)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_friday_before(self):
        rcount = Reminder.objects.all().count()
        req = '1:59pm friday ' + self.content
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        self.assertEqual(content['content'], r.content)
        target = datetime(2014, 1, 10, 13, 59, 0)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_friday_after(self):
        rcount = Reminder.objects.all().count()
        req = self.content + ' 1:59pm friday'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        self.assertEqual(content['content'], r.content)
        target = datetime(2014, 1, 10, 13, 59, 0)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_saturday_before(self):
        rcount = Reminder.objects.all().count()
        req = '1:59pm saturday ' + self.content
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        self.assertEqual(content['content'], r.content)
        target = datetime(2014, 1, 11, 13, 59, 0)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_saturday_after(self):
        rcount = Reminder.objects.all().count()
        req = self.content + ' 1:59pm saturday'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        self.assertEqual(content['content'], r.content)
        target = datetime(2014, 1, 11, 13, 59, 0)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_sunday_before(self):
        rcount = Reminder.objects.all().count()
        req = '1:59pm sunday ' + self.content
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        self.assertEqual(content['content'], r.content)
        target = datetime(2014, 1, 12, 13, 59, 0)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())


    @freeze_time(FROZEN_TIME)
    def test_sunday_after(self):
        rcount = Reminder.objects.all().count()
        req = self.content + ' 1:59pm sunday'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        self.assertEqual(content['content'], r.content)
        target = datetime(2014, 1, 12, 13, 59, 0)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_this_monday_before(self):
        rcount = Reminder.objects.all().count()
        req = '1:59pm this monday ' + self.content
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 6, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_this_monday_after(self):
        rcount = Reminder.objects.all().count()
        req = self.content + ' 1:59pm this monday'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 6, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_this_tuesday_before(self):
        rcount = Reminder.objects.all().count()
        req = '1:59pm this tuesday ' + self.content
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 7, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_this_tuesday_after(self):
        rcount = Reminder.objects.all().count()
        req = self.content + ' 1:59pm this tuesday'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 7, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_this_wednesday_before(self):
        rcount = Reminder.objects.all().count()
        req = '1:59pm this wednesday ' + self.content
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 8, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_this_wednesday_after(self):
        rcount = Reminder.objects.all().count()
        req = self.content + ' 1:59pm this wednesday'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 8, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_this_thursday_before(self):
        rcount = Reminder.objects.all().count()
        req = '1:59pm this thursday ' + self.content
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 9, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_this_thursday_after(self):
        rcount = Reminder.objects.all().count()
        req = self.content + ' 1:59pm this thursday'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 9, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_this_friday_before(self):
        rcount = Reminder.objects.all().count()
        req = '1:59pm this friday ' + self.content
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 10, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_this_friday_after(self):
        rcount = Reminder.objects.all().count()
        req = self.content + ' 1:59pm this friday'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 10, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_this_saturday_before(self):
        rcount = Reminder.objects.all().count()
        req = '1:59pm this saturday ' + self.content
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 11, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_this_saturday_after(self):
        rcount = Reminder.objects.all().count()
        req = self.content + ' 1:59pm this saturday'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 11, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_this_sunday_before(self):
        rcount = Reminder.objects.all().count()
        req = '1:59pm this sunday ' + self.content
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 12, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_this_sunday_after(self):
        rcount = Reminder.objects.all().count()
        req = self.content + ' 1:59pm this sunday'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 12, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_month_full_before(self):
        rcount = Reminder.objects.all().count()
        req = '1:59pm 25 April' + self.content
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 4, 25, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(
            content['start_time'],
            (target.replace(hour=12)).strftime('%H:%M:%S')
        )
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_month_full_after(self):
        rcount = Reminder.objects.all().count()
        req = self.content + ' 1:59pm 25 December'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 12, 25, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_us_month_full_before(self):
        rcount = Reminder.objects.all().count()
        req = '1:59pm April 25' + self.content
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 4, 25, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(
            content['start_time'],
            (target.replace(hour=12)).strftime('%H:%M:%S')
        )
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_us_month_full_after(self):
        rcount = Reminder.objects.all().count()
        req = self.content + ' 1:59pm December 25'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 12, 25, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_full_date_before(self):
        rcount = Reminder.objects.all().count()
        req = '1:59pm 25/04/2015' + self.content
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2015, 4, 25, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(
            content['start_time'],
            (target.replace(hour=12)).strftime('%H:%M:%S')
        )
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_full_date_after(self):
        rcount = Reminder.objects.all().count()
        req = self.content + ' 1:59pm 25/12/2015'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2015, 12, 25, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_short_month_before(self):
        rcount = Reminder.objects.all().count()
        req = '1:59pm 1 May' + self.content
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 5, 1, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(
            content['start_time'],
            (target.replace(hour=12)).strftime('%H:%M:%S')
        )
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_short_month_after(self):
        rcount = Reminder.objects.all().count()
        req = self.content + ' 1:59pm 22 May'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 5, 22, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(
            content['start_time'],
            (target.replace(hour=12)).strftime('%H:%M:%S')
        )
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_month_year_before(self):
        rcount = Reminder.objects.all().count()
        req = '1:59pm 25/04' + self.content
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 4, 25, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(
            content['start_time'],
            (target.replace(hour=12)).strftime('%H:%M:%S')
        )
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_month_year_after(self):
        rcount = Reminder.objects.all().count()
        req = self.content + ' 1:59pm 25/12'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 12, 25, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_us_month_year_before(self):
        rcount = Reminder.objects.all().count()
        req = '1:59pm 04/25' + self.content
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 4, 25, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(
            content['start_time'],
            (target.replace(hour=12)).strftime('%H:%M:%S')
        )
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_us_month_year_after(self):
        rcount = Reminder.objects.all().count()
        req = self.content + ' 1:59pm 12/20'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 12, 20, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_us_short_month_before(self):
        rcount = Reminder.objects.all().count()
        req = '1:59pm Jan 1' + self.content
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2015, 1, 1, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_us_short_month_after(self):
        rcount = Reminder.objects.all().count()
        req = self.content + ' 1:59pm Jan 22'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 22, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_new_years_day_before(self):
        rcount = Reminder.objects.all().count()
        req = '1:59pm new years day' + self.content
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2015, 1, 1, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_new_years_day_after(self):
        rcount = Reminder.objects.all().count()
        req = self.content + ' 1:59pm new years day'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2015, 1, 1, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_new_years_before(self):
        rcount = Reminder.objects.all().count()
        req = '1:59pm new years' + self.content
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 12, 31, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_new_years_after(self):
        rcount = Reminder.objects.all().count()
        req = self.content + ' 1:59pm new years'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 12, 31, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_christmas_day_before(self):
        rcount = Reminder.objects.all().count()
        req = '1:59pm christmas day' + self.content
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 12, 25, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_christmas_day_after(self):
        rcount = Reminder.objects.all().count()
        req = self.content + ' 1:59pm christmas day'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 12, 25, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_xmas_day_before(self):
        rcount = Reminder.objects.all().count()
        req = '1:59pm xmas day' + self.content
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 12, 25, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_xmas_day_after(self):
        rcount = Reminder.objects.all().count()
        req = self.content + ' 1:59pm xmas day'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 12, 25, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_christmas_eve_before(self):
        rcount = Reminder.objects.all().count()
        req = '1:59pm christmas eve' + self.content
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 12, 24, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_christmas_eve_after(self):
        rcount = Reminder.objects.all().count()
        req = self.content + ' 1:59pm christmas eve'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 12, 24, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_xmas_eve_before(self):
        rcount = Reminder.objects.all().count()
        req = '1:59pm xmas eve' + self.content
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 12, 24, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_xmas_eve_after(self):
        rcount = Reminder.objects.all().count()
        req = self.content + ' 1:59pm xmas eve'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 12, 24, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_boxing_day_before(self):
        rcount = Reminder.objects.all().count()
        req = '1:59pm boxing day' + self.content
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 12, 26, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_boxing_day_after(self):
        rcount = Reminder.objects.all().count()
        req = self.content + ' 1:59pm boxing day'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 12, 26, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_valentines_day_before(self):
        rcount = Reminder.objects.all().count()
        req = '1:59pm valentines day' + self.content
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 2, 14, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_valentines_day_after(self):
        rcount = Reminder.objects.all().count()
        req = self.content + ' 1:59pm valentines day'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 2, 14, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_april_fools_day_before(self):
        rcount = Reminder.objects.all().count()
        req = '1:59pm april fools day' + self.content
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 4, 1, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(
            content['start_time'],
            (target.replace(hour=target.hour-1)).strftime('%H:%M:%S')
        )
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_april_fools_day_after(self):
        rcount = Reminder.objects.all().count()
        req = self.content + ' 1:59pm april fools day'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 4, 1, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(
            content['start_time'],
            (target.replace(hour=target.hour-1)).strftime('%H:%M:%S')
        )
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_single_number_before(self):
        rcount = Reminder.objects.all().count()
        req = '1:59pm 25th' + self.content
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 25, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_single_number_after(self):
        rcount = Reminder.objects.all().count()
        req = self.content + ' 1:59pm 25th'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 25, 13, 59, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_double_digit_before(self):
        rcount = Reminder.objects.all().count()
        req = '22 April 8am ' + self.content
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 4, 22, 8, 0, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(
            content['start_time'],
            (target.replace(hour=target.hour-1)).strftime('%H:%M:%S')
        )
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_double_digit_after(self):
        rcount = Reminder.objects.all().count()
        req = '22 April 8am ' + self.content
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 4, 22, 8, 0, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(
            content['start_time'],
            (target.replace(hour=target.hour-1)).strftime('%H:%M:%S')
        )
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_call_the_bank(self):
        rcount = Reminder.objects.all().count()
        req = '2pm call the bank'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 5, 14, 0, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_kids_to_pool(self):
        rcount = Reminder.objects.all().count()
        req = '15:00 take the kids to the pool'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 5, 15, 0, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_put_the_dinner_on(self):
        rcount = Reminder.objects.all().count()
        req = 'Midday put the dinner on'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 5, 12, 0, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_email_bob_on_monday(self):
        rcount = Reminder.objects.all().count()
        req = 'Email Bob Monday 10am'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 6, 10, 0, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_next_monday(self):
        rcount = Reminder.objects.all().count()
        req = 'Call Cindy 18:30 next Monday'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 13, 18, 30, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_next_tuesday(self):
        rcount = Reminder.objects.all().count()
        req = 'Call Cindy 07:00 next Tuesday'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 14, 7, 0, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_next_wednesday(self):
        rcount = Reminder.objects.all().count()
        req = 'Call Cindy 22:53 next Wednesday'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 15, 22, 53, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_next_thursday(self):
        rcount = Reminder.objects.all().count()
        req = 'Call Cindy 11:13 next Thursday'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 16, 11, 13, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_next_friday(self):
        rcount = Reminder.objects.all().count()
        req = 'Call Cindy 1:17 next Friday'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 17, 1, 17, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_next_saturday(self):
        rcount = Reminder.objects.all().count()
        req = 'Call Cindy 1:17 next Saturday'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 18, 1, 17, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_next_sunday(self):
        rcount = Reminder.objects.all().count()
        req = 'Call Cindy 3:33 next Sunday'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 12, 3, 33, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_2_december(self):
        rcount = Reminder.objects.all().count()
        req = '02/12/14 6am walk the dog'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 12, 2, 6, 0, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_8pm_new_years_eve(self):
        rcount = Reminder.objects.all().count()
        req = 'Start dancing 8pm new years eve'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 12, 31, 20, 0, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_mon(self):
        rcount = Reminder.objects.all().count()
        req = 'Short date test 18:30 mon'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 6, 18, 30, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_tue(self):
        rcount = Reminder.objects.all().count()
        req = 'Short date test 18:30 tue'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 7, 18, 30, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_tues(self):
        rcount = Reminder.objects.all().count()
        req = 'Short date test 18:30 tues'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 7, 18, 30, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_wed(self):
        rcount = Reminder.objects.all().count()
        req = 'Short date test 18:30 wed'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 8, 18, 30, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_weds(self):
        rcount = Reminder.objects.all().count()
        req = 'Short date test 18:30 weds'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 8, 18, 30, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_thur(self):
        rcount = Reminder.objects.all().count()
        req = 'Short date test 18:30 thur'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 9, 18, 30, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_thurs(self):
        rcount = Reminder.objects.all().count()
        req = 'Short date test 18:30 thurs'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 9, 18, 30, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_fri(self):
        rcount = Reminder.objects.all().count()
        req = 'Short date test 18:30 fri'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 10, 18, 30, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_sat(self):
        rcount = Reminder.objects.all().count()
        req = 'Short date test 18:30 sat'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 11, 18, 30, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_satday(self):
        rcount = Reminder.objects.all().count()
        req = 'Short date test 18:30 satday'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 11, 18, 30, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_sun(self):
        rcount = Reminder.objects.all().count()
        req = 'Short date test 18:30 sun'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 12, 18, 30, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_next_mon(self):
        rcount = Reminder.objects.all().count()
        req = 'Short date test 18:30 next mon'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 13, 18, 30, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_next_tue(self):
        rcount = Reminder.objects.all().count()
        req = 'Short date test 18:30 next tue'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 14, 18, 30, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_next_tues(self):
        rcount = Reminder.objects.all().count()
        req = 'Short date test 18:30 next tues'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 14, 18, 30, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_next_wed(self):
        rcount = Reminder.objects.all().count()
        req = 'Short date test 18:30 next wed'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 15, 18, 30, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_next_weds(self):
        rcount = Reminder.objects.all().count()
        req = 'Short date test 18:30 next weds'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 15, 18, 30, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_next_thur(self):
        rcount = Reminder.objects.all().count()
        req = 'Short date test 18:30 next thur'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 16, 18, 30, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_next_thurs(self):
        rcount = Reminder.objects.all().count()
        req = 'Short date test 18:30 next thurs'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 16, 18, 30, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_next_fri(self):
        rcount = Reminder.objects.all().count()
        req = 'Short date test 18:30 next fri'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 17, 18, 30, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_next_sat(self):
        rcount = Reminder.objects.all().count()
        req = 'Short date test 18:30 next sat'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 18, 18, 30, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_next_satday(self):
        rcount = Reminder.objects.all().count()
        req = 'Short date test 18:30 next satday'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 18, 18, 30, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_short_weekday_next_sun(self):
        rcount = Reminder.objects.all().count()
        req = 'Short date test 18:30 next sun'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 201)
        self.assertEqual(rcount + 1, Reminder.objects.all().count())
        r = Reminder.objects.latest('created')
        target = datetime(2014, 1, 12, 18, 30, 0)
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())


class ReminderUserNotOwnerPrivacyTest(BaseTest):
    """
    Test viewing reminders not owned by user
    """

    @freeze_time(FROZEN_TIME)
    def setUp(self):
        super(ReminderUserNotOwnerPrivacyTest, self).setUp()
        self.user1 = self.create_user('user1', 'user1@test.com')
        self.user2 = self.create_user('user2', 'user2@test.com')
        self.content = 'Privacy Test'

    # Test overdue
    @freeze_time(FROZEN_TIME)
    def test_reminder_list_overdue(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        r.overdue()
        status_code, content = self.get(
            reverse('reminder_list', args=('overdue',))
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(len(content), 0)

    @freeze_time(FROZEN_TIME)
    def test_reminder_detail_overdue(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        r.overdue()
        status_code, content = self.get(
            reverse('reminder_detail', args=(r.id,))
        )
        self.assertEqual(status_code, 404)
        self.assertEqual(len(content), 0)

    @freeze_time(FROZEN_TIME)
    def test_reminder_list_upcoming(self):
        st = self.now - timedelta(hours=1)
        self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        status_code, content = self.get(
            reverse('reminder_list', args=('upcoming',))
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(len(content), 0)

    @freeze_time(FROZEN_TIME)
    def test_reminder_detail_upcoming(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        status_code, content = self.get(
            reverse('reminder_detail', args=(r.id,))
        )
        self.assertEqual(status_code, 404)
        self.assertEqual(len(content), 0)

    # Test paused
    @freeze_time(FROZEN_TIME)
    def test_reminder_list_paused(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        r.pause()
        status_code, content = self.get(
            reverse('reminder_list', args=('paused',))
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(len(content), 0)

    @freeze_time(FROZEN_TIME)
    def test_reminder_detail_paused(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        r.pause()
        status_code, content = self.get(
            reverse('reminder_detail', args=(r.id,))
        )
        self.assertEqual(status_code, 404)
        self.assertEqual(len(content), 0)

    @freeze_time(FROZEN_TIME)
    def test_reminder_list_completed(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        r.complete()
        status_code, content = self.get(
            reverse('reminder_list', args=('completed',))
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(len(content), 0)

    @freeze_time(FROZEN_TIME)
    def test_reminder_detail_completed(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(
            st.date(), st.time(),
            user=self.user2, content=self.content
        )
        r.complete()
        status_code, content = self.get(
            reverse('reminder_detail', args=(r.id,))
        )
        self.assertEqual(status_code, 404)
        self.assertEqual(len(content), 0)

    @freeze_time(FROZEN_TIME)
    def test_reminder_list_all(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(st.date(), st.time(),
                                 user=self.user2, content=self.content)
        r.complete()
        status_code, content = self.get(reverse('reminder_list'))
        self.assertEqual(status_code, 200)
        self.assertEqual(len(content), 0)


class ReminderUserLoggedOutTest(BaseTest):
    """
    Test viewing reminders while logged out
    """

    @freeze_time(FROZEN_TIME)
    def setUp(self):
        super(ReminderUserLoggedOutTest, self).setUp()
        self.content = 'Privacy Test'
        self.user_logout()

    # Test overdue
    @freeze_time(FROZEN_TIME)
    def test_reminder_list_overdue(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(st.date(), st.time(), content=self.content)
        r.overdue()
        status_code, content = self.get(
            reverse('reminder_list',
            args=('overdue',)), use_auth_token=False
        )
        self.assertEqual(status_code, 403)
        self.assertIn('credentials were not provided', content['detail'])

    @freeze_time(FROZEN_TIME)
    def test_reminder_detail_overdue(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(st.date(), st.time(), content=self.content)
        r.overdue()
        status_code, content = self.get(
            reverse('reminder_list', args=('overdue',)), use_auth_token=False
        )
        self.assertEqual(status_code, 403)
        self.assertIn('credentials were not provided', content['detail'])

    # Test upcoming
    @freeze_time(FROZEN_TIME)
    def test_reminder_list_upcoming(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(st.date(), st.time(), content=self.content)
        status_code, content = self.get(
            reverse('reminder_list', args=('overdue',)), use_auth_token=False
        )
        self.assertEqual(status_code, 403)
        self.assertIn('credentials were not provided', content['detail'])

    @freeze_time(FROZEN_TIME)
    def test_reminder_detail_upcoming(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(st.date(), st.time(), content=self.content)
        status_code, content = self.get(
            reverse('reminder_list', args=('overdue',)), use_auth_token=False
        )
        self.assertEqual(status_code, 403)
        self.assertIn('credentials were not provided', content['detail'])

    # Test paused
    @freeze_time(FROZEN_TIME)
    def test_reminder_list_paused(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(st.date(), st.time(), content=self.content)
        r.pause()
        status_code, content = self.get(
            reverse('reminder_list', args=('overdue',)), use_auth_token=False
        )
        self.assertEqual(status_code, 403)
        self.assertIn('credentials were not provided', content['detail'])

    @freeze_time(FROZEN_TIME)
    def test_reminder_detail_paused(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(st.date(), st.time(), content=self.content)
        r.pause()
        status_code, content = self.get(
            reverse('reminder_list', args=('overdue',)), use_auth_token=False
        )
        self.assertEqual(status_code, 403)
        self.assertIn('credentials were not provided', content['detail'])

    # Test completed
    @freeze_time(FROZEN_TIME)
    def test_reminder_list_completed(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(st.date(), st.time(), content=self.content)
        r.complete()
        status_code, content = self.get(
            reverse('reminder_list', args=('overdue',)), use_auth_token=False
        )
        self.assertEqual(status_code, 403)
        self.assertIn('credentials were not provided', content['detail'])

    @freeze_time(FROZEN_TIME)
    def test_reminder_detail_completed(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(st.date(), st.time(), content=self.content)
        r.complete()
        status_code, content = self.get(
            reverse('reminder_list', args=('overdue',)), use_auth_token=False
        )
        self.assertEqual(status_code, 403)
        self.assertIn('credentials were not provided', content['detail'])

    @freeze_time(FROZEN_TIME)
    def test_reminder_list_all(self):
        st = self.now - timedelta(hours=1)
        r = self.create_reminder(st.date(), st.time(), content=self.content)
        r.complete()
        status_code, content = self.get(
            reverse('reminder_list', args=('overdue',)), use_auth_token=False
        )
        self.assertEqual(status_code, 403)
        self.assertIn('credentials were not provided', content['detail'])


class ReminderSnoozeTest(BaseTest):
    """
    Test snoozing an already created reminder
    """

    @freeze_time(FROZEN_TIME)
    def setUp(self):
        super(ReminderSnoozeTest, self).setUp()
        self.reminder = Reminder(
            user=self.user, content="test test",
            start_date=self.now.date(),
            start_time=self.now.time()
        )
        self.reminder.save()
        self.url = reverse('reminder_snooze', args=(self.reminder.id,))

    def _make_request(self, snooze_until):
        form = {'snooze_until': snooze_until}
        return self.put(self.url, form)

    @freeze_time(FROZEN_TIME)
    def test_1_minute(self):
        rcount = Reminder.objects.all().count()
        req = '1 minute'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = self.now + timedelta(minutes=1)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_5_minute(self):
        rcount = Reminder.objects.all().count()
        req = '5 minutes'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = self.now + timedelta(minutes=5)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_1_hour(self):
        rcount = Reminder.objects.all().count()
        req = '1 hour'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = self.now + timedelta(hours=1)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_5_hours(self):
        rcount = Reminder.objects.all().count()
        req = '5 hours'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = self.now + timedelta(hours=5)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_1_day(self):
        rcount = Reminder.objects.all().count()
        req = '1 day'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = self.now + timedelta(days=1)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_5_days(self):
        rcount = Reminder.objects.all().count()
        req = '5 days'
        status_code, content = self._make_request(req)
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = self.now + timedelta(days=5)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_1_month(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('1 month')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = datetime(2014, 2, 5, r.start_time.hour,
                          r.start_time.minute, r.start_time.second)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_5_months(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('5 months')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = datetime(2014, 6, 5, r.start_time.hour,
                          r.start_time.minute, r.start_time.second)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(),
                         (target + timedelta(hours=1)).time()) # gmt

    @freeze_time(FROZEN_TIME)
    def test_1_year(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('1 year')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = datetime(2015, 1, 5, r.start_time.hour,
                          r.start_time.minute, r.start_time.second)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_5_years(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('5 years')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = datetime(2019, 1, 5, r.start_time.hour,
                          r.start_time.minute, r.start_time.second)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_am(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('8am')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = self.now.replace(hour=8, minute=0, second=0)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_pm(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('11pm')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = self.now.replace(hour=23, minute=0, second=0)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_full_time(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('11:59pm')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = self.now.replace(hour=23, minute=59, second=0)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_full_time_twenty_four_hour(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('23:59')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = self.now.replace(hour=23, minute=59, second=0)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_tomorrow(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('tomorrow')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = self.now.replace(day=self.tomorrow.day,
                                  month=self.tomorrow.month,
                                  year=self.tomorrow.year)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_tmrw(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('tmrw')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = self.now.replace(day=self.tomorrow.day,
                                  month=self.tomorrow.month,
                                  year=self.tomorrow.year)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_2morrow(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('2morrow')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = self.now.replace(day=self.tomorrow.day,
                                  month=self.tomorrow.month,
                                  year=self.tomorrow.year)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_2mrw(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('2mrw')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = self.now.replace(day=self.tomorrow.day,
                                  month=self.tomorrow.month,
                                  year=self.tomorrow.year)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_next_monday(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('next monday')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = self.now.replace(day=13)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_next_tuesday(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('next tuesday')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = self.now.replace(day=14)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_next_wednesday(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('next wednesday')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = self.now.replace(day=15)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_next_thursday(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('next thursday')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = self.now.replace(day=16)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_next_friday(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('next friday')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = self.now.replace(day=17)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_next_saturday(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('next saturday')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = self.now.replace(day=18)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_next_sunday(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('next sunday')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = self.now.replace(day=12)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_this_monday(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('this monday')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = self.now.replace(day=6)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_this_tuesday(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('this tuesday')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = self.now.replace(day=7)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_this_wednesday(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('this wednesday')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = self.now.replace(day=8)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_this_thursday(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('this thursday')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = self.now.replace(day=9)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_this_friday(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('this friday')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = self.now.replace(day=10)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_this_saturday(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('this saturday')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = self.now.replace(day=11)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_this_sunday(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('this sunday')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = self.now.replace(day=12)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_month_string1(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('25 April')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = datetime(
            2014, 4, 25, r.start_time.hour,
            r.start_time.minute, r.start_time.second
        )
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(
            r.localised_start().time(),
            (target + timedelta(hours=1)).time()
        )

    @freeze_time(FROZEN_TIME)
    def test_month_string2(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('April 25')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = datetime(
            2014, 4, 25,
            r.start_time.hour, r.start_time.minute, r.start_time.second
        )
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(
            r.localised_start().time(),
            (target + timedelta(hours=1)).time()
        )

    @freeze_time(FROZEN_TIME)
    def test_date_numbers_full_date(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('25/04/14')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = datetime(2014, 4, 25, r.start_time.hour,
                          r.start_time.minute, r.start_time.second)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(
            r.localised_start().time(),
            (target + timedelta(hours=1)).time()
        )

    @freeze_time(FROZEN_TIME)
    def test_monday(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('monday')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = self.now.replace(day=6)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_tuesday(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('tuesday')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = self.now.replace(day=7)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_wednesday(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('wednesday')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = self.now.replace(day=8)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_thursday(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('thursday')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = self.now.replace(day=9)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_friday(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('friday')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = self.now.replace(day=10)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_saturday(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('saturday')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = self.now.replace(day=11)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_sunday(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('sunday')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = self.now.replace(day=12)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_us_date_numbers(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('12/25')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = r.full_start_datetime.replace(day=25, month=12)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_uk_date_numbers(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('25/12')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = r.full_start_datetime.replace(day=25, month=12)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_day_as_string_first(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('first january')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = datetime(2015, 1, 1, r.start_time.hour,
                          r.start_time.minute, r.start_time.second)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_day_as_string_second(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('january first')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = datetime(2015, 1, 1, r.start_time.hour,
                          r.start_time.minute, r.start_time.second)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_new_years_day(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('new years day')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = datetime(2015, 1, 1, r.start_time.hour,
                          r.start_time.minute, r.start_time.second)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_new_years(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('new years')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = datetime(2014, 12, 31, r.start_time.hour,
                          r.start_time.minute, r.start_time.second)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_christmas_day(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('christmas day')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = datetime(2014, 12, 25, r.start_time.hour,
                          r.start_time.minute, r.start_time.second)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_xmas_day(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('xmas day')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = datetime(2014, 12, 25, r.start_time.hour,
                          r.start_time.minute, r.start_time.second)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_christmas_eve(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('christmas eve')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = datetime(2014, 12, 24, r.start_time.hour,
                          r.start_time.minute, r.start_time.second)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_xmas_eve(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('xmas eve')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = datetime(2014, 12, 24, r.start_time.hour,
                          r.start_time.minute, r.start_time.second)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_boxing_day(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('boxing day')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = datetime(2014, 12, 26, r.start_time.hour,
                          r.start_time.minute, r.start_time.second)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_valentines_day(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('valentines day')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = datetime(2014, 2, 14, r.start_time.hour,
                          r.start_time.minute, r.start_time.second)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_april_fools(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('april fools day')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = datetime(2014, 4, 1, r.start_time.hour,
                          r.start_time.minute, r.start_time.second)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(),
                         (target + timedelta(hours=1)).time()) # gmt

    @freeze_time(FROZEN_TIME)
    def test_single_number(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('25th')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = r.full_start_datetime.replace(day=25)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_easter_sunday(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('easter sunday')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = datetime(2014, 4, 20, r.start_time.hour,
                          r.start_time.minute, r.start_time.second)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(),
                         (target + timedelta(hours=1)).time()) # gmt

    @freeze_time(FROZEN_TIME)
    def test_good_friday(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('good friday')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = datetime(2014, 4, 18, r.start_time.hour,
                          r.start_time.minute, r.start_time.second)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(),
                         (target + timedelta(hours=1)).time()) # gmt

    # Test bug where snoozing till 06:58 at 06:56 failed
    @freeze_time('2014-01-05 06:56:02')
    def test_two_minute_snooze(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('06:58')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = r.full_start_datetime.replace(minute=58)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())

    @freeze_time(FROZEN_TIME)
    def test_snooze_4pm(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self._make_request('4pm')
        self.assertEqual(status_code, 200)
        r = Reminder.objects.latest('created')
        target = r.full_start_datetime.replace(hour=16)
        self.assertEqual(rcount, Reminder.objects.all().count())
        self.assertEqual(content['content'], r.content)
        self.assertEqual(content['start_time'], target.strftime('%H:%M:%S'))
        self.assertEqual(content['start_date'], target.strftime('%Y-%m-%d'))
        self.assertEqual(r.localised_start().date(), target.date())
        self.assertEqual(r.localised_start().time(), target.time())


class ReminderEditTest(BaseTest):
    """
    Test reminders can be edited successfully
    """

    def setUp(self):
        super(ReminderEditTest, self).setUp()
        self.reminder = Reminder(user=self.user, content="test test",
                                 start_date=self.today + timedelta(days=10),
                                 start_time=self.now.time())
        self.reminder.save()
        self.url = reverse('reminder_detail', args=(self.reminder.id,))

    def get_form(self):
        return {
            'content': self.reminder.content,
            'start_date': self.reminder.localised_start().strftime('%Y-%m-%d'),
            'start_time': self.reminder.localised_start().strftime('%H:%M'),
        }

    def _make_request(self, form):
        return self.put(self.url, form)

    @freeze_time(FROZEN_TIME)
    def test_edit_no_content(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form()
        form['content'] = ''
        status_code, content = self._make_request(form)
        self.assertEqual(status_code, 400)
        self.assertEqual('This field may not be blank.', content['content'][0])

    @freeze_time(FROZEN_TIME)
    def test_edit_content(self):
        rcount = Reminder.objects.all().count()
        form = self.get_form()
        form['content'] = 'updated content'
        status_code, content = self._make_request(form)
        self.assertEqual(status_code, 200)
        self.assertEqual(form['content'], content['content'])
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_edit_deleted(self):
        self.reminder.delete()
        form = self.get_form()
        status_code, content = self._make_request(form)
        self.assertEqual(status_code, 404)


class ReminderStatusTest(BaseTest):
    """
    Test reminder statuses can be updated
    """

    def setUp(self):
        super(ReminderStatusTest, self).setUp()
        self.reminder = Reminder(user=self.user, content="test test",
                                 start_date=self.today + timedelta(days=10),
                                 start_time=self.now.time())
        self.reminder.save()

    @freeze_time(FROZEN_TIME)
    def test_pause_non_existent(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self.put(
            reverse('reminder_pause', args=(999,)), {}
        )
        self.assertEqual(status_code, 404)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_pause_not_owned_by_user(self):
        self.user2 = self.create_user('user2', 'user2@test.com')
        r = self.create_reminder(self.now.date(), self.now.time(),
                                 user=self.user2, content='test')
        rcount = Reminder.objects.all().count()
        status_code, content = self.put(
            reverse('reminder_pause', args=(r.id,)), {}
        )
        self.assertEqual(status_code, 404)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_pause(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self.put(reverse('reminder_pause',
                                        args=(self.reminder.id,)), {})
        self.assertEqual(status_code, 200)
        self.assertEqual(rcount, Reminder.objects.all().count())
        updated = Reminder.objects.get(pk=self.reminder.id)
        self.assertEqual(updated.status, 1)

    @freeze_time(FROZEN_TIME)
    def test_unpause_non_existent(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self.put(
            reverse('reminder_unpause', args=(999,)), {}
        )
        self.assertEqual(status_code, 404)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_unpause_not_owned_by_user(self):
        self.user2 = self.create_user('user2', 'user2@test.com')
        r = self.create_reminder(self.now.date(), self.now.time(),
                                 user=self.user2, content='test')
        rcount = Reminder.objects.all().count()
        status_code, content = self.put(
            reverse('reminder_unpause', args=(r.id,)), {}
        )
        self.assertEqual(status_code, 404)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_unpause(self):
        self.reminder.pause()
        rcount = Reminder.objects.all().count()
        status_code, content = self.put(reverse('reminder_unpause',
                                        args=(self.reminder.id,)), {})
        self.assertEqual(status_code, 200)
        self.assertEqual(rcount, Reminder.objects.all().count())
        updated = Reminder.objects.get(pk=self.reminder.id)
        self.assertEqual(updated.status, 2)

    @freeze_time(FROZEN_TIME)
    def test_complete_non_existent(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self.put(
            reverse('reminder_complete', args=(999,)), {}
        )
        self.assertEqual(status_code, 404)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_complete_not_owned_by_user(self):
        self.user2 = self.create_user('user2', 'user2@test.com')
        r = self.create_reminder(self.now.date(), self.now.time(),
                                 user=self.user2, content='test')
        rcount = Reminder.objects.all().count()
        status_code, content = self.put(
            reverse('reminder_complete', args=(r.id,)), {}
        )
        self.assertEqual(status_code, 404)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_complete(self):
        self.reminder.pause()
        rcount = Reminder.objects.all().count()
        status_code, content = self.put(
            reverse('reminder_complete', args=(self.reminder.id,)), {}
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(rcount, Reminder.objects.all().count())
        updated = Reminder.objects.get(pk=self.reminder.id)
        self.assertEqual(updated.status, 5)

    # test delete
    @freeze_time(FROZEN_TIME)
    def test_delete_non_existent(self):
        rcount = Reminder.objects.all().count()
        status_code, content = self.put(
            reverse('reminder_delete', args=(999,)), {}
        )
        self.assertEqual(status_code, 404)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_delete_not_owned_by_user(self):
        self.user2 = self.create_user('user2', 'user2@test.com')
        r = self.create_reminder(self.now.date(), self.now.time(),
                                 user=self.user2, content='test')
        rcount = Reminder.objects.all().count()
        status_code, content = self.put(
            reverse('reminder_delete', args=(r.id,)), {}
        )
        self.assertEqual(status_code, 404)
        self.assertEqual(rcount, Reminder.objects.all().count())

    @freeze_time(FROZEN_TIME)
    def test_delete(self):
        self.reminder.pause()
        rcount = Reminder.objects.all().count()
        status_code, content = self.put(
            reverse('reminder_delete', args=(self.reminder.id,)), {}
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(rcount-1, Reminder.objects.all().count())
        updated = Reminder.objects.get(pk=self.reminder.id)
        self.assertEqual(updated.status, 7)


class UserDetailTest(BaseTest):
    """
    Test reminder statuses can be updated
    """

    @freeze_time(FROZEN_TIME)
    def test_user_detail(self):
        status_code, content = self.get(reverse('user'))
        self.assertEqual(status_code, 200)
        self.assertEqual(content['email'], self.user.username)
        self.assertEqual(content['id'], self.user.id)
        self.assertEqual(content['email'], self.user.email)


class NewRemindersTest(BaseTest):
    """
    Test fetching new reminders since given date
    """

    @freeze_time(FROZEN_TIME)
    def setUp(self):
        super(NewRemindersTest, self).setUp()
        self.reminder = Reminder(
            user=self.user, content="test test",
            start_date=self.today,
            start_time=(self.now - timedelta(minutes=5)).time()
        )
        self.reminder.save()
        self.reminder.overdue()

    def url(self, date):
        return reverse(
            'new_reminders', args=(date.strftime('%Y-%m-%d %H:%M:%S'),)
        )

    @freeze_time(FROZEN_TIME)
    def test_single_reminder(self):
        dt = self.now - timedelta(minutes=10)
        status_code, content = self.get(self.url(dt))
        self.assertEqual(status_code, 200)
        self.assertEqual(len(content), 1)
        self.assertEqual(self.reminder.id, content[0]['id'])

    @freeze_time(FROZEN_TIME)
    def test_single_before_threshold(self):
        dt = self.now - timedelta(minutes=1)
        status_code, content = self.get(self.url(dt))
        self.assertEqual(status_code, 200)
        self.assertEqual(len(content), 0)

    @freeze_time(FROZEN_TIME)
    def test_single_reminder_with_upcoming(self):
        dt = self.now - timedelta(minutes=10)
        st = self.now - timedelta(minutes=5)
        r1 = self.create_reminder(st.date(), st.time())
        with freeze_time('2014-01-05 07:43:24'):
            r2 = self.create_reminder(st.date(), st.time())
            status_code, content = self.get(self.url(dt))
            self.assertEqual(status_code, 200)
            self.assertEqual(len(content), 1)
            self.assertEqual(self.reminder.id, content[0]['id'])

    @freeze_time(FROZEN_TIME)
    def test_not_owned_by_user(self):
        dt = self.now - timedelta(minutes=10)
        st = self.now - timedelta(minutes=5)
        user2 = self.create_user('user2', 'user2@test.com')
        r2 = self.create_reminder(st.date(), st.time(), user=user2)
        r2.overdue()
        status_code, content = self.get(self.url(dt))
        self.assertEqual(status_code, 200)
        self.assertEqual(len(content), 1)
        self.assertEqual(self.reminder.id, content[0]['id'])

    @freeze_time(FROZEN_TIME)
    def test_reminder_list_overdue(self):
        self.user_logout()
        dt = self.now - timedelta(minutes=10)
        status_code, content = self.get(self.url(dt), use_auth_token=False)
        self.assertEqual(status_code, 403)


class SignUpTest(BaseTest):

    def setUp(self):
        super(SignUpTest, self).setUp()
        self.url = reverse('register')
        self.user_logout()

    def _get_form(self):
        return {
            'email': 'test01@test01.com',
            'password': 'test01',
            'confirm_password': 'test01',
            'timezone_name': 'Europe/London',
        }

    def test_invalid_email(self):
        count = LocalUser.objects.all().count()
        form = self._get_form()
        form['email'] = 'test01'
        status_code, content = self.post(self.url, form, use_auth_token=False)
        self.assertEqual(status_code, 400)
        self.assertIn('Enter a valid email address.', content['email'][0])
        self.assertEqual(count, LocalUser.objects.all().count())

    def test_empty_email(self):
        count = LocalUser.objects.all().count()
        form = self._get_form()
        form['email'] = ''
        status_code, content = self.post(self.url, form, use_auth_token=False)
        self.assertEqual(status_code, 400)
        self.assertIn('This field may not be blank', content['email'][0])
        self.assertEqual(count, LocalUser.objects.all().count())

    def test_email_exists(self):
        count = LocalUser.objects.all().count()
        form = self._get_form()
        form['email'] = self.user.email
        status_code, content = self.post(self.url, form, use_auth_token=False)
        self.assertEqual(status_code, 400)
        self.assertIn(
            'This email address is already in use.', content['email'][0]
        )
        self.assertEqual(count, LocalUser.objects.all().count())

    def test_empty_timezone(self):
        count = LocalUser.objects.all().count()
        form = self._get_form()
        form['timezone_name'] = ''
        status_code, content = self.post(self.url, form, use_auth_token=False)
        self.assertEqual(status_code, 400)
        self.assertIn(
            'This field may not be blank', content['timezone_name'][0]
        )
        self.assertEqual(count, LocalUser.objects.all().count())

    def test_invalid_password(self):
        count = LocalUser.objects.all().count()
        form = self._get_form()
        form['password'] = '1'
        form['confirm_password'] = '1'
        status_code, content = self.post(self.url, form, use_auth_token=False)
        self.assertEqual(status_code, 400)
        self.assertIn(
            'Password must be at least 6 characters', content['password'][0]
        )
        self.assertEqual(count, LocalUser.objects.all().count())

    def test_empty_password(self):
        count = LocalUser.objects.all().count()
        form = self._get_form()
        form['password'] = ''
        status_code, content = self.post(self.url, form, use_auth_token=False)
        self.assertEqual(status_code, 400)
        self.assertIn('This field may not be blank', content['password'][0])
        self.assertEqual(count, LocalUser.objects.all().count())

    def test_empty_confirm_password(self):
        count = LocalUser.objects.all().count()
        form = self._get_form()
        form['confirm_password'] = ''
        status_code, content = self.post(self.url, form, use_auth_token=False)
        self.assertEqual(status_code, 400)
        self.assertIn(
            'This field may not be blank', content['confirm_password'][0]
        )
        self.assertEqual(count, LocalUser.objects.all().count())

    def test_password_mismatch(self):
        count = LocalUser.objects.all().count()
        form = self._get_form()
        form['password'] = 'aaaaaa'
        form['confirm_password'] = 'bbbbbb'
        status_code, content = self.post(self.url, form, use_auth_token=False)
        self.assertEqual(status_code, 400)
        self.assertIn(
            'Please ensure both passwords match', content['password'][0]
        )
        self.assertEqual(count, LocalUser.objects.all().count())

    def test_valid_form(self):
        count = LocalUser.objects.all().count()
        form = self._get_form()
        status_code, content = self.post(self.url, form, use_auth_token=False)
        self.assertEqual(status_code, 201)

        self.assertEqual(count+1, LocalUser.objects.all().count())
        user = LocalUser.objects.latest('created')
        self.assertEqual(form['email'], user.username)
        self.assertEqual(form['email'], user.email)
        tz = Timezone.objects.get(name=form['timezone_name'])
        self.assertEqual(tz, user.timezone)

        # Ensure the user can login
        login_form = {
            'username': 'test01@test01.com',
            'password': form['password']
        }
        response = self.client.post(reverse('custom-token-auth'), login_form)
        self.assertEqual(response.status_code, 200)

        # Ensure an email is sent
        self.assertEquals(len(mail.outbox), 1)
        self.assertIn('Confirm Email Address', mail.outbox[0].subject)


class CustomTokenAuthTest(BaseTest):

    def setUp(self):
        super(CustomTokenAuthTest, self).setUp()
        self.url = reverse('custom-token-auth')
        self.user_logout()

    def _get_form(self):
        return {
            'username': 'test@test.com',
            'timezone_name': 'Europe/London',
            'password': 'password',
            'timezone': 999
        }

    def test_invalid_email(self):
        count = LocalUser.objects.all().count()
        form = self._get_form()
        form['username'] = 'test01'
        status_code, content = self.post(self.url, form, use_auth_token=False)
        self.assertEqual(status_code, 400)
        self.assertIn('Unable to log in with provided credentials.',
                      content['non_field_errors'][0])
        self.assertEqual(count, LocalUser.objects.all().count())

    def test_empty_email(self):
        count = LocalUser.objects.all().count()
        form = self._get_form()
        form['username'] = ''
        status_code, content = self.post(self.url, form, use_auth_token=False)
        self.assertEqual(status_code, 400)
        self.assertIn('This field may not be blank.',
                      content['username'][0])
        self.assertEqual(count, LocalUser.objects.all().count())

    def test_empty_timezone(self):
        count = LocalUser.objects.all().count()
        form = self._get_form()
        form['timezone_name'] = ''
        token, created = Token.objects.get_or_create(user=self.user)
        status_code, content = self.post(self.url, form, use_auth_token=False)
        self.assertEqual(status_code, 200)
        self.assertEqual(form['username'], content['email'])
        self.assertEqual(token.key, content['token'])
        self.assertEqual(count, LocalUser.objects.all().count())

    def test_invalid_password(self):
        count = LocalUser.objects.all().count()
        form = self._get_form()
        form['password'] = '1'
        status_code, content = self.post(self.url, form, use_auth_token=False)
        self.assertEqual(status_code, 400)
        self.assertIn('Unable to log in with provided credentials.',
                      content['non_field_errors'][0])
        self.assertEqual(count, LocalUser.objects.all().count())

    def test_empty_password(self):
        count = LocalUser.objects.all().count()
        form = self._get_form()
        form['password'] = ''
        status_code, content = self.post(self.url, form, use_auth_token=False)
        self.assertEqual(status_code, 400)
        self.assertIn('This field may not be blank.',
                      content['password'][0])
        self.assertEqual(count, LocalUser.objects.all().count())

    def test_valid_form(self):
        count = LocalUser.objects.all().count()
        form = self._get_form()
        token, created = Token.objects.get_or_create(user=self.user)
        status_code, content = self.post(self.url, form, use_auth_token=False)
        self.assertEqual(status_code, 200)
        self.assertEqual(form['username'], content['email'])
        self.assertEqual(token.key, content['token'])
        self.assertEqual(count, LocalUser.objects.all().count())
