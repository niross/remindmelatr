from django import forms
from django.forms import widgets

from bootstrap_toolkit.widgets import BootstrapTextInput

from .models import LocalUser


class CustomSignupForm(forms.ModelForm):
    """
    Confirm a users timezone on signup
    """

    class Meta:
        model = LocalUser
        fields = ('timezone',)
        widgets = {
            'timezone': widgets.Select(attrs={
                'class': 'tzselect select-block',
                'placeholder': 'Your timezone'
            })
        }

    def __init__(self, *args, **kwargs):
        super(CustomSignupForm, self).__init__(*args, **kwargs)
        self.fields['timezone'].empty_label = 'Select your timezone'

    def signup(self, request, user):
        user.timezone = self.cleaned_data['timezone']
        user.timezone_id = user.timezone.id
        user.save()
        return user

    def save(self, commit=True):
        user = super(CustomSignupForm, self).save(commit=False)
        return self.signup(None, user)


class LocalUserForm(forms.ModelForm):
    """
    User settings form
    """
    class Meta:
        model = LocalUser
        fields = ('email', 'timezone')
        widgets = {
            'timezone': widgets.Select(attrs={
                'class': 'tzselect select-block',
                'placeholder': 'Your timezone'
            }),
            'email': BootstrapTextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Please enter your email address',
                'title': 'Your email address cannot be changed currently',
                'readonly': 'readonly',
            }),
        }

class UserSingleUpdateForm(forms.ModelForm):
    """
    Form to set a single user setting
    """

    class Meta:
        model = LocalUser
        fields = ('username', 'email', 'timezone', 'show_welcome_message')
