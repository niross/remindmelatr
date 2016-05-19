from django import forms
from django.forms import widgets


class BaseUserDetailsForm(forms.ModelForm):
    MONTHS = (
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'),
        (12, 'December'))

    dob_day = forms.IntegerField(widget=widgets.TextInput(attrs={
        'class': 'form-control',
        'value': 1,
        'tabindex': 2
    }), required=True)

    dob_month = forms.ChoiceField(choices=MONTHS, widget=widgets.Select(attrs={
        'tabindex': 3
    }), required=True)

    dob_year = forms.IntegerField(widget=widgets.TextInput(attrs={
        'class': 'form-control',
        'tabindex': 4,
        'placeholder': 'Year'
    }), required=True)

    country_typeahead = forms.CharField(widget=widgets.TextInput(attrs={
        'class': 'form-control',
        'tabindex': 6,
        'autocomplete': 'off',
        'data-provide': 'typeahead',
        'placeholder': 'Country'
    }), required=True)

    postcode_typeahead = forms.CharField(widget=widgets.TextInput(attrs={
        'class': 'form-control',
        'tabindex': 7,
        'autocomplete': 'off',
        'data-provide': 'typeahead',
        'placeholder': 'Postal/Zip code'
    }), required=True)
