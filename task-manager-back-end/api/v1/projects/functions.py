from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

from task_tables.models import Project, Task


def getProject(pk):
    project = None
    if Project.objects.filter(pk=pk).exists():
        project = Project.objects.get(pk=pk)
    return project


def getTask(pk):
    task = None
    if Task.objects.filter(pk=pk).exists():
        task = Task.objects.get(pk=pk)
    return task
