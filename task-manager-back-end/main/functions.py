from datetime import timedelta
import json
import random
import math
from typing import Type
from django.core.paginator import Paginator , EmptyPage, PageNotAnInteger
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives, EmailMessage, send_mail
import requests
from task_tables.models import ActivityLog, ErrorLog, Notification

def get_pagination_instance(request, instances):
    paginator = Paginator(instances, 20)
    page = request.GET.get('page')
    try:
        instances = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        instances = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        instances = paginator.page(paginator.num_pages)
    # pagination ends here
    return instances


def set_errorLog(UserID, error_type, action, body_params, Description):
    instance = ErrorLog.objects.create(
        UserID=UserID,
        Description=Description,
        error_type=error_type,
        action=action,
        body_params=body_params,
    )
    return instance.id


def converted_float(Val):
    try:
        result = float(Val)
    except:
        result = 0
    return result


def converted_to_datetime_object(date_string):
    # date_string = "2022-04-06 16:12:21"
    from datetime import datetime
    datetime_object = datetime.strptime(
        date_string, '%Y-%m-%d %H:%M:%S')
    return datetime_object


def converted_to_date_object(date_string):
    # date_string = "2022-03-29 11:19:51"
    from datetime import datetime
    datetime_object = datetime.strptime(
        date_string, '%Y-%m-%d')
    return datetime_object

def get_today():
    import datetime
    today = datetime.datetime.now()
    return today


def set_activityLog(UserID,ProjectID,TaskID,Description):
    print(ProjectID)
    instance = ActivityLog.objects.create(
        UserID=UserID,
        ProjectID=ProjectID,
        TaskID=TaskID,
        Description=Description
    )
    return ""


def set_Notification(UserID, ProjectID, TaskID,name,type):
    if type == "create":
        instance = Notification.objects.create(
            UserID=UserID,
            ProjectID=ProjectID,
            TaskID=TaskID,
            is_view=False
        )
    else:
        if name == "project":
            if Notification.objects.filter(UserID=UserID, ProjectID=ProjectID).exists():
                instance = Notification.objects.filter(
                    UserID=UserID, ProjectID=ProjectID).update(is_view=True)
        elif name == "task":
            if Notification.objects.filter(UserID=UserID, TaskID=TaskID).exists():
                instance = Notification.objects.filter(
                    UserID=UserID, TaskID=TaskID).update(is_view=True)
        
    return ""


def GetUsername(UserID, request):
    username = ""
    if User.objects.filter(id=UserID).exists():
        username = User.objects.get(id=UserID).username
    else:
        token = request.META.get('HTTP_AUTHORIZATION')
        username = createUser(token, UserID)
    return username


# def GetUsername(UserID, request):
#     token = request.META.get('HTTP_AUTHORIZATION')
#     headers = {
#         'Content-Type': 'application/json',
#         'Authorization': token
#     }
#     data = {"UserID":  UserID}
#     web_host = "http://localhost:8000"
#     # web_host = "https://api.accounts.vikncodes.in"

#     request_url = web_host + "/api/v1/users/get-username/"
#     response = requests.post(
#         request_url, headers=headers, data=json.dumps(data))
#     data = response.json()
#     username = ""
#     if data["StatusCode"] == 6000:
#         username = data["username"]
#     return username


def getBaseUrl(type="baseUrl"):
    if type == "baseUrl":
        # Url = "http://localhost:8000/"
        # Url = "https://api.accounts.vikncodes.in/"
        Url = "https://api.accounts.vikncodes.com/"
    elif type == "vertionURl":
        # Url = "http://localhost:8000/api/v1/"
        # Url = "https://api.accounts.vikncodes.in/api/v1/"
        Url = "https://api.accounts.vikncodes.com/api/v1/"
    return Url


def createUser(token,UserID):
    if token.split()[0] == "Bearer":
        token = token.split()[1]
    service_header = {
        'Content-Type': 'application/json',
        'Authorization': f"Bearer {token}"
    }
    base_url = getBaseUrl("vertionURl")
    service_url = base_url + "users/create-service/user/"
    service_data = {"service": "task_manager", "UserID": UserID}
    response_service = requests.post(
        service_url, headers=service_header, data=json.dumps(service_data))
    
    response_service = response_service.json()
    print(response_service,UserID)
    data = response_service["service_data"]
    id = data["id"]
    first_name = data["first_name"]
    last_name = data["last_name"]
    email = data["email"]
    username = data["username"]
    password = data["password"]
    last_login = data["last_login"]
    
    if data and not User.objects.filter(username=username, email=email).exists():
        if not last_login:
            last_login = None
        user = User.objects.create_user(
            id=id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            username=username,
            password=password,
            is_superuser=False,
            last_login=last_login
        )
        
    return username


def send_mail_user_invitation(MemberList, invited_mails):
    token = ""
    # domain = "https://viknbooks.com"
    # domain = "https://vikncodes.in"
    domain = "https://accounts.vikncodes.com/"
    # domain = "http://localhost:3000"
    site_name = "task.vikncodes.com"
    if MemberList:
        reset_password_url = f"{domain}sign-in?service=task_manager"
        context = {
            "domain": domain,
            "site_name": site_name,
            "reset_password_url": reset_password_url,
        }

        email_html_message = render_to_string(
            "email/user_invitation.html", context)
        subject = "User Invitation for {title}".format(title=site_name)

        msg = EmailMultiAlternatives(
            # title:
            "Email Verification",
            # message:
            subject,
            # from:
            "noreply@somehost.local",
            # to:
            MemberList,
        )
        msg.attach_alternative(email_html_message, "text/html")
        msg.send()
    if invited_mails:
        reset_password_url = f"{domain}sign-up?service=task_manager"
        
        context = {
            "domain": domain,
            "site_name": site_name,
            "reset_password_url": reset_password_url,
        }

        email_html_message = render_to_string(
            "email/user_invitation.html", context)
        subject = "User Invitation for {title}".format(title=site_name)

        msg = EmailMultiAlternatives(
            # title:
            "Email Verification",
            # message:
            subject,
            # from:
            "noreply@somehost.local",
            # to:
            invited_mails,
        )
        msg.attach_alternative(email_html_message, "text/html")
        msg.send()
