from __future__ import absolute_import
import json
from random import randint
import logging

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.conf import settings

from .models import Reminder, RemindOn, RemindAt
from .forms import BasicReminderForm, ExternalSnoozeForm, QuickReminderForm
from utils.helpers import get_paginator, get_multiple_reminders

logger = logging.getLogger(__name__)


@login_required
def dashboard(request):
    overdue = Reminder.objects.overdue(user=request.user)
    outstanding = Reminder.objects.outstanding(user=request.user)
    completed = Reminder.objects.completed(user=request.user)
    reminders = Reminder.objects.incomplete(user=request.user)
    demo = settings.DEMO_REMINDERS[randint(0, len(settings.DEMO_REMINDERS)-1)]
    form = QuickReminderForm()

    if request.user.is_new:
        request.user.is_new = False
        request.user.save()

    if request.method == 'POST':
        form = QuickReminderForm(request.POST)
        if form.is_valid():
            reminder = form.save(commit=False)
            reminder.user = request.user
            reminder.save()
            messages.success(request, reminder.success_message())
            reminder.add_history_entry('Reminder created for %s.'.format(
                reminder.localised_start().strftime('%H:%M on %d/%m/%y'))
            )
            return HttpResponseRedirect(reverse('dashboard'))

    return render_to_response('dashboard.html', {
        'overdue': overdue,
        'outstanding': outstanding,
        'completed': completed,
        'reminders': reminders,
        'demo_reminder': demo,
        'quick_reminder_form': form,
        'user': request.user,
    }, context_instance=RequestContext(request))


@login_required
def reminder(request, reminder_id):
    rem = get_object_or_404(
        Reminder.objects, user=request.user,
        id=reminder_id, deleted=False
    )

    history = get_paginator(rem.history(), request.GET.get('page', 1), 10)

    return render_to_response('reminder.html', {
        'reminder': rem,
        'history': history,
    }, context_instance=RequestContext(request))


@login_required
def new(request):

    default_remind_on = 'Today'
    if request.session.get('remind_on', False):
        default_remind_on = request.session['remind_on']

    if request.method == 'POST':
        form = BasicReminderForm(request.POST)
        if form.is_valid():
            reminder = form.save(commit=False)
            reminder.user = request.user
            reminder.save()
            messages.success(request, reminder.success_message())
            request.session['remind_on'] = \
                request.POST['remind_on'].capitalize()
            reminder.add_history_entry('Reminder created for %s.'.format(
                reminder.localised_start().strftime('%H:%M on %d/%m/%y')
            ))
            return HttpResponseRedirect(reverse('new'))
    else:
        form = BasicReminderForm(initial={'remind_on': default_remind_on})

    return render_to_response('new_reminder.html', {
        'form': form,
    }, context_instance=RequestContext(request))


@login_required
def edit(request, reminder_id):
    reminder = get_object_or_404(
        Reminder.objects, user=request.user, id=reminder_id, deleted=False
    )
    form = BasicReminderForm(
        instance=reminder, initial=reminder.initial_form_values()
    )

    orig_start = reminder.localised_start()
    orig_content = reminder.content
    if request.method == 'POST':
        form = BasicReminderForm(request.POST, instance=reminder)
        if form.is_valid():
            reminder = form.save()
            messages.success(request, reminder.edited_message())

            new_start = reminder.localised_start()
            if new_start != orig_start:
                reminder.add_history_entry('Reminder set for {}.'.format(
                    new_start.strftime('%H:%M on %d/%m/%y')
                ))

            if reminder.content != orig_content:
                extra = 'Content was:\n%s\n\nAfter update:\n{}'.format(
                    orig_content, reminder.content
                )
                reminder.add_history_entry(
                    'Reminder content updated', extra=extra
                )

            return HttpResponseRedirect(
                request.POST.get('next', reverse('reminders'))
            )

    return render_to_response('new_reminder.html', {
        'form': form,
        'reminder': reminder,
        'next': request.POST.get('next', reverse('reminders')),
    }, context_instance=RequestContext(request))


@login_required
def reminders(request):
    if Reminder.objects.overdue(user=request.user).count() > 0:
        return HttpResponseRedirect(reverse('overdue'))
    return HttpResponseRedirect(reverse('upcoming'))


@login_required
def overdue(request):
    reminders = get_paginator(
        Reminder.objects.overdue(user=request.user),
        request.GET.get('page', 1)
    )
    return render_to_response('reminders/overdue.html', {
        'reminders': reminders,
    }, context_instance=RequestContext(request))


@login_required
def upcoming(request):
    reminders = get_paginator(
        Reminder.objects.outstanding(user=request.user),
        request.GET.get('page', 1)
    )
    return render_to_response('reminders/upcoming.html', {
        'reminders': reminders,
    }, context_instance=RequestContext(request))


@login_required
def paused(request):
    reminders = get_paginator(
        Reminder.objects.paused(user=request.user),
        request.GET.get('page', 1)
    )
    return render_to_response('reminders/paused.html', {
        'reminders': reminders,
    }, context_instance=RequestContext(request))


@login_required
def completed(request):
    reminders = get_paginator(
        Reminder.objects.completed(user=request.user),
        request.GET.get('page', 1)
    )
    return render_to_response('reminders/completed.html', {
        'reminders': reminders,
    }, context_instance=RequestContext(request))


@login_required
def delete(request, reminder_id):
    reminder = get_object_or_404(
        Reminder.objects, user=request.user,
        id=reminder_id, deleted=False
    )
    if request.method == 'POST':
        reminder.soft_delete()
        message = 'Reminder deleted successfully'
        messages.success(request, message)
        return HttpResponseRedirect(
            request.POST.get(
            'next', reverse('reminders'))
        )
    else:
        return HttpResponseRedirect('%s?next=%s' % (
            reverse('confirm_delete', args=(reminder.id,)),
            request.GET.get('next', reverse('reminders')))
        )


