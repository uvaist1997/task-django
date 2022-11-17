from django.urls import path, re_path
from . import views

app_name = 'api.v1.general.urls'

urlpatterns = [
    path("summary", views.summary, name="Summary"),
    path("send-mail", views.send_mail, name="send_mail"),
    path("view-notification", views.view_notification, name="view_notification"),
    path("check-notification", views.check_notification, name="check_notification"),
]