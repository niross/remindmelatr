from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core import mail

from website.models import ContactMessage


class ContactTest(TestCase):

    def _get_form(self):
        return {
            'name': 'Test01',
            'email': 'test01@test.com',
            'message': 'test message',
        }

    # page load
    def test_page_load(self):
        response = self.client.get(reverse('website_contact'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Contact Us', response.content)

    # empty name field
    def test_empty_name(self):
        form = self._get_form()
        form['name'] = ''
        response = self.client.post(
            reverse('website_contact'), form, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('This field is required', response.content)

    # empty email field
    def test_empty_email(self):
        form = self._get_form()
        form['email'] = ''
        response = self.client.post(
            reverse('website_contact'), form, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('This field is required', response.content)

    # invalid email address
    def test_invalid_email(self):
        form = self._get_form()
        form['email'] = 'test01'
        response = self.client.post(
            reverse('website_contact'), form, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('Enter a valid email address', response.content)

    # empty message
    def test_invalid_email(self):
        form = self._get_form()
        form['message'] = ''
        response = self.client.post(
            reverse('website_contact'), form, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('This field is required', response.content)

    # valid form
    def test_valid_form(self):
        contact_count = ContactMessage.objects.all().count()
        mail_count = len(mail.outbox)
        form = self._get_form()
        response = self.client.post(
            reverse('website_contact'), form, follow=True
        )
        self.assertRedirects(response, reverse('home'))
        self.assertIn('message sent successfully', response.content)
        self.assertEqual(contact_count+1, ContactMessage.objects.all().count())
        self.assertEquals(mail_count+1, len(mail.outbox))
        self.assertIn('Contact message received', mail.outbox[0].subject)
