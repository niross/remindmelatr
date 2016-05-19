import os
import sys
sys.stdout = sys.stderr

import djcelery
djcelery.setup_loader()

# put the Django project on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

os.environ["DJANGO_SETTINGS_MODULE"] = "settings.production"

# Secret settings - TODO: These need to be updated before going live
os.environ["DJANGO_SETTINGS_MODULE"] = "settings.production"
os.environ["DATABASE_URL"] = "postgres://"
os.environ["FROM_EMAIL"] = "test@test.com"
os.environ["AWS_ACCESS_KEY_ID"] = "1234567890"
os.environ["AWS_SECRET_ACCESS_KEY"] = "ABCDEFGHIJKL"
os.environ["DJANGO_SECRET_KEY"] = "LKJIHGFEDCBA"

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

