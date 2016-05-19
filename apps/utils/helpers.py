from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import get_object_or_404

from reminders.models import Reminder


def get_paginator(reminders, page, limit=20):
    paginator = Paginator(reminders, limit)
    try: return paginator.page(page)
    except PageNotAnInteger:
        return paginator.page(1)
    except EmptyPage:
        return paginator.page(paginator.num_pages)


def get_multiple_reminders(ids, user):
    reminders = []
    for rid in ids:
        reminder = get_object_or_404(Reminder.objects, id=rid,
                                     user=user, deleted=False)
        reminders.append(reminder)
    return reminders
