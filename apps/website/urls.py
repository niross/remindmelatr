from django.conf.urls import patterns, url

urlpatterns = patterns(
    'website.views',
    url(r'^$', 'home', name='home'),
    url(r'^contact/$', 'contact', name='website_contact'),
    url(r'^about/$', 'about', name='about'),
    url(r'^privacy/$', 'privacy', name='privacy'),
    url(r'^terms/$', 'terms', name='terms'),
)

