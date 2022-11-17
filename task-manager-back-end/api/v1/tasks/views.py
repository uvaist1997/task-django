import json
from multiprocessing import Condition

from django.core.exceptions import ObjectDoesNotExist
from django.http.response import HttpResponse
from pydantic import conset
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.renderers import JSONRenderer
from api.v1.projects.functions import getProject
from main.functions import  GetUsername, get_today, set_Notification, set_activityLog, set_errorLog
from task_tables.models import ActivityLog, Documents, ErrorLog, Members, Notification, Project, SubTask,Task
from users.functions import get_user
from api.v1.tasks.serialization import TaskSerializer
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


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@authentication_classes((JWTTokenUserAuthentication,))
@renderer_classes((JSONRenderer,))
def create_task(request):
    today = get_today()
    try:
        with transaction.atomic():
            data = request.data
            CreateatedUserID = request.user.id
            TaskName = data["TaskName"]
            Description = data["Description"]
            Status = data["Status"]
            TaskConfermation = data["TaskConfermation"]
            ProjectID = data["ProjectID"]
            ReportUserID = data["ReportUserID"]
            if not ReportUserID:
                ReportUserID = None
            AssignerID = data["AssignerID"]
            AssigneeName = data["AssigneeName"]

            Priority = data["Priority"]
            DueDate = data["DueDate"]
            DocumentList = data["DocumentList"]
            UserName = data["CreatedBy"]
            SubTaskList = data["SubTaskList"]
            # Assignee = data["Assignee"]
            SubTaskList = json.loads(SubTaskList)
            if not AssignerID:
                AssignerID = CreateatedUserID
            status_message = status.HTTP_200_OK
            project_instance = None
            ProjectName = None
            if ProjectID:
                if Project.objects.filter(pk=ProjectID):
                    project_instance = Project.objects.get(pk=ProjectID)
                    ProjectName = project_instance.ProjectName
            

            if TaskConfermation == "true":
                TaskConfermation = True
            elif TaskConfermation == "false":
                TaskConfermation = False
            else:
                TaskConfermation = False

            task_instance = Task.objects.create(
                Title=TaskName,
                Description=Description,
                Status=Status,
                TaskConfermation=TaskConfermation,
                Reporter=ReportUserID,
                Assignee=AssignerID,
                TaskProject=project_instance,
                Priority=Priority,
                DueDate=DueDate,
                CreatedUserID=CreateatedUserID,
            )
            activity_description = f"{UserName} Created Task {TaskName} To {AssigneeName}"
            set_activityLog(CreateatedUserID, None, task_instance,
                            activity_description)
            
            if not AssignerID == CreateatedUserID:
                set_Notification(
                    AssignerID, None, task_instance, "task", "create")
            
            # Creating Attachment
            DocFiles = request.FILES
            if DocFiles:
                for d in DocFiles:
                    d = DocFiles[d]
                    Documents.objects.create(
                        TaskID=task_instance,
                        DocFile=d,
                        CreatedUserID=CreateatedUserID
                    )

            # Creating SubTask
            if SubTaskList:
                for task in SubTaskList:
                    SubTask.objects.create(
                        MainTask=task_instance,
                        Description=task["Description"],
                        is_completed=task["is_completed"],
                        CreatedUserID=CreateatedUserID
                    )
                    activity_description = f"{UserName} Created Sub Task {TaskName}"
                    set_activityLog(CreateatedUserID, None, task_instance,
                                    activity_description)
            
            response_data = {
                "StatusCode": 6000,
                "message": "successfully Created"
            }
            return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        err_descrb = str(exc_type) + str(fname) + str(exc_tb.tb_lineno)
        response_data = {
            "StatusCode": 6001,
            "message": "some error occured..please try again",
            "err_descrb": err_descrb
        }
        body_params = str(request.data)
        error_id = set_errorLog(
            CreateatedUserID, "error", "create Project", body_params, err_descrb)
        return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@authentication_classes((JWTTokenUserAuthentication,))
