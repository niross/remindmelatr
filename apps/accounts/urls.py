from django.conf.urls import patterns, url

urlpatterns = patterns(
    'accounts.views',
    url(r'^settings/$', 'settings', name='settings'),
    url(r'^update_setting/$', 'update_setting', name='update_setting'),
)
