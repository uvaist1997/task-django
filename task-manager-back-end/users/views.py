from django.contrib.auth.models import Group, User
from django.utils.translation import gettext_lazy as _
from rest_framework import parsers, renderers, status
from rest_framework.decorators import api_view, permission_classes, renderer_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTTokenUserAuthentication
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from task_tables.models import InvitedUsers, Members


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@authentication_classes((JWTTokenUserAuthentication,))
@renderer_classes((JSONRenderer,))
def create_user(request):
    data = request.data
    user = None
    if data and not User.objects.filter(username=data['username'], email=data['email']).exists():
        user = User.objects.create_user(
            id=data['id'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            username=data['username'],
            password=data['password'],
            is_superuser=False,
            last_login=data['last_login']
        )
    else:
        if User.objects.filter(email=data['email']).exists():
            user = User.objects.get(email=data['email'])
    if InvitedUsers.objects.filter(Email=data['email']).exists() and user:
        invited_ins = InvitedUsers.objects.filter(Email=data['email'])
        for i in invited_ins:
            project_ins = i.MemberProject
            Members.objects.create(
                MemberUserID=user.id,
                MemberProject=project_ins,
                MemberType="member",
                CreatedUserID=i.CreatedUserID
            )
            i.delete()
   
    response_data = {
        "message": "success",
    }
    return Response(response_data, status=status.HTTP_200_OK)
