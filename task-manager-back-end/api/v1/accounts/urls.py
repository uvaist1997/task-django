from django.urls import path, re_path
from . import views

app_name = 'api.v1.accounts.urls'

urlpatterns = [
    path("accounts", views.accounts, name="accounts"),
]