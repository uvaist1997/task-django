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
from main.functions import  GetUsername, converted_to_date_object, converted_to_datetime_object, createUser, get_today, set_Notification, set_activityLog, set_errorLog
from task_tables.models import ActivityLog, Comments, Documents, ErrorLog, InvitedUsers, Members, Notification, Project
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
from django.core.paginator import Paginator


def call_paginator_all(model_object, page_number, items_per_page):
    paginator = Paginator(model_object, items_per_page)
    content = paginator.page(page_number)
    return content


def list_pagination(list_value, items_per_page, page_no):
    paginator_object = Paginator(list_value, items_per_page)
    get_value = paginator_object.page(page_no).object_list
    return get_value

@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@authentication_classes((JWTTokenUserAuthentication,))
@renderer_classes((JSONRenderer,))
def create_project(request):
    today = get_today()
    try:
        with transaction.atomic():
            data = request.data
            UserID = request.user.id
            try:
                TaskConfermation = data["TaskConfermation"]
                if TaskConfermation == "true":
                    TaskConfermation = True
                else:
                    TaskConfermation = False
            except:
                TaskConfermation = False

            try:
                TrakPerformance = data["TrakPerformance"]
                if TrakPerformance == "true":
                    TrakPerformance = True
                else:
                    TrakPerformance = False
            except:
                TrakPerformance = False

            ProjectName = data["ProjectName"]
            Description = data["Description"]
            Status = data["Status"]
            Priority = data["Priority"]
            DueDate = data["DueDate"]
            ProjectFile = data["ProjectFile"]
            MemberList = data["MemberList"]
            MemberList = data["MemberList"]
            InvitedList = data["InvitedList"]
            UserName = data["CreatedBy"]
            status_message = status.HTTP_200_OK
            if not Project.objects.filter(is_deleted=False, CreatedUserID=UserID, ProjectName__iexact=ProjectName).exists():
                project_instance = Project.objects.create(
                    ProjectName=ProjectName,
                    Description=Description,
                    Status=Status,
                    Priority=Priority,
                    DueDate=DueDate,
                    CreatedUserID=UserID,
                    TrakPerformance=TrakPerformance,
                    TaskConfermation=TaskConfermation,
                )
                activity_description = f"{UserName} Created Project {ProjectName}"
                set_activityLog(UserID, project_instance, None,
                                activity_description)
                if MemberList:
                    ret = request.POST
                    MemberList = json.loads(ret['MemberList'])
                    MemberList.append({
                        "MemberUserID": UserID,
                        "MemberType": "owner",
                        "username": UserName,
                        "progress_rate": 0
                    })
                    print(MemberList)
                    for m in MemberList:
                        Members.objects.create(
                            MemberUserID=m["MemberUserID"],
                            MemberProject=project_instance,
                            MemberType=m["MemberType"],
                            CreatedUserID=UserID
                        )
                        
                        if not User.objects.filter(id=m["MemberUserID"]).exists():
                            token = request.META.get('HTTP_AUTHORIZATION')
                            username = createUser(token, m["MemberUserID"])
                            
                        if not m["MemberUserID"] == UserID:
                            activity_description = f"{UserName} added {m['username']} to {ProjectName}"
                            set_activityLog(UserID, project_instance, None,
                                            activity_description)
                            set_Notification(
                                m["MemberUserID"], project_instance, None, "project", "create")
                            
                            
                        
                
                # invited_mails = []
                if InvitedList:
                    ret = request.POST
                    InvitedList = json.loads(ret['InvitedList'])
                    for i in InvitedList:
                        if not InvitedUsers.objects.filter(Email=i).exists():
                            InvitedUsers.objects.create(
                                Email=i,
                                MemberProject=project_instance,
                                CreatedUserID=UserID
                            )
                            # invited_mails.append(i)
                    
                DocFiles = request.FILES
                if DocFiles:
                    for d in DocFiles:
                        d = DocFiles[d]
                        Documents.objects.create(
                            ProjectID=project_instance,
                            DocFile=d,
                            CreatedUserID=UserID
                        )
                # if DocumentList:
                #     # ret = request.POST
                #     # DocumentList = json.loads(ret['DocumentList'])
                #     print("?????????????????")
                #     print(DocumentList)
                #     DocumentList = json.loads(DocumentList)
                #     print(DocumentList)
                #     for d in DocumentList:
                #         Documents.objects.create(
                #             ProjectID=project_instance,
                #             DocFile=d,
                #             CreatedUserID=UserID
                #         )
                
                response_data = {
                    "StatusCode": 6000,
                    "message": "successfully Created",
                }
            else:
                response_data = {
                    "StatusCode": 6001,
                    "message": "You already have created Project with same Name"
                }
            

            return Response(response_data, status=status_message)
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
            UserID, "error", "create Project", body_params, err_descrb)
        return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@authentication_classes((JWTTokenUserAuthentication,))