@login_required
def delete_multiple(request):
    if request.method == 'POST':
        ids = request.POST['reminder_ids'].split(',')
        reminders = get_multiple_reminders(ids, request.user)
        for reminder in reminders:
            reminder.soft_delete()
        message = '%s reminders deleted successfully' % len(reminders)
        messages.success(request, message)
        return HttpResponseRedirect(
            request.POST.get(
            'next', reverse('reminders'))
        )


@login_required
def pause(request, reminder_id):
    reminder = get_object_or_404(
        Reminder.objects, user=request.user, id=reminder_id, deleted=False
    )
    reminder.pause()
    messages.success(request, reminder.pause_message())
    return HttpResponseRedirect(
        request.POST.get(
        'next', reverse('reminders'))
    )


@login_required
def pause_multiple(request):
    if request.method == 'POST':
        ids = request.POST['reminder_ids'].split(',')
        reminders = get_multiple_reminders(ids, request.user)
        for reminder in reminders:
            reminder.pause()
        message = '%s reminders paused successfully' % len(reminders)
        messages.success(request, message)
        return HttpResponseRedirect(
            request.POST.get(
            'next', reverse('reminders'))
        )


@login_required
def unpause(request, reminder_id):
    reminder = get_object_or_404(Reminder.objects, user=request.user,
                                 id=reminder_id, deleted=False)
    reminder.unpause()
    messages.success(request, reminder.unpause_message())
    return HttpResponseRedirect(
        request.POST.get(
        'next', reverse('reminders'))
    )


@login_required
def unpause_multiple(request):
    if request.method == 'POST':
        ids = request.POST['reminder_ids'].split(',')
        reminders = get_multiple_reminders(ids, request.user)
        for reminder in reminders:
            reminder.unpause()
        message = '%s reminders activated successfully' % len(reminders)
        messages.success(request, message)
        return HttpResponseRedirect(
            request.POST.get(
            'next', reverse('reminders'))
        )


@login_required
def complete(request, reminder_id):
    reminder = get_object_or_404(Reminder.objects, user=request.user,
                                 id=reminder_id, deleted=False)
    if request.method == 'POST':
        reminder.complete()
        message = '<strong>Well Done!</strong> Reminder completed successfully'
        messages.success(request, message)
        return HttpResponseRedirect(
            request.POST.get(
            'next', reverse('reminders'))
        )
    else:
        return HttpResponseRedirect(
            reverse('confirm_complete', args=(reminder.id,))
        )


@login_required
def complete_multiple(request):
    if request.method == 'POST':
        ids = request.POST['reminder_ids'].split(',')
        reminders = get_multiple_reminders(ids, request.user)
        for reminder in reminders:
            reminder.complete()

        message = '%s reminders completed successfully' % len(reminders)
        messages.success(request, message)
        return HttpResponseRedirect(
            request.POST.get(
            'next', reverse('reminders'))
        )


@login_required
def snooze(request, reminder_id):
    reminder = get_object_or_404(Reminder.objects, id=reminder_id,
                                 user=request.user)

    if request.method == 'POST':
        form = ExternalSnoozeForm(request.POST, instance=reminder)
        if form.is_valid():
            form.save()
            messages.success(request, reminder.snooze_message())
            return HttpResponseRedirect(
                request.POST.get('next',
                reverse('reminders'))
            )
    else:
        form = ExternalSnoozeForm(instance=reminder)

    return render_to_response('external/snooze.html', {
        'reminder': reminder,
        'form': form,
        'next': request.GET.get('next', reverse('reminders')),
    }, context_instance=RequestContext(request))


@login_required
def confirm_complete(request, reminder_id):

    reminder = get_object_or_404(
        Reminder.objects, user=request.user, id=reminder_id
    )

    return render_to_response('external/complete.html', {
        'reminder': reminder,
    }, context_instance=RequestContext(request))


@login_required
def reminder_external(request, hash_digest):
    reminder = get_object_or_404(
        Reminder.objects, user=request.user, hash_digest=hash_digest
    )

    return HttpResponseRedirect(
        reverse('reminder', args=(reminder.id,))
    )


@login_required
def confirm_complete_external(request, hash_digest):
    reminder = get_object_or_404(
        Reminder.objects, user=request.user, hash_digest=hash_digest
    )

    return HttpResponseRedirect(
        reverse('confirm_complete', args=(reminder.id,))
    )


@login_required
def snooze_external(request, hash_digest):
    reminder = get_object_or_404(
        Reminder.objects, user=request.user, hash_digest=hash_digest
    )

    return HttpResponseRedirect(reverse('snooze', args=(reminder.id,)))


@login_required
def confirm_delete(request, reminder_id):

    reminder = get_object_or_404(
        Reminder.objects, user=request.user, id=reminder_id
    )

    return render_to_response('external/delete.html', {
        'reminder': reminder,
        'next': request.GET.get('next', None),
    }, context_instance=RequestContext(request))


@login_required
def on_options(request):
    q = request.GET.get('query', '')
    values = [r.name for r in RemindOn.objects.filter(name__icontains=q)]
    return HttpResponse(json.dumps(values), 'application/json; charset=utf8')


@login_required
def at_options(request):
    q = request.GET.get('query', '')
    values = [r.name for r in RemindAt.objects.filter(name__icontains=q)]
    return HttpResponse(json.dumps(values), 'application/json; charset=utf8')
