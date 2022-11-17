from requests import request
from rest_framework import serializers
from main.functions import GetUsername, converted_float
from task_tables.models import ActivityLog, Comments, Documents, Members, Notification, Project, Task
from users import models
from django.db.models import Max, Prefetch, Q, Sum
from django.contrib.auth.models import User


class ProjectModelSerializer(serializers.ModelSerializer):
    MemberType = serializers.SerializerMethodField()
    DocumentList = serializers.SerializerMethodField()
    MemberList = serializers.SerializerMethodField()
    CommentList = serializers.SerializerMethodField()
    HistoryList = serializers.SerializerMethodField()
    Progress = serializers.SerializerMethodField()
    ToDoTaskCount = serializers.SerializerMethodField()
    ProgressTaskCount = serializers.SerializerMethodField()
    CompletedTaskCount = serializers.SerializerMethodField()
    UnconfirmedCount = serializers.SerializerMethodField()
    CreatedBy = serializers.SerializerMethodField()
    CreatedDate = serializers.SerializerMethodField()
    is_view = serializers.SerializerMethodField()

    class Meta:
        model = Project
        exclude = ('UpdatedDate', 'DeletedDate',
                   'UpdatedUserID', 'DeletededUserID')

    def get_is_view(self, instance):
        UserID = self.context.get("UserID")
        is_view = True
        if Notification.objects.filter(UserID=UserID, ProjectID=instance).exists():
            is_view = Notification.objects.filter(
                UserID=UserID, ProjectID=instance).first().is_view
        return is_view
    
    def get_CreatedBy(self, instance):
        CreatedUserID = instance.CreatedUserID
        username = User.objects.get(id=CreatedUserID).username
        return username
    
    def get_CreatedDate(self, instance):
        CreatedDate = instance.CreatedDate.date()
        return CreatedDate
    
    
    def get_UnconfirmedCount(self, instace):
        UserID = self.context.get("UserID")
        UnconfirmedCount = 0
        if Task.objects.filter(TaskProject=instace, is_deleted=False, Reporter=UserID, Status="confirming").exists():
            UnconfirmedCount = Task.objects.filter(
                TaskProject=instace, is_deleted=False, Reporter=UserID, Status="confirming").count()
        return UnconfirmedCount

    def get_ToDoTaskCount(self, instace):
        ToDoTaskCount = 0
        UserID = self.context.get("UserID")
        if Task.objects.filter(TaskProject=instace, Assignee=UserID, is_deleted=False).exists():
            tasks = Task.objects.filter(
                TaskProject=instace, Assignee=UserID, is_deleted=False)
            ToDoTaskCount = tasks.filter(Status="todo").count()
        return ToDoTaskCount
    
    def get_ProgressTaskCount(self, instace):
        UserID = self.context.get("UserID")
        ProgressTaskCount = 0
        if Task.objects.filter(TaskProject=instace, Assignee=UserID, is_deleted=False).exists():
            tasks = Task.objects.filter(
                TaskProject=instace, Assignee=UserID, is_deleted=False)
            ProgressTaskCount = tasks.filter(Status="progress").count()
        return ProgressTaskCount
    
    def get_CompletedTaskCount(self, instace):
        UserID = self.context.get("UserID")
        CompletedTaskCount = 0
        if Task.objects.filter(TaskProject=instace, Assignee=UserID, is_deleted=False).exists():
            tasks = Task.objects.filter(
                TaskProject=instace, Assignee=UserID, is_deleted=False)
            CompletedTaskCount = tasks.filter(Status="completed").count()
        return CompletedTaskCount

    def get_Progress(self, instace):
        UserID = self.context.get("UserID")
        Progress = 0
        if Task.objects.filter(TaskProject=instace, Assignee=UserID, is_deleted=False).exists():
            tasks = Task.objects.filter(
                TaskProject=instace, Assignee=UserID, is_deleted=False)
            total_task = tasks.count()
            completed_task = tasks.filter(Status="completed").count()
            Progress = (converted_float(
                completed_task) / converted_float(total_task)) * 100
        return Progress
    
    def get_MemberType(self, instace):
        UserID = self.context.get("UserID")
        type = ""
        if Members.objects.filter(is_deleted=False, MemberProject=instace, is_ActiveMember=True, MemberUserID=UserID).exists():
            member_ins = Members.objects.filter(
                is_deleted=False, MemberProject=instace, is_ActiveMember=True, MemberUserID=UserID).first()
            type = member_ins.MemberType
        return str(type)
    
    def get_DocumentList(self, instace):
        UserID = self.context.get("UserID")
        docs = []
        if Documents.objects.filter(is_deleted=False, ProjectID=instace).exists():
            doc_ins = Documents.objects.filter(
                is_deleted=False, ProjectID=instace)
            docSerialized = ProjecDocumentModelSerializer(doc_ins,many=True)
            docs = docSerialized.data
        return docs
    
    def get_MemberList(self, instace):
        UserID = self.context.get("UserID")
        request = self.context.get("request")
        member_list = []
        if Members.objects.filter(is_deleted=False, MemberProject=instace, is_ActiveMember=True).exists():
            member_ins = Members.objects.filter(
                is_deleted=False, MemberProject=instace, is_ActiveMember=True)
            memberSerialized = MemberModelSerializer(member_ins, many=True, context={
                                                     "UserID": UserID, "request": request})
            member_list = memberSerialized.data
        return member_list
    
    def get_CommentList(self, instace):
        UserID = self.context.get("UserID")
        request = self.context.get("request")
        comment_list = []
        if Comments.objects.filter(is_deleted=False, ProjectID=instace).exists():
            comments_ins = Comments.objects.filter(
                is_deleted=False, ProjectID=instace)
            commentsSerialized = CommentModelSerializer(comments_ins, many=True, context={
                "UserID": UserID, "request": request})
            comment_list = commentsSerialized.data
        return comment_list
    
    def get_HistoryList(self, instace):
        UserID = self.context.get("UserID")
        request = self.context.get("request")
        history_list = []
        if ActivityLog.objects.filter(is_deleted=False, ProjectID=instace).exists():
            history_ins = ActivityLog.objects.filter(
                is_deleted=False, ProjectID=instace)
            historySerialized = ActivityLogModelSerializer(
                history_ins, many=True, context={
                    "UserID": UserID, "request": request})
            history_list = historySerialized.data
        return history_list
    


