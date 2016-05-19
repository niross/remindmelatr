from common import *
from datetime import timedelta
import warnings

# Turn datetime warnings into exceptions
warnings.filterwarnings(
    'error', r'DateTimeField .* received a naive datetime',
    RuntimeWarning, r'django\.db\.models\.fields'
)

DEBUG = True

# To extend any settings from settings/base.py here's an example:
INSTALLED_APPS = INSTALLED_APPS + ('django_nose',)

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Is this a development instance? Set this to True on development/master
# instances and False on stage/prod.
DEV = True

# Uncomment these to activate and customize Celery:
BROKER_URL = 'django://'
CELERY_RESULT_BACKEND='djcelery.backends.database:DatabaseBackend'
CELERY_TIMEZONE = 'Europe/London'

CELERYBEAT_SCHEDULE = {
    'add-every-10-seconds': {
        'task': 'reminders.tasks.scheduler',
        'schedule': timedelta(seconds=10),
    },
}

## Log settings
LOGGING = {
   'version': 1,
   'disable_existing_loggers': True,
   'formatters': {
       'simple': {
           'format': '%(levelname)s %(message)s',
       },
   },
   'handlers': {
       'console':{
           'level':'DEBUG',
           'class':'logging.StreamHandler',
           'formatter': 'simple'
       },
   },
   'loggers': {
       'django': {
           'handlers': ['console'],
           'level': 'DEBUG',
       },
   }
}

INTERNAL_IPS = ('127.0.0.1',)
