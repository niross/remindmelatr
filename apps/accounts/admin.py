from django.contrib import admin
from .models import LocalUser


class LocalUserAdmin(admin.ModelAdmin):
    pass
admin.site.register(LocalUser, LocalUserAdmin)
