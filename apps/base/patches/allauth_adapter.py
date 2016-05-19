import os

from django.template.loader import render_to_string
from django.template import TemplateDoesNotExist
from django.core.mail import EmailMultiAlternatives, EmailMessage
from email.mime.image import MIMEImage
from django.conf import settings

from allauth.account.adapter import DefaultAccountAdapter


class RemindmelatrAccountAdapter(DefaultAccountAdapter):
    """
    Attaches the company logo to any emails sent from allauth
    """

    def render_mail(self, template_prefix, email, context):
        """
        Renders an e-mail to `email`.  `template_prefix` identifies the
        e-mail that is to be sent, e.g. "account/email/email_confirmation"
        """
        subject = render_to_string('{0}_subject.txt'.format(template_prefix),
                                   context)
        # remove superfluous line breaks
        subject = " ".join(subject.splitlines()).strip()
        subject = self.format_email_subject(subject)

        bodies = {}
        for ext in ['html', 'txt']:
            try:
                template_name = '{0}_message.{1}'.format(template_prefix, ext)
                bodies[ext] = render_to_string(template_name,
                                               context).strip()
            except TemplateDoesNotExist:
                if ext == 'txt' and not bodies:
                    # We need at least one body
                    raise

        if 'txt' in bodies:
            msg = EmailMultiAlternatives(subject,
                                         bodies['txt'],
                                         settings.DEFAULT_FROM_EMAIL,
                                         [email])
            if 'html' in bodies:
                msg.attach_alternative(bodies['html'], 'text/html')
                msg.mixed_subtype = 'related'
                logo_path = settings.EMAIL_LOGO
                with open(logo_path, 'rb') as fp:
                    msg_img = MIMEImage(fp.read())
                    msg_img.add_header(
                        'Content-ID', '<%s>' % os.path.basename(logo_path)
                    )
                    msg.attach(msg_img)

        else:
            msg = EmailMessage(subject,
                               bodies['html'],
                               settings.DEFAULT_FROM_EMAIL,
                               [email])
            msg.content_subtype = 'html'  # Main content is now text/html
        return msg

