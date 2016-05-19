from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.core.urlresolvers import reverse

from .forms import ContactForm


@login_required
def contact(request):
    form = ContactForm(request.POST)
    if form.is_valid():
        con = form.save(commit=False)
        con.user = request.user
        con.save()
        messages.success(request, 'Contact message sent successfully')
    else:
        messages.error(request,
                       'Please enter a message before making contact')
    return HttpResponseRedirect(request.POST.get('next', reverse('home')))
