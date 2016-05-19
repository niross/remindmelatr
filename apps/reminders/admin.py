from __future__ import absolute_import
from django.contrib import admin

from reminders.models import Reminder, RemindOn


class RemindOnAdmin(admin.ModelAdmin):
    pass
admin.site.register(RemindOn, RemindOnAdmin)


class ReminderAdmin(admin.ModelAdmin):
    pass
admin.site.register(Reminder, ReminderAdmin)
