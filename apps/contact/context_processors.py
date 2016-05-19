from .forms import ContactForm


def contact_form(request):
    return {
        'contact_form': ContactForm(initial={'user': request.user})
    }
