from argparse import Action
import json
from multiprocessing import Condition
from typing import Tuple
from django.core.exceptions import ObjectDoesNotExist
from django.http.response import HttpResponse
from pydantic import conset
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.renderers import JSONRenderer
from api.v1.projects.functions import getProject, getTask
from main.functions import  GetUsername, createUser, get_today, getBaseUrl, send_mail_user_invitation, set_Notification, set_activityLog, set_errorLog
from task_tables.models import ActivityLog, Comments, Documents, ErrorLog, Members, Notification, Project, Task
from users.functions import get_user
from . import serialization
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, renderer_classes, authentication_classes
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
from rest_framework_simplejwt.authentication import JWTTokenUserAuthentication
import os
from django.conf import settings
from os.path import exists



@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@authentication_classes((JWTTokenUserAuthentication,))
@renderer_classes((JSONRenderer,))
def summary(request):
    today = get_today()
    data = request.data
    UserID = request.user.id
    UpcomingFilter = data["UpcomingFilter"]
    status_message = status.HTTP_200_OK
    
    progress_dict = {
        "ToDo": 0,
        "InProgress": 0,
        "Completed": 0,
        "Low": 0,
        "Medium": 0,
        "High": 0,
    }
    
    UpComingTasks = []
    RecentActivities = []
    
    if Task.objects.filter(Assignee=UserID, is_deleted=False).exists():
        tasks = Task.objects.filter(
            Assignee=UserID, is_deleted=False).order_by("-DueDate")
        ToDo = tasks.filter(Status="todo").count()
        InProgress = tasks.filter(Status="progress").count()
        Completed = tasks.filter(Status="completed").count()
        Low = tasks.filter(Priority="low").count()
        Medium = tasks.filter(Priority="medium").count()
        High = tasks.filter(Priority="high").count()
        progress_dict = {
            "ToDo": ToDo,
            "InProgress": InProgress,
            "Completed": Completed,
            "Low": Low,
            "Medium": Medium,
            "High": High,
        }
        priorities = ["low", "medium", "high"]
        if UpcomingFilter:
          priorities = [UpcomingFilter]
        upcomingtasks = tasks.filter(DueDate__gt=today, Priority__in=priorities)
        for u in upcomingtasks:
            DueDate = u.DueDate
            TaskName = u.Title
            ProjectName = ""
            if u.TaskProject:
                ProjectName = u.TaskProject.ProjectName
            Priority = u.Priority
            day = DueDate.day
            month = DueDate.strftime("%B")
            year = DueDate.year
            UpComingTasks.append({
                "DueDate": DueDate,
                "TaskName": TaskName,
                "ProjectName": ProjectName,
                "Priority": Priority,
                "day": day,
                "month": month,
                "year": year,
            })
    
    projects = []
    if Members.objects.filter(MemberUserID=UserID, is_ActiveMember=True, MemberType__in=["admin","owner"],is_deleted=False).exists():
       projects = Members.objects.filter(MemberUserID=UserID, is_ActiveMember=True, MemberType__in=[
                                         "admin", "owner"], is_deleted=False).values_list("MemberProject",flat=True)
    if ActivityLog.objects.filter(is_deleted=False, ProjectID__in=projects).exists():
        activities = ActivityLog.objects.filter(
            is_deleted=False, ProjectID__in=projects).order_by("-CreatedDate")
        
        for a in activities:
            Description = a.Description
            ProjectName = a.ProjectID.ProjectName
            TaskName = ""
            if a.TaskID:
                TaskName = a.TaskID.Title
            date = a.CreatedDate
            day = date.day
            month = date.strftime("%B")
            year = date.year
            date = str(day)+ " " + str(month) + " " + str(year)
            RecentActivities.append({
                "Description": Description,
                "ProjectName": ProjectName,
                "TaskName": TaskName,
                "date": date,
            })
            
    if not User.objects.filter(id=UserID).exists():
        token = request.META.get('HTTP_AUTHORIZATION')
        createUser(token, UserID)
    
    response_data = {
        "StatusCode": 6000,
        "progress_dict": progress_dict,
        "UpComingTasks": UpComingTasks,
        "RecentActivities": RecentActivities,
    }

    return Response(response_data, status=status_message)


@api_view(["POST"])
@permission_classes((IsAuthenticated,))
@authentication_classes((JWTTokenUserAuthentication,))
@renderer_classes((JSONRenderer,))
def send_mail(request):
    MemberList = request.data['MemberList']
    invited_mails = request.data['invited_mails']
    send_mail_user_invitation(MemberList, invited_mails)
    response_data = {"StatusCode": 6000}
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes((IsAuthenticated,))
@authentication_classes((JWTTokenUserAuthentication,))
@renderer_classes((JSONRenderer,))
def view_notification(request):
    UserID = request.data['UserID']
    try:
        ProjectID = request.data['ProjectID']
    except:
        ProjectID = None
    try:
        TaskID = request.data['TaskID']
    except:
        TaskID = None
    name = request.data['name']
    project = getProject(ProjectID)
    task = getTask(TaskID)
    set_Notification(UserID, project, task, name, "update")
    response_data = {"StatusCode": 6000}
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes((IsAuthenticated,))
@authentication_classes((JWTTokenUserAuthentication,))
@renderer_classes((JSONRenderer,))
def check_notification(request):
    try:
        UserID = request.user.id
    except:
        UserID = request.data['UserID']
    
    project_notify = 0
    task_notify = 0
    if Notification.objects.filter(UserID=UserID, is_view=False, ProjectID__isnull=False).exists():
        project_notify = Notification.objects.filter(
            UserID=UserID, is_view=False, ProjectID__isnull=False).count()
    if Notification.objects.filter(UserID=UserID, is_view=False, TaskID__isnull=False).exists():
        task_notify = Notification.objects.filter(
            UserID=UserID, is_view=False, TaskID__isnull=False).count()
        
    response_data = {"StatusCode": 6000,
                     "project_notify": project_notify, "task_notify": task_notify}
    return Response(response_data, status=status.HTTP_200_OK)

