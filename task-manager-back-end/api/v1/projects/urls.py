from django.urls import path, re_path
from . import views

app_name = 'api.v1.projects.urls'

urlpatterns = [
    path("create-project", views.create_project, name="Create Project"),
    path("list-project", views.list_project, name="List Project"),
    path("update-progress", views.update_progress, name="Update Progress"),
    path("project-comments", views.project_comments, name="Project Comments"),
    
    re_path(r'^edit-project/(?P<pk>.*)$',
            views.edit_project, name="Edit project"),
    re_path(r'^delete-project/(?P<pk>.*)$',
            views.delete_project, name="Delete project"),
]