@renderer_classes((JSONRenderer,))
def edit_task(request,pk):
    today = get_today()
    try:
        with transaction.atomic():
            task_instance = Task.objects.get(pk=pk)
            data = request.data
            CreateatedUserID = request.user.id
            TaskName = data["TaskName"]
            Description = data["Description"]
            Status = data["Status"]
            TaskConfermation = data["TaskConfermation"]
            ProjectID = data["ProjectID"]
            ReportUserID = data["ReportUserID"]
            if not ReportUserID or ReportUserID == "null":
                ReportUserID = None
            ReporterName = data["ReporterName"]
            AssignerID = data["AssignerID"]
            AssigneeName = data["AssigneeName"]
            if not AssignerID:
                AssignerID = CreateatedUserID
                
            Priority = data["Priority"]
            DueDate = data["DueDate"]
            UserName = data["CreatedBy"]
            SubTaskList = data["SubTaskList"]
            SubTaskList = json.loads(SubTaskList)
            status_message = status.HTTP_200_OK
            project_instance = None
            ProjectName = None

            if ProjectID and not ProjectID == "null":
                if Project.objects.filter(pk=ProjectID):
                    project_instance = Project.objects.get(pk=ProjectID)
                    ProjectName = project_instance.ProjectName
            
            if TaskConfermation == "true":
                TaskConfermation = True
            elif TaskConfermation == "false":
                TaskConfermation = False
            else:
                TaskConfermation = False

            # Add Changes To ActivityLog
            if task_instance.Title != TaskName:
                activity_description = f"{UserName} Updated Task Name from {task_instance.TaskProject} to {ProjectName}"
                set_activityLog(CreateatedUserID, None, task_instance,
                                activity_description)
            if task_instance.Description != Description:
                activity_description = f"{UserName} Updated Project Description"
                set_activityLog(CreateatedUserID, None, task_instance,
                                activity_description)
            if task_instance.Status != Status:
                activity_description = f"{UserName} Changed Status to {Status}"
                set_activityLog(CreateatedUserID, None, task_instance,
                                activity_description)
            if task_instance.Priority != Priority:
                activity_description = f"{UserName} Changed Priority to {Priority}"
                set_activityLog(CreateatedUserID, None, task_instance,
                                activity_description)
            if task_instance.DueDate != DueDate:
                activity_description = f"{UserName} Changed DueDate to {DueDate}"
                set_activityLog(CreateatedUserID, None, task_instance,
                                activity_description)
            if task_instance.TaskConfermation != TaskConfermation:
                activity_description = f"{UserName} Changed Task Confermation to {TaskConfermation}"
                set_activityLog(CreateatedUserID, None, task_instance,
                                activity_description)
            if task_instance.TaskProject != project_instance:
                from_ProjectName = ""
                to_ProjectName = ""
                if task_instance.TaskProject:
                    from_ProjectName = task_instance.TaskProject.ProjectName
                if project_instance:
                    to_ProjectName = project_instance.ProjectName
                activity_description = f"{UserName} Changed Project `{from_ProjectName}` to {to_ProjectName}"
                set_activityLog(CreateatedUserID, None, task_instance,
                                activity_description)
            if task_instance.Reporter != ReportUserID:
                activity_description = f"{UserName} Changed Reporter `{GetUsername(ReportUserID,request)}` to {ReporterName}"
                set_activityLog(CreateatedUserID, None, task_instance,
                                activity_description)
            if task_instance.Assignee != AssignerID:
                activity_description = f"{UserName} Changed Assigner `{GetUsername(AssignerID,request)}` to {AssigneeName}"
                set_activityLog(CreateatedUserID, None, task_instance,
                                activity_description)
            Task.objects.filter(pk=pk).update(
                Title=TaskName,
                Description=Description,
                Status=Status,
                TaskConfermation=TaskConfermation,
                Reporter=ReportUserID,
                Assignee=AssignerID,
                TaskProject=project_instance,
                Priority=Priority,
                DueDate=DueDate,
                UpdatedDate=datetime.datetime.now(),
                UpdatedUserID=CreateatedUserID)

            docs_ins = Documents.objects.filter(TaskID=task_instance).delete()
            
            print(docs_ins,"OOOOOOOOOOOOOOOOOOOOOOOOOOOO")
            DocFiles = request.FILES
            print(DocFiles)

            if DocFiles:
                for d in DocFiles:
                    d = DocFiles[d]
                    Documents.objects.create(
                        TaskID=task_instance,
                        DocFile=d,
                        CreatedUserID=CreateatedUserID
                    )
            
            # Creating SubTask
            SubTask.objects.filter(MainTask=task_instance).delete()
            if SubTaskList:
                for task in SubTaskList:
                    SubTask.objects.create(
                        MainTask=task_instance,
                        Description=task["Description"],
                        is_completed=task["is_completed"],
                        CreatedUserID=CreateatedUserID

                    )
            response_data = {
                "StatusCode": 6000,
                "message": "successfully Created"
            }
            return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        err_descrb = str(exc_type) + str(fname) + str(exc_tb.tb_lineno)
        response_data = {
            "StatusCode": 6001,
            "message": "some error occured..please try again",
            "err_descrb": err_descrb
        }
        body_params = str(request.data)
        error_id = set_errorLog(
            request.user.id, "error", "create Project", body_params, err_descrb)
        return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@authentication_classes((JWTTokenUserAuthentication,))
