from django.conf.urls import patterns, url, include


urlpatterns = patterns('api.views',
    url(r'^auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^reminders/(?P<pk>[0-9]+)/$',
        'reminder_detail', name='reminder_detail'),
    url(r'^reminders/(?P<pk>[0-9]+)/snooze$',
        'reminder_snooze', name='reminder_snooze'),
    url(r'^reminders/(?P<pk>[0-9]+)/pause$',
        'reminder_pause', name='reminder_pause'),
    url(r'^reminders/(?P<pk>[0-9]+)/unpause$',
        'reminder_unpause', name='reminder_unpause'),
    url(r'^reminders/(?P<pk>[0-9]+)/complete$',
        'reminder_complete', name='reminder_complete'),
    url(r'^reminders/(?P<pk>[0-9]+)/delete$',
        'reminder_delete', name='reminder_delete'),
    url(r'^reminders/$', 'reminder_list', name='reminder_list'),
    url(r'^reminders/(?P<status_name>.+?)/$',
        'reminder_list', name='reminder_list'),

    url(r'^new_reminders/(?P<since>.+?)/$',
        'new_reminders', name='new_reminders'),
    url(r'^user/$', 'user', name='user'),
    url(r'^user/register/$', 'register', name='register'),
    url(
        r'^custom-token-auth/',
        'custom_obtain_auth_token',
        name='custom-token-auth'
    ),
)

urlpatterns += patterns('',
    url(
        r'^token-auth/',
        'rest_framework.authtoken.views.obtain_auth_token',
        name='token-auth'
    ),
)
