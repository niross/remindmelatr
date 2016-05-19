from django import forms
from django.forms import widgets

from .models import ContactMessage

class ContactForm(forms.ModelForm):

    class Meta:
        model = ContactMessage
        fields = ('message',)
        widgets = {
            'message': widgets.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Your message goes here'
            })
        }