@renderer_classes((JSONRenderer,))
def list_task(request):
    today = get_today()
    data = request.data
    UserID = request.user.id
    ProjectFilter = data["ProjectFilter"]
    FilterType = data["FilterType"]
    FilterValue = data["FilterValue"]
    FilterStartDate = data["FilterStartDate"]
    FilterEndDate = data["FilterEndDate"]
    ProjectID = data["ProjectID"]
    try:
        TaskConfermation = data["TaskConfermation"]
    except:
        TaskConfermation = False
    try:
        is_load = data["is_load"]
    except:
        is_load = False
    status_message = status.HTTP_200_OK
    statuses = ["todo", "progress", "completed", "confirming"]
    if TaskConfermation == True:
        statuses = ["confirming"]
    condition1 = (Q(is_deleted=False, Status__in=statuses))
    condition2 = (Q(Assignee=UserID))
    # condition2 = (Q(CreatedUserID=UserID) |
    #               Q(Assignee=UserID))
    if FilterType == 0:
        condition2 = (Q(Assignee=UserID))
    elif FilterType == 1 and FilterValue:
        condition2 = (Q(TaskProject__id=FilterValue))
    elif FilterType == 2 and FilterValue and ProjectID:
        condition2 = (Q(Assignee=FilterValue, TaskProject__id=ProjectID))
    task_instaces = Task.objects.filter(
        condition1 & condition2).order_by("-CreatedDate")
    if is_load == True and not ProjectFilter:
        task_instaces = task_instaces.filter().exclude(Status="completed")
    
    if ProjectFilter:
        statuses = ['todo', 'progress', 'completed']
        if TaskConfermation == True:
            statuses.append("confirming")
            ProjectFilter.append("confirming")
        priorities = ['low', 'medium', 'high']
        statuses_as_set = set(statuses)
        intersection_status = statuses_as_set.intersection(ProjectFilter)
        intersection_status_as_list = list(intersection_status)
        pririties_as_set = set(priorities)
        intersection_priority = pririties_as_set.intersection(
            ProjectFilter)
        intersection_priority_as_list = list(intersection_priority)
        task_instaces = task_instaces.filter(
            DueDate__gte=FilterStartDate, DueDate__lte=FilterEndDate)
        if intersection_status_as_list:
            statuses = intersection_status_as_list
            task_instaces = task_instaces.filter(Status__in=statuses)
        else:
            statuses = []
        if intersection_priority_as_list:
            priorities = intersection_priority_as_list
            task_instaces = task_instaces.filter(Priority__in=priorities)
        else:
            priorities = []
        
        if not statuses and not priorities:
            task_instaces = task_instaces.filter(
                Status__in=statuses, Priority__in=priorities)
        
    
    # if FilterStartDate and FilterEndDate:
    #     task_instaces = task_instaces.filter(
    #         DueDate__gte=FilterStartDate, DueDate__lte=FilterEndDate,)
    # if FilterType == 1 and FilterValue:
    #     project_ins = getProject(FilterValue)
    #     task_instaces = task_instaces.filter(
    #         TaskProject=project_ins)
    if ProjectID and FilterType != 2:
        task_instaces = task_instaces.filter(TaskProject__id=ProjectID)
        
    if ((FilterType == 1 and FilterValue) or ProjectID):
        if ProjectID:
            project = getProject(ProjectID)
        else:
            project = getProject(FilterValue)
        role = Members.objects.filter(
            MemberProject=project, MemberUserID=UserID).first().MemberType
        if role == "member":
            task_instaces = task_instaces.filter(Assignee=UserID)
    
    if task_instaces.exists():
        serialzed = TaskSerializer(
            task_instaces, many=True, context={"UserID": UserID, "request": request})
        project_notify = 0
        task_notify = 0
        if Notification.objects.filter(UserID=UserID, is_view=False, ProjectID__isnull=False).exists():
            project_notify = Notification.objects.filter(
                UserID=UserID, is_view=False, ProjectID__isnull=False).count()
        if Notification.objects.filter(UserID=UserID, is_view=False, TaskID__isnull=False).exists():
            task_notify = Notification.objects.filter(
                UserID=UserID, is_view=False, TaskID__isnull=False).count()
        
        response_data = {
            "StatusCode": 6000,
            "data": serialzed.data,
            "project_notify": project_notify,
            "task_notify": task_notify,
        }
    else:
        ProjectName = ""
        project = None
        if ProjectID:
            project = getProject(ProjectID)
            ProjectName = project.ProjectName
        if FilterType == 1 and FilterValue:
            project = getProject(FilterValue)
            ProjectName = project.ProjectName
        
        response_data = {
            "StatusCode": 6001,
            "message": "Task is Not Exists",
            "ProjectName": ProjectName,
        }

    return Response(response_data, status=status_message)



