from django.test import TestCase
from django.test import Client
from django.core.urlresolvers import reverse
from django.core import mail

from accounts.models import LocalUser
from contact.models import ContactMessage


class BaseTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = self.create_user('testuser', 'test@test.com')
        self.user.is_new_user = False
        self.user.save()
        self.user_login()

    def create_user(self, username, email, password='password'):
        return LocalUser.objects.create_user(username, email, password)

    def user_login(self, username=None, password='password'):
        if username is None:
            username = self.user.username
        self.client.login(username=username, password=password)
        self.user_password = password


class ContactTest(BaseTest):
    """
    Test creating a contact message
    """

    def test_contact_popup_display(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Contact Us', response.content)

    def test_submit_no_message(self):
        msg_count = ContactMessage.objects.all().count()
        form = {'message': '', 'next': reverse('dashboard')}
        response = self.client.post(reverse('contact'), form, follow=True)
        self.assertRedirects(response, reverse('dashboard'))
        self.assertIn('Please enter a message', response.content)
        self.assertEqual(msg_count, ContactMessage.objects.all().count())

    def test_valid_submit(self):
        msg_count = ContactMessage.objects.all().count()
        mail_count = len(mail.outbox)
        form = {'message': 'test message', 'next': reverse('dashboard')}
        response = self.client.post(reverse('contact'), form, follow=True)
        self.assertRedirects(response, reverse('dashboard'))
        self.assertIn('Contact message sent successfully', response.content)
        self.assertEqual(msg_count+1, ContactMessage.objects.all().count())
        self.assertEquals(mail_count+1, len(mail.outbox))
        self.assertIn('Contact message received', mail.outbox[0].subject)
