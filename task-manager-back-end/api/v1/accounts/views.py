import json
from multiprocessing import Condition

from django.core.exceptions import ObjectDoesNotExist
from django.http.response import HttpResponse
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.renderers import JSONRenderer
from users.functions import get_user
from . import serialization
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework import status
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from api.v1.general.functions import generate_serializer_errors
import requests
from django.conf import settings
from rest_framework_jwt.settings import api_settings as jwt_settings
import datetime
from datetime import date, timedelta
import os
from os import path
import sys
from django.utils.encoding import smart_str
from django.http import FileResponse
import mimetypes
from django.db import transaction, IntegrityError
from django.db.models import Max, Prefetch, Q, Sum


@api_view(['GET'])
@permission_classes((AllowAny,))
@renderer_classes((JSONRenderer,))
def accounts(request):
    sid = request.GET.get('sid')
    try:
        action = request.GET.get('action')
    except:
        action = "login"
    # print(request.COOKIES.get('setting-cookie'))
    # response = HttpResponse("")
    response = HttpResponse("Cookie Set")
    two_years = datetime.datetime.now() + datetime.timedelta(days=730)
    if action == "logout":
        two_years = "1970-05-08T09:42:34.445Z"

    # domain = "vikncodes.in"
    domain = None
    response.set_cookie(key='VBID', value=sid, domain=domain,
                        secure=True, expires=two_years)
    # response.set_cookie('VBID', sid)
    return response