@renderer_classes((JSONRenderer,))
def edit_project(request,pk):
    today = get_today()
    try:
        with transaction.atomic():
            data = request.data
            UserID = request.user.id

            try:
                TaskConfermation = data["TaskConfermation"]
                if TaskConfermation == "true":
                    TaskConfermation = True
                else:
                    TaskConfermation = False
            except:
                TaskConfermation = False

            try:
                TrakPerformance = data["TrakPerformance"]
                if TrakPerformance == "true":
                    TrakPerformance = True
                else:
                    TrakPerformance = False
            except:
                TrakPerformance = False
            ProjectName = data["ProjectName"]
            Description = data["Description"]
            Status = data["Status"]
            Priority = data["Priority"]
            DueDate = data["DueDate"]
            MemberList = data["MemberList"]
            InvitedList = data["InvitedList"]
            UserName = data["CreatedBy"]
            status_message = status.HTTP_200_OK
            instance = Project.objects.get(pk=pk)
            if not Project.objects.filter(is_deleted=False, CreatedUserID=UserID, ProjectName__iexact=ProjectName).exclude(id=instance.id).exists():
                if instance.ProjectName != ProjectName:
                    activity_description = f"{UserName} Updated Project Name from {instance.ProjectName} to {ProjectName}"
                    set_activityLog(UserID, instance, None,
                                    activity_description)
                if instance.Description != Description:
                    activity_description = f"{UserName} Updated Project Description"
                    set_activityLog(UserID, instance, None,
                                    activity_description)
                if instance.Status != Status:
                    activity_description = f"{UserName} Changed Status to {Status}"
                    set_activityLog(UserID, instance, None,
                                    activity_description)
                if instance.Priority != Priority:
                    activity_description = f"{UserName} Changed Priority to {Priority}"
                    set_activityLog(UserID, instance, None,
                                    activity_description)
                if str(instance.DueDate) != str(DueDate):
                    activity_description = f"{UserName} Changed DueDate to {DueDate}"
                    set_activityLog(UserID, instance, None,
                                    activity_description)

                instance.TrakPerformance = TrakPerformance
                instance.TaskConfermation = TaskConfermation
                instance.ProjectName = ProjectName
                instance.Description = Description
                instance.Status = Status
                instance.Priority = Priority
                instance.DueDate = DueDate

                instance.UpdatedUserID = UserID
                instance.UpdatedDate = today
                instance.Action = "M"
                instance.save()
                
                new_member_emails = []
                if MemberList:
                    ret = request.POST
                    MemberList = json.loads(ret['MemberList'])
                    for m in MemberList:
                        members_ins = Members.objects.filter(MemberProject=instance, is_ActiveMember=True)
                        
                        if members_ins:
                            memberIds = members_ins.values_list('MemberUserID',flat=True)
                            ids = [val['MemberUserID'] for val in MemberList]
                            removed_ids = list(set(memberIds) - set(ids))
                            if removed_ids:
                                for r in removed_ids:
                                    RemovedUser = GetUsername(r,request)
                                    members_ins.filter(MemberUserID=r).update(is_ActiveMember=False)
                                    activity_description = f"{UserName} removed {RemovedUser} from {ProjectName}"
                                    set_activityLog(UserID, instance, None,
                                                    activity_description)
                            for mi in memberIds:
                                member = members_ins.filter(MemberUserID=mi).first()
                                if mi == m["MemberUserID"] and not member.MemberType == m["MemberType"]:
                                    member.MemberType = m["MemberType"]
                                    member.save()
                                    type_user = GetUsername(mi, request)
                                    activity_description = f"{UserName} changed Type of {type_user} to {m['MemberType']}"
                                    set_activityLog(UserID, instance, None,
                                                    activity_description)
                            
                        if not Members.objects.filter(MemberUserID=m["MemberUserID"], MemberProject=instance, is_ActiveMember=True).exists():
                            new_member_emails.append(m["email"])
                            Members.objects.create(
                                MemberUserID=m["MemberUserID"],
                                MemberProject=instance,
                                MemberType=m["MemberType"],
                                CreatedUserID=UserID
                            )
                            if not User.objects.filter(id=m["MemberUserID"]).exists():
                                token = request.META.get('HTTP_AUTHORIZATION')
                                username = createUser(token, m["MemberUserID"])
                            activity_description = f"{UserName} added {m['username']} to {ProjectName}"
                            set_activityLog(UserID, instance, None,
                                        activity_description)
                
                if InvitedList:
                    ret = request.POST
                    InvitedList = json.loads(ret['InvitedList'])
                    for i in InvitedList:
                        if not InvitedUsers.objects.filter(Email=i).exists():
                            InvitedUsers.objects.create(
                                Email=i,
                                MemberProject=instance,
                                CreatedUserID=UserID,
                            )

                docs_ins = Documents.objects.filter(ProjectID=instance)
                print(docs_ins,"^^^^^^^^^^^&&&&&&&&^^^^^^^^^^^^")
                if docs_ins:
                    for p in docs_ins:
                        baseUrl = settings.BASE_DIR
                        baseUrl = baseUrl + p.DocFile.url
                        file_exists = exists(baseUrl)
                        if file_exists:
                            os.remove(baseUrl)
                docs_ins.delete()
                            
                DocFiles = request.FILES
                print(DocFiles)
                if DocFiles:
                    for d in DocFiles:
                        d = DocFiles[d]
                        Documents.objects.create(
                            ProjectID=instance,
                            DocFile=d,
                            CreatedUserID=UserID
                        )

                response_data = {
                    "StatusCode": 6000,
                    "message": "successfully Updated",
                    "new_member_emails": new_member_emails
                }
            else:
                response_data = {
                    "StatusCode": 6001,
                    "message": "You already have created Project with same Name"
                }

            return Response(response_data, status=status_message)
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
            UserID, "error", "create Project", body_params, err_descrb)
        return Response(response_data, status=status.HTTP_200_OK)
    
    


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@authentication_classes((JWTTokenUserAuthentication,))
@renderer_classes((JSONRenderer,))
def list_project(request):
    today = get_today()
    data = request.data
    UserID = request.user.id
    ProjectFilter = data["ProjectFilter"]
    FilterStartDate = data["FilterStartDate"]
    FilterEndDate = data["FilterEndDate"]
    try:
        page_number = data["page_no"]
    except:
        page_number = ""
    try:
        items_per_page = data["items_per_page"]
    except:
        items_per_page = ""
    status_message = status.HTTP_200_OK
    
    if Members.objects.filter(is_deleted=False,MemberUserID=UserID, is_ActiveMember=True).exists():
        member_instaces = Members.objects.filter(
            is_deleted=False, MemberUserID=UserID, is_ActiveMember=True)
        statuses = ['todo', 'progress', 'completed']
        priorities = ['low', 'medium', 'high']
        if FilterStartDate and FilterEndDate:
            member_instaces = member_instaces.filter(
                MemberProject__DueDate__gte=FilterStartDate, MemberProject__DueDate__lte=FilterEndDate)
        if ProjectFilter:
            # StatusFilter = [x['value']
            #                 for x in ProjectFilter if x['name'] == 'status']
            # PriorityFilter = [x['value']
            #                   for x in ProjectFilter if x['name'] == 'priority']
            
            statuses_as_set = set(statuses)
            intersection_status = statuses_as_set.intersection(ProjectFilter)
            intersection_status_as_list = list(intersection_status)
            
            pririties_as_set = set(priorities)
            intersection_priority = pririties_as_set.intersection(ProjectFilter)
            intersection_priority_as_list = list(intersection_priority)

            if intersection_status_as_list:
                statuses = intersection_status_as_list
            if intersection_priority_as_list:
                priorities = intersection_priority_as_list
        
        project_ids = member_instaces.values_list("MemberProject",flat=True)
        instances = Project.objects.filter(
            id__in=project_ids, Status__in=statuses, Priority__in=priorities).order_by("-CreatedDate")
        count = len(instances)
        if page_number and items_per_page:
            instances = list_pagination(
                instances, items_per_page, page_number
            )
        serialzed = serialization.ProjectModelSerializer(
            instances, many=True, context={"UserID": UserID, "request": request})
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
            "count": count,
            "project_notify": project_notify,
            "task_notify": task_notify,
        }
    else:
        response_data = {
            "StatusCode": 6001,
            "message": "You are not Member of Any Active Projects"
        }

    return Response(response_data, status=status_message)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@authentication_classes((JWTTokenUserAuthentication,))
