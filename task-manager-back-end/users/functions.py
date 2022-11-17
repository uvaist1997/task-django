from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404


def get_user(id):
    if User.objects.filter(id=id).exists():
        UserID = get_object_or_404(User.objects.filter(id=id))
    else:
        UserID = "User Not Found"
    return UserID
