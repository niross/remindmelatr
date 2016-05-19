from django.conf.urls import patterns, url

urlpatterns = patterns(
    'reminders.views',
    url(r'^on_options/$', 'on_options', name='on_options'),
    url(r'^at_options/$', 'at_options', name='at_options'),

    url(r'^dashboard/$', 'dashboard', name='dashboard'),

    url(r'^new/$', 'new', name='new'),
    url(r'^reminders/$', 'reminders', name='reminders'),

    url(r'^reminders/overdue/$', 'overdue', name='overdue'),
    url(r'^reminders/upcoming/$', 'upcoming', name='upcoming'),
    url(r'^reminders/paused/$', 'paused', name='paused'),
    url(r'^reminders/completed/$', 'completed', name='completed'),

    url(r'^reminder/(?P<reminder_id>\d+)/$', 'reminder', name='reminder'),
    url(r'^edit/(?P<reminder_id>\d+)/$', 'edit', name='edit'),
    url(r'^delete/(?P<reminder_id>\d+)/$', 'delete', name='delete'),
    url(
        r'^confirm_delete/(?P<reminder_id>\d+)/$',
        'confirm_delete',
        name='confirm_delete'
    ),
    url(r'^snooze/(?P<reminder_id>\d+)/$', 'snooze', name='snooze'),
    url(r'^pause/(?P<reminder_id>\d+)/$', 'pause', name='pause'),
    url(r'^unpause/(?P<reminder_id>\d+)/$', 'unpause', name='unpause'),
    url(r'^complete/(?P<reminder_id>\d+)/$', 'complete', name='complete'),
    url(
        r'^confirm_complete/(?P<reminder_id>\d+)/$',
        'confirm_complete',
        name='confirm_complete'
    ),

    # Multiple actions
    url(
        r'^delete_multiple/$',
        'delete_multiple',
        name='delete_multiple'
    ),
    url(
        r'^complete_multiple/$',
        'complete_multiple',
        name='complete_multiple'
    ),
    url(
        r'^pause_multiple/$',
        'pause_multiple',
        name='pause_multiple'
    ),
    url(
        r'^unpause_multiple/$',
        'unpause_multiple',
        name='unpause_multiple'
    ),

    # External (non logged in) views
    url(
        r'^reminder/(?P<hash_digest>.+?)/snooze/$',
        'snooze_external',
        name='snooze_external'
    ),
    url(
        r'^reminder/(?P<hash_digest>.+?)/complete/$',
        'confirm_complete_external',
        name='confirm_complete_external'
    ),
    url(
        r'^reminder/(?P<hash_digest>.+?)/$',
        'reminder_external',
        name='reminder_external'
    ),
)

