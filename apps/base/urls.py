from django.conf.urls import patterns, url

urlpatterns = patterns(
    'base.views',
    url(r'^list_users/$', 'list_users', name='list_users'),
)