@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@authentication_classes((JWTTokenUserAuthentication,))
@renderer_classes((JSONRenderer,))
def single_task(request,pk):
    today = get_today()
    data = request.data
    UserID = request.user.id
    status_message = status.HTTP_200_OK
    task_instaces = Task.objects.filter(
            is_deleted=False)
    if task_instaces.exists():
        instance = Task.objects.get(pk=pk,
            is_deleted=False)
        serialzed = TaskSerializer(
            instance, context={"UserID": UserID, "request": request})
        response_data = {
            "StatusCode": 6000,
            "data": serialzed.data
        }
    else:
        response_data = {
            "StatusCode": 6001,
            "message": "Task is Not Exists"
        }

    return Response(response_data, status=status_message)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@authentication_classes((JWTTokenUserAuthentication,))
@renderer_classes((JSONRenderer,))
def update_status_priority(request,pk):
    today = get_today()
    data = request.data
    UserID = request.user.id
    value = data["value"]
    task_type = data["task_type"]
    status_message = status.HTTP_200_OK
    print(value,task_type)
    try:
        UserName = data["UserName"]
    except:
        UserName = ""
    if Task.objects.filter(pk=pk).exists() and task_type:
        if task_type == "Status":
            Task.objects.filter(pk=pk).update(Status=value)
        elif task_type == "Priority":
            Task.objects.filter(pk=pk).update(Priority=value)
        instaces = Task.objects.get(pk=pk)
        ProjectID = None
        if instaces.TaskProject:
            ProjectID = instaces.TaskProject
        activity_description = f"{UserName} Changed {task_type} to {value}"
        set_activityLog(UserID, ProjectID, instaces,
                        activity_description)
        response_data = {
            "StatusCode": 6000
        }
    else:
        response_data = {
            "StatusCode": 6001,
            "message": "No Project with this ID"
        }

    return Response(response_data, status=status_message)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@authentication_classes((JWTTokenUserAuthentication,))
@renderer_classes((JSONRenderer,))
def delete_task(request,pk):
    status_message = status.HTTP_200_OK
    UserName = request.data["UserName"]
    if Task.objects.filter(pk=pk).exists():
        Task.objects.filter(pk=pk).update(is_deleted=True)
        instance = Task.objects.get(pk=pk)
        activity_description = f"{UserName} deleted Task {instance.Title}"
        set_activityLog(request.user.id,None, instance,
                        activity_description)
        response_data = {
            "StatusCode": 6000
        }
    else:
        response_data = {
            "StatusCode": 6001,
            "message": "Task Deleted"
        }

    return Response(response_data, status=status_message)