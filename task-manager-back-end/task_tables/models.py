from ast import Assign
from audioop import add
from typing import Type
from django.db import models
from main.models import BaseModel
import uuid
from django.utils.translation import gettext_lazy as _

# Create your models here.


class Project(BaseModel):
    ProjectName = models.CharField(
        max_length=128, blank=True, null=True, db_index=True)
    Description = models.TextField(blank=True, null=True)
    Status = models.CharField(
        max_length=128, blank=True, null=True, db_index=True)
    Priority = models.CharField(max_length=128, blank=True, null=True)
    DueDate = models.DateField(blank=True, null=True)
    TaskConfermation = models.BooleanField(default=False)
    TrakPerformance = models.BooleanField(default=False)
    class Meta:
        db_table = 'projects_table'

    def __str__(self):
        return str(self.id)


class Task(BaseModel):
    Title = models.CharField(
        max_length=1000, blank=True, null=True, db_index=True)
    Description = models.TextField(blank=True, null=True)
    Status = models.CharField(
        max_length=128, blank=True, null=True, db_index=True)
    Assignee = models.BigIntegerField(blank=True, null=True)
    Reporter = models.BigIntegerField(blank=True, null=True)
    TaskProject = models.ForeignKey(
        "task_tables.Project", related_name="Task_Project", on_delete=models.CASCADE, blank=True, null=True
    )
    Priority = models.CharField(max_length=128, blank=True, null=True)
    DueDate = models.DateField(blank=True, null=True)
    TaskConfermation = models.BooleanField(default=False)


    class Meta:
        db_table = 'projects_task'

    def __str__(self):
        return str(self.id)


class SubTask(BaseModel):
    MainTask = models.ForeignKey(
        "task_tables.Task", related_name="Task_sub", on_delete=models.CASCADE, blank=True, null=True
    )
    Description = models.TextField(blank=True, null=True)
    is_completed = models.BooleanField(default=False)
    

    class Meta:
        db_table = 'projects_sub_task'

    def __str__(self):
        return str(self.id)
    
    
class Members(BaseModel):
    MemberUserID = models.BigIntegerField(blank=True, null=True)
    MemberProject = models.ForeignKey(
        "task_tables.Project", related_name="Member_Project", on_delete=models.CASCADE, blank=True, null=True
    )
    is_ActiveMember = models.BooleanField(default=True)
    MemberType = models.CharField(
        max_length=128, blank=True, null=True, db_index=True)

    class Meta:
        db_table = 'projects_members'

    def __str__(self):
        return str(self.id)
    

class Comments(BaseModel):
    UserID = models.BigIntegerField(blank=True, null=True)
    ProjectID = models.ForeignKey(
        "task_tables.Project", related_name="Comments_Project", on_delete=models.CASCADE, blank=True, null=True
    )
    TaskID = models.ForeignKey(
        "task_tables.Task", related_name="Comments_Task", on_delete=models.CASCADE, blank=True, null=True
    )
    Comment = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'comments_table'

    def __str__(self):
        return str(self.id)
    
    
class Documents(BaseModel):
    ProjectID = models.ForeignKey(
        "task_tables.Project", related_name="Documents_Project", on_delete=models.CASCADE, blank=True, null=True
    )
    TaskID = models.ForeignKey(
        "task_tables.Task", related_name="Documents_Task", on_delete=models.CASCADE, blank=True, null=True
    )
    DocFile = models.FileField(upload_to='documents/')

    class Meta:
        db_table = 'documents_table'

    def __str__(self):
        return str(self.id)
    
    
class ActivityLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    UserID = models.BigIntegerField(blank=True, null=True)
    ProjectID = models.ForeignKey(
        "task_tables.Project", related_name="ActivityLog_Project", on_delete=models.CASCADE, blank=True, null=True
    )
    TaskID = models.ForeignKey(
        "task_tables.Task", related_name="ActivityLog_Task", on_delete=models.CASCADE, blank=True, null=True
    )
    Description = models.TextField(blank=True, null=True)
    CreatedDate = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
    Action = models.CharField(
        max_length=128, default="A", blank=True, null=True)

    class Meta:
        db_table = 'activitylog_table'

    def __str__(self):
        return str(self.id)


class ErrorLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    UserID = models.BigIntegerField(blank=True, null=True)
    Description = models.TextField(blank=True, null=True)
    error_type = models.CharField(max_length=128, blank=True, null=True,default="error")
    is_deleted = models.BooleanField(default=False)
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)
    action = models.CharField(
        max_length=128, blank=True, null=True, default="View")
    is_solved = models.BooleanField(default=False)
    body_params = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'errorlog_table'

    def __str__(self):
        return str(self.id)


class InvitedUsers(BaseModel):
    Email = models.EmailField(blank=True, null=True)
    MemberProject = models.ForeignKey(
        "task_tables.Project", related_name="Invited_Member_Project", on_delete=models.CASCADE, blank=True, null=True
    )

    class Meta:
        db_table = 'projects_invited_member'

    def __str__(self):
        return str(self.id)


class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    UserID = models.BigIntegerField(blank=True, null=True)
    ProjectID = models.ForeignKey(
        "task_tables.Project", related_name="Notification_Project", on_delete=models.CASCADE, blank=True, null=True
    )
    TaskID = models.ForeignKey(
        "task_tables.Task", related_name="Notification_Task", on_delete=models.CASCADE, blank=True, null=True
    )
    is_view = models.BooleanField(default=True)

    class Meta:
        db_table = 'notification_table'

    def __str__(self):
        return str(self.id)
