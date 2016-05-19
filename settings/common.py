import sys
import logging
from .toolbar import custom_show_toolbar
import environ


ADMINS = ()
MANAGERS = ADMINS

ALLOWED_HOSTS = ['*']

PROJECT_ROOT = environ.Path(__file__) - 2
sys.path.append(str(PROJECT_ROOT('apps')))

env = environ.Env()

DEBUG = env.bool("DJANGO_DEBUG", False)


SUPPORTED_NONLOCALES = ['media', 'admin', 'static']

# Make django timezone aware
USE_TZ = True

DATABASES = {
    # Raises ImproperlyConfigured exception if DATABASE_URL not in os.environ
    'default': env.db("DATABASE_URL"),
}
DATABASES['default']['ATOMIC_REQUESTS'] = True


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'UTC'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-gb'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = str(PROJECT_ROOT.path('static'))

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = str(PROJECT_ROOT('static', 'media'))

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = '/static/admin/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.DefaultStorageFinder',
    'compressor.finders.CompressorFinder',
)

FILE_UPLOAD_PERMISSIONS = 0664

# The WSGI Application to use for runserver
WSGI_APPLICATION = 'base.wsgi.application'

MIDDLEWARE_CLASSES = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'commonware.middleware.FrameOptionsHeader',
    'reminders.middleware.TimezoneMiddleware',
]

# Package/module name to import the root urlpatterns from for the project.
ROOT_URLCONF = "urls"

# Application definition
INSTALLED_APPS = (
    # Django contrib apps
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.humanize',
    'django.contrib.syndication',
    'django.contrib.staticfiles',
    'django.contrib.gis',

    # Third-party apps, patches, fixes
    'commonware.response.cookies',
    'djcelery',
    'kombu.transport.django',
    'compressor',
    'avatar',
    'rest_framework',
    'rest_framework.authtoken',

    # Auth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.twitter',

    # bootstrap forms
    'bootstrap_toolkit',

    # Application base, containing global templates.
    'base',

    # New timezone app
    'timezones',

    # Users and stuff
    'accounts',

    # reminder app
    'reminders',

    # contact app
    'contact',

    # Internet facing site
    'website',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            str(PROJECT_ROOT('templates')),
            str(PROJECT_ROOT('templates', 'allauth')),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                "django.contrib.auth.context_processors.auth",
                'django.core.context_processors.debug',
                'django.core.context_processors.i18n',
                'django.core.context_processors.media',
                'django.core.context_processors.static',
                'django.core.context_processors.tz',
                'django.core.context_processors.request',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
                'django.core.context_processors.csrf',
                'base.context_processors.site',
                'contact.context_processors.contact_form',
            ],
        },
    },
]


# Place bcrypt first in the list, so it will be the default password hashing
# mechanism
PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.SHA1PasswordHasher',
    'django.contrib.auth.hashers.MD5PasswordHasher',
    'django.contrib.auth.hashers.CryptPasswordHasher',
)

AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",

    # `allauth` specific authentication methods, such as login by e-mail
    "allauth.account.auth_backends.AuthenticationBackend",
)

# Sessions
#
# By default, be at least somewhat secure with our session cookies.
SESSION_COOKIE_HTTPONLY = True

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOG_LEVEL = logging.INFO
HAS_SYSLOG = True
SYSLOG_TAG = "http_app_remindmelatr"  # Make this unique to your project.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': [],
            'email_backend': 'django_ses.SESBackend',
        },
        'logfile': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(PROJECT_ROOT('log', 'rml.log')),
            'maxBytes': 50000,
            'backupCount': 2,
        },
        'console':{
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'reminders': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
        },
    }
}


# Django settings
SECRET_KEY = env.str('DJANGO_SECRET_KEY')
AUTH_USER_MODEL = "accounts.LocalUser"
LOGIN_REDIRECT_URL = '/app/dashboard/'
LOGIN_URL = '/app/login/'

# All Auth Settings
ACCOUNT_ADAPTER = 'base.patches.allauth_adapter.RemindmelatrAccountAdapter'
ACCOUNT_USERNAME_MIN_LENGTH = 4
ACCOUNT_PASSWORD_MIN_LENGTH = 6
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_AUTHENTICATION_METHOD = 'email'
SOCIALACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_SIGNUP_FORM_CLASS = 'accounts.forms.CustomSignupForm'
SOCIALACCOUNT_AUTO_SIGNUP = False

# Email Settings
FROM_EMAIL = env.str('FROM_EMAIL', 'noreply@example.com')
SERVER_EMAIL = FROM_EMAIL
DEFAULT_FROM_EMAIL = FROM_EMAIL
EMAIL_BACKEND = 'django_ses.SESBackend'

# Required to send emails via Amazon SES
AWS_ACCESS_KEY_ID = env.str('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = env.str('AWS_SECRET_ACCESS_KEY', '')

SOUTH_TESTS_MIGRATE = False

EMAIL_LOGO = str(PROJECT_ROOT(
    'apps', 'base', 'static', 'images', 'remindmelatr-whitebg.png'
))

DEMO_REMINDERS = (
    'Hairdresser 7pm',
    'Pick up laundry 10am tomorrow',
    'Get the kids from school 3pm',
    'Mow the lawn Saturday 14:00',
    'Ten am Friday call Grandma',
    'Dance lessons midnight Sunday',
    'Meet Bob midday Wednesday',
    'Have something to eat lunchtime today',
)

# Rest Framework Config
REST_FRAMEWORK = {
    # Use hyperlinked styles by default.
    # Only used if the `serializer_class` attribute is not set on a view.
    'DEFAULT_MODEL_SERIALIZER_CLASS':
        'rest_framework.serializers.HyperlinkedModelSerializer',

    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ),
    'PAGINATE_BY': 10
}
