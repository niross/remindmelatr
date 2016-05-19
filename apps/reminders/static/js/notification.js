var Notification = window.Notification || window.mozNotification || window.webkitNotification;
$(document).ready(function() {
    enableNotifications();

    // Hack because of chrome bug that requires user
    // interaction to enable desktop notifications
    window.addEventListener('click', function () {
       enableNotifications();
    });
});

function formatDate(d) {
    var date = d.getFullYear() + '-' + (d.getMonth()+1) + '-' + d.getDate();
    var time = d.getHours() + ':' + d.getMinutes() + ':00';
    return date + ' ' + time;
}

function enableNotifications() {
    var last_check = new Date();
    if (Notification && Notification.permission === 'granted') {
        notifier(last_check);
    }
    else if (Notification && Notification.permission !== 'denied') {
        Notification.requestPermission(function(permission) {
            // This allows us to use Notification.permission with Chrome/Safari
            if (Notification.permission !== permission) {
                Notification.permission = permission;
            }
            if (permission == 'granted') {
                notifier(last_check);
            }
        });
    }
}

function notifier(last_check) {
    setTimeout(function() {
        $.ajax({
            url: '/api/new_reminders/' + formatDate(last_check) + '/',
            success: function(response) {
                last_check = new Date();
                $(response).each(function(index, reminder) {
                    var instance = new Notification(
                        'New Reminder from Remind Me Latr', {
                            body: reminder.short_content,
                            icon: 'https://remindmelatr.com/static/images/remindmelatr-notification-icon-32x32.png',

                        }
                    );
                    console.debug(instance);
                    instance.onclick = function () {
                        window.open(reminder.url);
                        instance.close();
                    };
                });
            },
            complete: function() {
                notifier(last_check);
            },
            timeout: 10000
        })
    }, 20000);
}
