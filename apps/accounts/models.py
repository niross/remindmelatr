from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver

from rest_framework.authtoken.models import Token

from base.models import TimeStampedModel
from timezones.models import Timezone


class LocalUser(AbstractUser, TimeStampedModel):
    timezone = models.ForeignKey(Timezone, null=True)
    is_new = models.BooleanField(default=True)
    show_welcome_message = models.BooleanField(default=True)

    def __unicode__(self):
        return self.username


# Create an auth token on initial save
@receiver(post_save, sender=LocalUser)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
