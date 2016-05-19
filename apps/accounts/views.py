from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib import messages
from django.core.urlresolvers import reverse

from .models import LocalUser
from .forms import LocalUserForm


@login_required
def settings(request):
    form = LocalUserForm(instance=request.user)
    if request.method == 'POST':
        form = LocalUserForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            msg = 'Your account was updated successfully'
            messages.success(request, msg)
            return HttpResponseRedirect(reverse('settings'))

    return render_to_response('settings.html', {
        'form': form,
    }, context_instance=RequestContext(request))


@login_required
def update_setting(request):
    if request.method == 'POST':
        field = request.POST['field']
        value = request.POST['value']
        field_type = LocalUser._meta.get_field(
                'show_welcome_message').get_internal_type()

        if field_type == 'BooleanField' or field_type == 'IntegerField':
            try:
                value = int(value)
            except ValueError:
                pass

        setattr(request.user, field, value)
        request.user.save()

    return HttpResponseRedirect(
        request.POST.get('next', reverse('dashboard'))
    )
