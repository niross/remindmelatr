from django.db.models.signals import post_save
from django.contrib.sites.models import Site
from django.dispatch import receiver
from django.core.mail import mail_admins

from contact.models import ContactMessage


@receiver(post_save, sender=ContactMessage, dispatch_uid='contact.save')
def contact_save(sender, **kwargs):
    site = Site.objects.get_current()
    contact = kwargs['instance']
    subject = 'Contact message received on %s' % site.name
    msg = 'The following message was receveived at %s\n\n' % contact.created
    msg += 'User: %s\n' % contact.user.username
    msg += 'Email: %s\n' % contact.user.email
    msg += 'Message: \n%s\n\n' % contact.message
    mail_admins(subject, msg)
