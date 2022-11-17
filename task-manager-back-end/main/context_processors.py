from django.shortcuts import render, get_object_or_404
import datetime




def main_context(request):

    user = request.user
    is_superuser = False
    username = None

    if user.is_authenticated:
        username = user.username
        if user.is_superuser:
            is_superuser = True
        else:
            is_superuser = False
    return {
        "is_superuser": is_superuser,
        "username": username,
    }