class ProjecDocumentModelSerializer(serializers.ModelSerializer):
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
    

        
class MemberModelSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    progress_rate = serializers.SerializerMethodField()
    class Meta:
        model = Members
        exclude = ('UpdatedDate', 'DeletedDate',
                   'UpdatedUserID', 'DeletededUserID')
        
    def get_username(self, instace):
        request = self.context.get("request")
        MemberUserID = instace.MemberUserID
        username = GetUsername(MemberUserID, request)
        return username
    
    def get_progress_rate(self, instace):
        MemberUserID = instace.MemberUserID
        MemberProject = instace.MemberProject
        progress = 0
        if Task.objects.filter(TaskProject=MemberProject, Assignee=MemberUserID,is_deleted=False).exists():
            tasks = Task.objects.filter(
                TaskProject=MemberProject, Assignee=MemberUserID, is_deleted=False)
            total_task = tasks.count()
            completed_task = tasks.filter(Status="completed").count()
            progress = (converted_float(
                completed_task) / converted_float(total_task)) * 100
        return progress
        
        
class CommentModelSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    Description = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    class Meta:
        model = Comments
        exclude = ('UpdatedDate', 'DeletedDate',
                   'UpdatedUserID', 'DeletededUserID')

    def get_name(self, instace):
        request = self.context.get("request")
        UserID = instace.UserID
        name = GetUsername(UserID, request)
        return name
    
    def get_Description(self, instace):
        Description = instace.Comment
        return Description

    def get_type(self,instance):
        return "comments"
    
class ActivityLogModelSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    
    class Meta:
        model = ActivityLog
        fields = '__all__'
        
    def get_name(self, instace):
        request = self.context.get("request")
        UserID = instace.UserID
        name = GetUsername(UserID, request)
        return name
    
    def get_type(self,instace):
        return "history"
