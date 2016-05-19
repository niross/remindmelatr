from django.utils import timezone


class TimezoneMiddleware(object):
    """
    If timezone is provided in the request use it
    """
    def process_request(self, request):
        # TODO - here we can probably check if there is
        # a timezone override cookie as well
        if request.user.is_authenticated \
                and hasattr(request.user, 'timezone') \
                and request.user.timezone is not None:
            user_timezone = request.user.timezone.name
            timezone.activate(user_timezone)
        else:
            timezone.deactivate()
