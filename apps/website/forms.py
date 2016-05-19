from django import forms
from django.forms import widgets
from bootstrap_toolkit.widgets import BootstrapTextInput
from website.models import ContactMessage


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ('name', 'email', 'message')
        widgets = {
            'name': BootstrapTextInput(attrs={
                'autofocus': 'autofocus',
                'class': 'form-control',
                'tabindex': 1,
                'placeholder': 'What\'s your name?',
            }),
            'email': BootstrapTextInput(attrs={
                'class': 'form-control',
                'tabindex': 2,
                'placeholder': 'What\'s your email address?',
            }),
            'message': widgets.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'tabindex': 3,
                'placeholder': 'What would you like to say?',
            }),
        }
