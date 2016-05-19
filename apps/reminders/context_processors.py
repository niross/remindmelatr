from .forms import BasicReminderForm


def new_reminder(request):
    form = BasicReminderForm()
    return {
        'new_reminder_form': form,
    }
