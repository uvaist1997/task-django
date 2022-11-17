from requests import request
from rest_framework import serializers
from main.functions import GetUsername, converted_float
from task_tables.models import Comments, Documents, Members, Notification, Project, SubTask,Task
from users import models
from django.db.models import Max, Prefetch, Q, Sum
from django.contrib.auth.models import User


class TaskSerializer(serializers.ModelSerializer):
    DocumentList = serializers.SerializerMethodField()
    SubTaskList = serializers.SerializerMethodField()
    CommentList = serializers.SerializerMethodField()
    ReporterName = serializers.SerializerMethodField()
    AssigneeName = serializers.SerializerMethodField()
    ProjectName = serializers.SerializerMethodField()
    Progress = serializers.SerializerMethodField()
    CreatedBy = serializers.SerializerMethodField()
    CreatedDate = serializers.SerializerMethodField()
    user_type = serializers.SerializerMethodField()
    membersList = serializers.SerializerMethodField()
    is_view = serializers.SerializerMethodField()


    class Meta:
        model = Task
        exclude = ('UpdatedDate', 'DeletedDate',
                   'UpdatedUserID', 'DeletededUserID')

    def get_is_view(self, instance):
        UserID = self.context.get("UserID")
        is_view = True
        if Notification.objects.filter(UserID=UserID, TaskID=instance).exists():
            is_view = Notification.objects.filter(
                UserID=UserID, TaskID=instance).first().is_view
        return is_view
    
    def get_user_type(self, instance):
        UserID = self.context.get("UserID")
        user_type = ""
        if Members.objects.filter(MemberUserID=UserID, MemberProject=instance.TaskProject).exists():
            user_type = Members.objects.get(
                MemberUserID=UserID, MemberProject=instance.TaskProject).MemberType
        return user_type

    def get_CreatedBy(self, instance):
        CreatedUserID = instance.CreatedUserID
        username = User.objects.get(id=CreatedUserID).username
        return username
    
    def get_CreatedDate(self, instance):
        CreatedDate = instance.CreatedDate.date()
        return CreatedDate

    def get_DocumentList(self, instance):
        docs = []
        if Documents.objects.filter(is_deleted=False, TaskID=instance).exists():
            doc_ins = Documents.objects.filter(
                is_deleted=False, TaskID=instance)
            docSerialized = TaskDocumentSerializer(doc_ins,many=True)
            docs = docSerialized.data
        return docs
    
    
    def get_CommentList(self, instance):
        comment_list = []
        if Comments.objects.filter(is_deleted=False, TaskID=instance).exists():
            member_ins = Comments.objects.filter(
                is_deleted=False, TaskID=instance)
            memberSerialized = CommentModelSerializer(member_ins, many=True)
            comment_list = memberSerialized.data
        return comment_list
    
    def get_ReporterName(self, instance):
        request = self.context.get("request")
        ReporterName = ""
        if instance.Reporter:
            ReporterName = GetUsername(instance.Reporter, request)
        return ReporterName

    def get_AssigneeName(self, instance): 
        request = self.context.get("request")
        AssigneeName = ""
        if instance.Assignee:
            AssigneeName = GetUsername(instance.Assignee, request)
        return AssigneeName

    def get_ProjectName(self, instance):  
        ProjectName = ""
        if instance.TaskProject:
            ProjectName = instance.TaskProject.ProjectName      
        return ProjectName

    def get_SubTaskList(self, instance):
        subTasklist = []
        if SubTask.objects.filter(is_deleted=False, MainTask=instance).exists():
            subtask_ins = SubTask.objects.filter(
                is_deleted=False, MainTask=instance)
            subTaskSerialized = SubTaskSerializer(subtask_ins, many=True)
            subTasklist = subTaskSerialized.data
        return subTasklist
    
    def get_Progress(self, instace):
        UserID = self.context.get("UserID")
        Progress = 0
        if SubTask.objects.filter(MainTask=instace, is_deleted=False).exists():
            tasks = SubTask.objects.filter(
                MainTask=instace, is_deleted=False)
            total_task = tasks.count()
            completed_task = tasks.filter(is_completed=True).count()
            Progress = (converted_float(
                completed_task) / converted_float(total_task)) * 100
        if instace.Status == "completed":
            Progress = 100
        return Progress

    def get_membersList(self, instance):
        members = []
        if instance.TaskProject and Members.objects.filter(MemberProject=instance.TaskProject, is_ActiveMember=True):
            member_ins = Members.objects.filter(
                MemberProject=instance.TaskProject, is_ActiveMember=True)
            for i in member_ins:
                username = GetUsername(i.MemberUserID, request)
                members.append({
                    "username": username,
                    "UserID": i.MemberUserID
                })
        return members

class TaskDocumentSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    class Meta:
        model = Documents
        exclude = ('UpdatedDate', 'DeletedDate',
                   'UpdatedUserID', 'DeletededUserID')

    def get_name(self, instace):
        name = ""
        if instace.DocFile:
            name = instace.DocFile.name.split("/")[1]
        return name
        
class CommentModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comments
        exclude = ('UpdatedDate', 'DeletedDate',
                   'UpdatedUserID', 'DeletededUserID')


class SubTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubTask
        exclude = ('UpdatedDate', 'DeletedDate',
                   'UpdatedUserID', 'DeletededUserID')


