from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages

from website.forms import ContactForm

def home(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('dashboard'))

    return render_to_response('home.html', {
    }, context_instance=RequestContext(request))


def contact(request):
    form = ContactForm()
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            msg = 'Contact message sent successfully'
            messages.success(request, msg)
            return HttpResponseRedirect(reverse('home'))

    return render_to_response('contact.html', {
        'form': form,
    }, context_instance=RequestContext(request))


def about(request):
    return render_to_response('about.html', {
    }, context_instance=RequestContext(request))


def privacy(request):
    return render_to_response('privacy.html', {
    }, context_instance=RequestContext(request))


def terms(request):
    return render_to_response('terms.html', {
    }, context_instance=RequestContext(request))


def custom_500(request):
    return render_to_response('500.html', {
    }, context_instance=RequestContext(request))
