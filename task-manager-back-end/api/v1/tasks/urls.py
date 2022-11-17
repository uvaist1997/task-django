from django.urls import path, re_path
from . import views

app_name = 'api.v1.tasks.urls'

urlpatterns = [
    path("create-task", views.create_task, name="Create task"),
    path("list-task", views.list_task, name="List task"),
    re_path('update-status-priority/(?P<pk>.*)/$', views.update_status_priority, name='update_status_priority'),
    re_path('view/task/(?P<pk>.*)/$', views.single_task, name='single_task'),

    re_path('edit/task/(?P<pk>.*)/$', views.edit_task, name='edit_task'),
    re_path('delete/task/(?P<pk>.*)/$', views.delete_task, name='delete_task'),


]