@renderer_classes((JSONRenderer,))
def update_progress(request):
    today = get_today()
    data = request.data
    UserID = request.user.id
    pk = data["ProjectID"]
    Progress = data["Progress"]
    try:
        UserName = data["UserName"]
    except:
        UserName = ""
    status_message = status.HTTP_200_OK
    if Project.objects.filter(pk=pk).exists():
        instaces = Project.objects.get(pk=pk)
        instaces.Status=Progress
        instaces.save()
        activity_description = f"{UserName} Changed Status to {Progress}"
        set_activityLog(UserID, instaces, None,
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
def project_comments(request):
    today = get_today()
    data = request.data
    UserID = request.user.id
    ProjectID = data["ProjectID"]
    TaskID = data["TaskID"]
    comment = data["comment"]
    project = getProject(ProjectID)
    task = getTask(TaskID)
    type = data["type"]
    unq_id = data["unq_id"]
    status_message = status.HTTP_200_OK
    
    if type == "create":
        instance = Comments.objects.create(
            UserID=UserID,
            ProjectID=project,
            TaskID=task,
            Comment=comment
        )
        comments_ins = Comments.objects.filter(
            is_deleted=False, ProjectID=project)
        commentsSerialized = serialization.CommentModelSerializer(comments_ins, many=True,context={"request": request})
        comment_list = commentsSerialized.data
        response_data = {
            "StatusCode": 6000,
            "data": comment_list
        }
    elif type == "edit" and unq_id:
        instance = Comments.objects.filter(id=unq_id).update(Comment=comment,Action="E")
        comments_ins = Comments.objects.filter(
            is_deleted=False, ProjectID=project)
        commentsSerialized = serialization.CommentModelSerializer(
            comments_ins, many=True, context={"request": request})
        comment_list = commentsSerialized.data
        response_data = {
            "StatusCode": 6000,
            "data": comment_list
        }
    elif type == "delete" and unq_id:
        instance = Comments.objects.filter(
            id=unq_id).update(Comment=comment, Action="D",is_deleted=True)
        comments_ins = Comments.objects.filter(
            is_deleted=False, ProjectID=project)
        commentsSerialized = serialization.CommentModelSerializer(
            comments_ins, many=True, context={"request": request})
        comment_list = commentsSerialized.data
        response_data = {
            "StatusCode": 6000,
            "data": comment_list
        }
        
    else:
        response_data = {
            "StatusCode": 6000,
            "data": []
        }
        
    return Response(response_data, status=status_message)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@authentication_classes((JWTTokenUserAuthentication,))
@renderer_classes((JSONRenderer,))
def delete_project(request,pk):
    today = get_today()
    data = request.data
    UserID = request.user.id
    UserName = data["UserName"]
    status_message = status.HTTP_200_OK
    
    if Project.objects.filter(pk=pk).exists():
        instance = Project.objects.get(pk=pk)
        instance.is_deleted = True
        instance.save()
        if Members.objects.filter(MemberProject=instance).exists():
            member_ins = Members.objects.filter(MemberProject=instance).update(is_deleted=True)
        if Documents.objects.filter(ProjectID=instance).exists():
            member_ins = Documents.objects.filter(
                ProjectID=instance).update(is_deleted=True)
            
        activity_description = f"{UserName} deleted Project {instance.ProjectName}"
        set_activityLog(UserID, instance, None,
                        activity_description)
        response_data = {
            "StatusCode": 6000,
        }
    else:
        response_data = {
            "StatusCode": 6001,
            "message": "Project Not Found"
        }

    return Response(response_data, status=status_message)
