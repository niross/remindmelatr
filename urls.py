from django.conf import settings
from django.conf.urls import patterns, url, include
from django.contrib import admin
from django.views.generic import TemplateView
admin.autodiscover()

# Custom 404 page
handler500 = 'apps.website.views.custom_500'

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls), name='admin'),
    url(r'^robots\.txt$', TemplateView.as_view(template_name='robots.txt')),

    url(r'', include('website.urls')),
    url(r'^app/', include('allauth.urls')),
    url(r'^app/', include('reminders.urls')),
    url(r'^app/', include('accounts.urls')),
    url(r'^app/contact/', include('contact.urls')),
    url(r'^api/', include('api.urls')),
)

if settings.DEBUG:
    urlpatterns = patterns('',
        url(r'static/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.STATIC_ROOT, 'show_indexes': True
        }),
        url(r'^uploads/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT, 'show_indexes': True
        }),
        url(r'', include('django.contrib.staticfiles.urls')),
    ) + urlpatterns
