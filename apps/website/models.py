from django.db import models
from base.models import TimeStampedModel


class ContactMessage(TimeStampedModel):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()

