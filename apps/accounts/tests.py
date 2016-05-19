import re
from datetime import datetime, timedelta

import pytz

from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from django.test.client import RequestFactory
from django.core import mail
from django.http import HttpResponseRedirect

from allauth.account.models import EmailAddress, EmailConfirmation
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from allauth.socialaccount.views import SignupView
from allauth.socialaccount.models import SocialAccount, SocialLogin
from allauth.socialaccount.helpers import complete_social_login

from accounts.models import LocalUser
from timezones.models import Timezone

tz = pytz.timezone('UTC')


class BaseTest(TestCase):
    fixtures = ['socialapp.json', 'timezones.json']

    def setUp(self):
        self.client = Client()
        self.user = self.create_user('testuser', 'test@test.com')
        self.user.save()

    def create_user(self, username, email, password='password'):
        tz = Timezone.objects.get(pk=73)
        return LocalUser.objects.create_user(
            username, email, password, timezone=tz
        )

    def user_login(self, username=None, password='password'):
        if username is None:
            username = self.user.username
        self.client.login(username=username, password=password)

    def user_logout(self):
        self.client.logout()


class SignUpTest(BaseTest):
    fixtures = ['socialapp.json', 'timezones.json']

    def _get_form(self):
        return {
            'username': 'test01',
            'email': 'test01@test01.com',
            'password1': 'test01',
            'password2': 'test01',
            'timezone': 73,
        }

    def _create_confirmation(self, email, sent):
        confirmation = EmailConfirmation.create(email)
        confirmation.sent = sent
        confirmation.save()
        return confirmation

    def test_signup_page_load(self):
        count = LocalUser.objects.all().count()
        response = self.client.get(reverse('account_signup'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Sign Up', response.content)
        self.assertEqual(count, LocalUser.objects.all().count())

    def test_invalid_email(self):
        count = LocalUser.objects.all().count()
        form = self._get_form()
        form['email'] = 'test01'
        response = self.client.post(
            reverse('account_signup'), form, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('Enter a valid email address', response.content)
        self.assertEqual(count, LocalUser.objects.all().count())

    def test_empty_email(self):
        count = LocalUser.objects.all().count()
        form = self._get_form()
        form['email'] = ''
        response = self.client.post(
            reverse('account_signup'), form, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('This field is required', response.content)
        self.assertEqual(count, LocalUser.objects.all().count())

    def test_email_exists(self):
        count = LocalUser.objects.all().count()
        form = self._get_form()
        form['email'] = self.user.email
        response = self.client.post(
            reverse('account_signup'), form, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('A user is already registered', response.content)
        self.assertEqual(count, LocalUser.objects.all().count())

    def test_invalid_timezone(self):
        count = LocalUser.objects.all().count()
        form = self._get_form()
        form['timezone'] = '9999999'
        response = self.client.post(
            reverse('account_signup'), form, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('Select a valid choice', response.content)
        self.assertEqual(count, LocalUser.objects.all().count())

    def test_empty_timezone(self):
        count = LocalUser.objects.all().count()
        form = self._get_form()
        form['timezone'] = ''
        response = self.client.post(
            reverse('account_signup'), form, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('This field is required', response.content)
        self.assertEqual(count, LocalUser.objects.all().count())

    def test_invalid_password1(self):
        count = LocalUser.objects.all().count()
        form = self._get_form()
        form['password1'] = '1'
        response = self.client.post(
            reverse('account_signup'), form, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'Password must be a minimum of 6 characters', response.content
        )
        self.assertEqual(count, LocalUser.objects.all().count())

    def test_empty_password1(self):
        count = LocalUser.objects.all().count()
        form = self._get_form()
        form['password1'] = ''
        response = self.client.post(
            reverse('account_signup'), form, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('This field is required', response.content)
        self.assertEqual(count, LocalUser.objects.all().count())

    def test_invalid_password2(self):
        count = LocalUser.objects.all().count()
        form = self._get_form()
        form['password2'] = '1'
        response = self.client.post(
            reverse('account_signup'), form, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'You must type the same password each time', response.content
        )
        self.assertEqual(count, LocalUser.objects.all().count())

    def test_empty_password2(self):
        count = LocalUser.objects.all().count()
        form = self._get_form()
        form['password2'] = ''
        response = self.client.post(
            reverse('account_signup'), form, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('This field is required', response.content)
        self.assertEqual(count, LocalUser.objects.all().count())

    def test_password_mismatch(self):
        count = LocalUser.objects.all().count()
        form = self._get_form()
        form['password1'] = '123456'
        form['password2'] = '654321'
        response = self.client.post(
            reverse('account_signup'), form, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'You must type the same password each time', response.content
        )
        self.assertEqual(count, LocalUser.objects.all().count())

    def test_valid_form(self):
        count = LocalUser.objects.all().count()
        form = self._get_form()
        response = self.client.post(
            reverse('account_signup'), form, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('We have sent an email to you for verification',
                      response.content)
        self.assertEqual(count+1, LocalUser.objects.all().count())

        # Ensure an email is sent
        self.assertEquals(len(mail.outbox), 1)
        self.assertIn('Confirm Email Address', mail.outbox[0].subject)

    def test_valid_email_verify_link(self):
        form = self._get_form()
        self.client.post(reverse('account_signup'), form, follow=True)

        # Get the verify url from the email body
        body = mail.outbox[0].body
        url = re.match(r'.*?(http.*?)\n.*?', body, re.DOTALL).group(1)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Confirm Your Email Address', response.content)

    def test_invalid_email_verify_link(self):
        response = self.client.get(reverse('account_confirm_email',
                                   args=('abcd',)))
        self.assertEqual(response.status_code, 200)
        self.assertIn('confirmation link has expired or is invalid',
                      response.content)

    def test_expired_email_verify_link(self):
        verified_count = EmailAddress.objects.filter(verified=True).count()

        # create a user
        user = self.create_user('username', 'a@a.com', 'password')

        # create an unverified email address
        email = EmailAddress(user=user, email=user.email,
                             verified=False, primary=True)
        email.save()

        # create and email confirmation object
        confirmation = self._create_confirmation(
            email, datetime.now(tz) - timedelta(days=10)
        )

        response = self.client.post(reverse('account_confirm_email',
                                            args=(confirmation.key,)))
        self.assertEqual(response.status_code, 404)
        new_verified_count = EmailAddress.objects.filter(verified=True).count()
        self.assertEqual(verified_count, new_verified_count)

    def test_email_verify_success(self):
        verified_count = EmailAddress.objects.filter(verified=True).count()

        # create a user
        user = self.create_user('username', 'a@a.com', 'password')

        # create an unverified email address
        email = EmailAddress(user=user, email=user.email,
                             verified=False, primary=True)
        email.save()

        # create an email confirmation object
        confirmation = self._create_confirmation(
            email, datetime.now(tz) - timedelta(hours=1)
        )

        response = self.client.post(reverse('account_confirm_email',
                                            args=(confirmation.key,)))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account_login'))
        new_verified_count = EmailAddress.objects.filter(verified=True).count()
        self.assertEqual(verified_count + 1, new_verified_count)


class SignInTest(BaseTest):

    def test_login_page_load(self):
        """
        Tests that the login page is accessible
        """
        response = self.client.get(reverse('account_login'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Sign In', response.content)
        self.assertIn('Sign in with Facebook', response.content)
        self.assertIn('Sign in with Twitter', response.content)

    def test_empty_email(self):
        self.create_user('username', 'a@a.com', 'password')
        form = {
            'login': '',
            'password': 'password',
        }
        response = self.client.post(reverse('account_login'),
                                    form, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('has-error', response.content)
        self.assertIn('This field is required', response.content)

    def test_invalid_email(self):
        self.create_user('username', 'a@a.com', 'password')
        form = {
            'login': 'a@b.com',
            'password': 'password',
        }
        response = self.client.post(reverse('account_login'),
                                    form, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'e-mail address and/or password you specified are not correct',
            response.content
        )

    def test_empty_password(self):
        self.create_user('username', 'a@a.com', 'password')
        form = {
            'login': self.user.email,
            'password': '',
        }
        response = self.client.post(reverse('account_login'),
                                    form, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('has-error', response.content)
        self.assertIn('This field is required', response.content)

    def test_invalid_password(self):
        self.create_user('username', 'a@a.com', 'password')
        form = {
            'login': self.user.email,
            'password': 'drowssap',
        }
        response = self.client.post(reverse('account_login'),
                                    form, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'e-mail address and/or password you specified are not correct',
            response.content
        )

    def test_valid_form(self):
        email = EmailAddress(user=self.user, email=self.user.email,
                             verified=True, primary=True)
        email.save()
        form = {
            'login': self.user.email,
            'password': 'password',
        }
        response = self.client.post(
            reverse('account_login'),
            form, follow=True
        )
        self.assertRedirects(response, reverse('dashboard'))

    def test_form_with_valid_username(self):
        # Should error as we only accept email addresses now
        email = EmailAddress(user=self.user, email=self.user.email,
                             verified=True, primary=True)
        email.save()
        form = {
            'login': self.user.username,
            'password': 'password',
        }
        response = self.client.post(
            reverse('account_login'), form, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('Enter a valid email address', response.content)

class SignOutTest(BaseTest):

    def test_logout_get_request(self):
        self.create_user('username', 'a@a.com', 'password')
        self.client.login(username='username', password='password')
        response = self.client.get(reverse('account_logout'))
        self.assertRedirects(response, reverse('home'))

    def test_logout_post_request(self):
        self.create_user('username', 'a@a.com', 'password')
        self.client.login(username='username', password='password')
        response = self.client.post(
            reverse('account_logout'), {}, follow=True
        )
        self.assertEqual(response.status_code, 200)


class ForgotPasswordTest(BaseTest):

    def test_page_load(self):
        """
        Tests that the forgot password page is accessible
        """
        response = self.client.get(reverse('account_reset_password'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Password Reset', response.content)

    def test_empty_email(self):
        form = {
            'email': '',
        }
        response = self.client.post(reverse('account_reset_password'),
                                    form, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('has-error', response.content)
        self.assertIn('This field is required', response.content)

    def test_invalid_email(self):
        form = {
            'email': 'a.com',
        }
        response = self.client.post(reverse('account_reset_password'),
                                    form, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('has-error', response.content)
        self.assertIn('Enter a valid email address', response.content)

    def test_unregistered_email(self):
        form = {
            'email': 'abc@cba.com',
        }
        response = self.client.post(reverse('account_reset_password'),
                                    form, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('has-error', response.content)
        self.assertIn('not assigned to any user account', response.content)

    def test_valid_form(self):
        self.create_user('username', 'a@a.com', 'password')
        form = {
            'email': 'a@a.com',
        }
        response = self.client.post(reverse('account_reset_password'),
                                    form, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Password Reset', response.content)
        self.assertIn('We have sent you an email', response.content)
        # Ensure an email is sent
        self.assertEquals(len(mail.outbox), 1)
        self.assertIn('Password Reset', mail.outbox[0].subject)

    def test_reset_logged_in_user(self):
        self.create_user('username', 'a@a.com', 'password')
        self.client.login(username='username', password='password')
        response = self.client.get(reverse('account_reset_password'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('you are already logged in as username.',
                      response.content)

    def test_reset_done_logged_in_user(self):
        self.create_user('username', 'a@a.com', 'password')
        self.client.login(username='username', password='password')
        response = self.client.get(reverse('account_reset_password_done'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('you are already logged in as username.',
                      response.content)


class SocialLoginFailureTest(BaseTest):

    def test_social_login_error(self):
        response = self.client.get(reverse('socialaccount_login_error'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Login Failure', response.content)
        self.assertIn('An error occurred', response.content)

    def test_social_login_failure(self):
        response = self.client.get(reverse('socialaccount_login_cancelled'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Login Cancelled', response.content)
        self.assertIn('You have decided to cancel logging', response.content)


class SocialSignUp(BaseTest):

    def _create_request(self, provider, process, user, url, method, data=None):

        factory = RequestFactory()
        request = factory.get('/accounts/login/callback/')

        factory = RequestFactory()
        if method == 'GET':
            request = factory.get(url)
        else:
            request = factory.post(url, data)

        request.user = AnonymousUser()
        SessionMiddleware().process_request(request)
        MessageMiddleware().process_request(request)

        user = LocalUser(username='test', email='test@test.com')
        account = SocialAccount(user=user, provider=provider, uid='123')
        sociallogin = SocialLogin(user=user, account=account)

        if process is not None:
            sociallogin.state['process'] = process

        complete_social_login(request, sociallogin)

        return request

    def test_signup_page_load_no_session_data(self):
       response = self.client.get(reverse('socialaccount_signup'), follow=True)
       self.assertRedirects(response, reverse('account_login'))
       self.assertIn('Sign Up', response.content)

    # Facebook OAuth

    def test_facebook_signup_page_load_with_session_data(self):
        request = self._create_request('facebook', None, self.user,
                                       '/accounts/login/callback/', 'GET')
        response = SignupView.as_view()(request).render()
        self.assertIn('Sign Up', response.content)
        self.assertIn('Facebook', response.content)

    def test_facebook_complete_signup_empty_email(self):
        post_data = {
            'email': '',
            'timezone': 73,
        }
        request = self._create_request(
            'facebook', None, self.user, reverse('socialaccount_signup'),
            'POST', post_data
        )

        response = SignupView.as_view()(request).render()
        self.assertEqual(response.status_code, 200)
        self.assertIn('This field is required', response.content)

    def test_facebook_complete_signup_invalid_email(self):
        post_data = {
            'email': 'test.com',
            'timezone': 73,
        }
        request = self._create_request(
            'facebook', None, self.user, reverse('socialaccount_signup'),
            'POST', post_data
        )

        response = SignupView.as_view()(request).render()
        self.assertEqual(response.status_code, 200)
        self.assertIn('Enter a valid email address', response.content)

    def test_facebook_complete_signup_existing_email(self):
        user = LocalUser(username='testuser', email='test@test.com')
        post_data = {
            'email': 'test@test.com',
            'timezone': 73,
        }
        request = self._create_request(
            'facebook', None, user, reverse('socialaccount_signup'),
            'POST', post_data
        )
        response = SignupView.as_view()(request).render()
        self.assertEqual(response.status_code, 200)
        self.assertIn('account already exists', response.content)

    def test_facebook_complete_signup_empty_timezone(self):
        post_data = {
            'email': 'test@test.com',
            'timezone': '',
        }
        request = self._create_request(
            'facebook', None, self.user, reverse('socialaccount_signup'),
            'POST', post_data
        )
        response = SignupView.as_view()(request).render()
        self.assertEqual(response.status_code, 200)
        self.assertIn('This field is required', response.content)

    def test_facebook_complete_signup_invalid_timezone(self):
        post_data = {
            'email': 'test@test.com',
            'timezone': 9999,
        }
        request = self._create_request(
            'facebook', None, self.user, reverse('socialaccount_signup'),
            'POST', post_data
        )
        response = SignupView.as_view()(request).render()
        self.assertEqual(response.status_code, 200)
        self.assertIn('Select a valid choice', response.content)

    def test_facebook_complete_signup_valid_form(self):
        user_count = LocalUser.objects.all().count()
        post_data = {
            'email': 'testuservalid@test.com',
            'timezone': 73,
        }
        request = self._create_request(
            'facebook', None, self.user, reverse('socialaccount_signup'),
            'POST', post_data
        )
        response = SignupView.as_view()(request)
        self.assertTrue(isinstance(response, HttpResponseRedirect))
        self.assertEqual(
            response.get('location'),
            reverse('account_email_verification_sent')
        )
        self.assertEqual(user_count + 1, LocalUser.objects.all().count())

    # Twitter OAuth

    def test_twitter_signup_page_load_with_session_data(self):
        request = self._create_request('twitter', None, self.user,
                                       '/accounts/login/callback/', 'GET')
        response = SignupView.as_view()(request).render()
        self.assertIn('Sign Up', response.content)
        self.assertIn('Email', response.content)
        self.assertIn('Timezone', response.content)

    def test_twitter_complete_signup_empty_email(self):
        post_data = {
            'email': '',
            'timezone': 73,
        }
        request = self._create_request(
            'twitter', None, self.user, reverse('socialaccount_signup'),
            'POST', post_data
        )
        response = SignupView.as_view()(request).render()
        self.assertEqual(response.status_code, 200)
        self.assertIn('This field is required', response.content)

    def test_twitter_complete_signup_invalid_email(self):
        post_data = {
            'email': 'a',
            'timezone': 73,
        }
        request = self._create_request(
            'twitter', None, self.user, reverse('socialaccount_signup'),
            'POST', post_data
        )

        response = SignupView.as_view()(request).render()
        self.assertEqual(response.status_code, 200)
        self.assertIn('Enter a valid email address', response.content)

    def test_twitter_complete_signup_existing_email(self):
        post_data = {
            'email': 'test@test.com',
            'timezone': 73,
        }
        user = LocalUser(username='testuser', email='test@test.com')
        request = self._create_request(
            'twitter', None, user, reverse('socialaccount_signup'),
            'POST', post_data
        )

        response = SignupView.as_view()(request).render()
        self.assertEqual(response.status_code, 200)
        self.assertIn('account already exists', response.content)

    def test_twitter_complete_signup_empty_timezone(self):
        post_data = {
            'email': 'test@test.com',
            'timezone': '',
        }
        request = self._create_request(
            'twitter', None, self.user, reverse('socialaccount_signup'),
            'POST', post_data
        )

        response = SignupView.as_view()(request).render()
        self.assertEqual(response.status_code, 200)
        self.assertIn('This field is required', response.content)

    def test_twitter_complete_signup_invalid_timezone(self):
        post_data = {
            'email': 'test@test.com',
            'timezone': 9999,
        }
        request = self._create_request(
            'twitter', None, self.user, reverse('socialaccount_signup'),
            'POST', post_data
        )
        response = SignupView.as_view()(request).render()
        self.assertEqual(response.status_code, 200)
        self.assertIn('Select a valid choice', response.content)

    def test_twitter_complete_signup_valid_form(self):
        user_count = LocalUser.objects.all().count()
        post_data = {
            'email': 'testuservalid@test.com',
            'timezone': 73,
        }
        request = self._create_request(
            'twitter', None, self.user, reverse('socialaccount_signup'),
            'POST', post_data
        )
        response = SignupView.as_view()(request)
        self.assertTrue(isinstance(response, HttpResponseRedirect))
        self.assertEqual(
            response.get('location'),
            reverse('account_email_verification_sent')
        )
        self.assertEqual(user_count + 1, LocalUser.objects.all().count())
