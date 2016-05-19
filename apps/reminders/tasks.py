from __future__ import absolute_import

from celery import shared_task

from .models import Reminder


@shared_task
def run_reminder(reminder):
    print "*"*80
    print "GO A REMINDER"
    reminder.remind()


@shared_task
def scheduler():
    for r in Reminder.objects.valid():
        run_reminder.delay(r)

