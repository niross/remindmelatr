from datetime import datetime

import pytz

from django.http import HttpResponse
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import (api_view, permission_classes)
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer

from allauth.account.utils import send_email_confirmation

from reminders.models import Reminder
from accounts.models import LocalUser
from timezones.models import Timezone
from .serializers import (
    ReminderSerializer, UserSerializer,
    QuickReminderSerializer, ReminderSnoozeSerializer,
    ReminderEditSerializer, UserRegisterSerializer
)


class JSONResponse(HttpResponse):
    """
    An HttpResponse that renders its content into JSON.
    """
    def __init__(self, data, **kwargs):
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)


@api_view(['GET', 'POST'])
def reminder_list(request, status_name=None):
    """
    List all reminders
    Available statuses:
        overdue
        outstanding
        paused
        completed
        deleted
    """
    updated_after = request.GET.get('since', None)

    if request.method == 'GET':
        reminders = Reminder.objects.filter(user=request.user)
        if status_name is not None:
            if status_name == 'overdue':
                reminders = Reminder.objects.overdue(user=request.user)
            elif status_name == 'outstanding':
                reminders = Reminder.objects.overdue(user=request.user)
            elif status_name == 'paused':
                reminders = Reminder.objects.paused(user=request.user)
            elif status_name == 'completed':
                reminders = Reminder.objects.completed(user=request.user)
            else:
                reminders  = Reminder.objects.none()

        if updated_after is not None:
            try:
                updated_after = datetime.strptime(updated_after,
                                                  '%Y-%m-%d %H:%M:%S')
                reminders = reminders.filter(modified__gt=updated_after)
            except ValueError:
                pass

        serializer = ReminderSerializer(reminders, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        data = request.data
        data['user'] = request.user.id
        serializer = QuickReminderSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JSONResponse(
                serializer.data, status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def reminder_detail(request, pk):
    """
    Retrieve, update or delete a reminder
    """
    try:
        reminder = Reminder.objects.get(pk=pk, user=request.user, deleted=False)
    except Reminder.DoesNotExist:
        return HttpResponse(status=404)

    if request.method == 'GET':
        serializer = ReminderSerializer(reminder)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = ReminderEditSerializer(reminder, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.validated_data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        reminder.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['PUT'])
def reminder_snooze(request, pk):
    """
    Snooze a reminder
    """
    try:
        reminder = Reminder.objects.get(pk=pk, user=request.user, deleted=False)
    except Reminder.DoesNotExist:
        return HttpResponse(status=404)

    serializer = ReminderSnoozeSerializer(reminder, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
def reminder_pause(request, pk):
    """
    Pause a reminder
    """
    try:
        reminder = Reminder.objects.get(pk=pk, user=request.user, deleted=False)
    except Reminder.DoesNotExist:
        return HttpResponse(status=404)

    reminder.pause()
    serializer = ReminderSerializer(reminder)
    return Response(serializer.data)


@api_view(['PUT'])
def reminder_pause(request, pk):
    """
    Pause a reminder
    """
    try:
        reminder = Reminder.objects.get(pk=pk, user=request.user, deleted=False)
    except Reminder.DoesNotExist:
        return HttpResponse(status=404)

    reminder.pause()
    serializer = ReminderSerializer(reminder)
    return Response(serializer.data)


@api_view(['PUT'])
def reminder_unpause(request, pk):
    """
    Un-pause a reminder
    """
    try:
        reminder = Reminder.objects.get(pk=pk, user=request.user, deleted=False)
    except Reminder.DoesNotExist:
        return HttpResponse(status=404)

    reminder.unpause()
    serializer = ReminderSerializer(reminder)
    return Response(serializer.data)


@api_view(['PUT'])
def reminder_complete(request, pk):
    """
    Complete a
    """
    try:
        reminder = Reminder.objects.get(pk=pk, user=request.user, deleted=False)
    except Reminder.DoesNotExist:
        return HttpResponse(status=404)

    reminder.complete()
    serializer = ReminderSerializer(reminder)
    return Response(serializer.data)


@api_view(['PUT'])
def reminder_delete(request, pk):
    """
    Delete a reminder
    """
    try:
        reminder = Reminder.objects.get(pk=pk, user=request.user, deleted=False)
    except Reminder.DoesNotExist:
        return HttpResponse(status=404)

    reminder.soft_delete()
    serializer = ReminderSerializer(reminder)
    return Response(serializer.data)


@api_view(['GET'])
def new_reminders(request, since):
    """
    Return any reminders that have become overdue since 'since'
    """
    usertz = pytz.timezone(timezone.get_current_timezone_name())
    since = usertz.localize(datetime.strptime(since, '%Y-%m-%d %H:%M:%S'))
    reminders = Reminder.objects.filter(user=request.user, deleted=False,
                                        desktop_notification_sent=False,
                                        status=4, full_start_datetime__gte=since)
    serializer = ReminderSerializer(reminders, many=True)
    response = Response(serializer.data)
    reminders.update(desktop_notification_sent=True)
    return response


@api_view(['GET'])
def user(request):
    """
    View a single user
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes(())
def register(request):
    """
    Create a single user
    """
    data = request.data
    serializer = UserRegisterSerializer(data=data)
    if serializer.is_valid():
        timezone = Timezone.objects.get(
            name=serializer.validated_data['timezone_name']
        )
        user = LocalUser.objects.create_user(
            username=serializer.validated_data['email'],
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password'],
            timezone=timezone
        )
        send_email_confirmation(request._request, user, signup=True)
        return Response(
            UserSerializer(instance=user).data,
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Override rest_frameworks auth token mechanism so we can return more data
class CustomObtainAuthToken(ObtainAuthToken):
    serializer_class = AuthTokenSerializer
    model = Token

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'email': token.user.email,
                'token': token.key,
                'timezone': token.user.timezone.name,
            })
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

custom_obtain_auth_token = CustomObtainAuthToken.as_view()
