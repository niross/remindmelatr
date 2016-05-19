from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.core import serializers

from accounts.models import LocalUser

CONTENT_TYPE = 'application/json; charset=utf8'

@login_required
def list_users(request):
    term = request.GET.get('term', '')
    limit = request.GET.get('limit', 10)
    users = LocalUser.objects.filter(is_active=True, deleted=False)
    if term is not None:
        users = users.filter(username__icontains=term)
    response = serializers.serialize('json', users[:limit])
    return HttpResponse(response, content_type=CONTENT_TYPE)
