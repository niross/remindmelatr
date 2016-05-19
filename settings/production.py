from datetime import timedelta

from common import *

DEBUG = False
TEMPLATE_DEBUG = DEBUG

# Set this to true if you are using https
SESSION_COOKIE_SECURE = True

CSRF_COOKIE_SECURE = True

CELERYBEAT_SCHEDULE = {
    'add-every-10-seconds': {
        'task': 'reminders.tasks.scheduler',
        'schedule': timedelta(seconds=10),
    },
}
