from django.db import models

from accounts.models import LocalUser
from base.models import TimeStampedModel


class ContactMessage(TimeStampedModel):
    user = models.ForeignKey(LocalUser)
    message = models.TextField()
    replied = models.BooleanField(default=False)



