from django.contrib import admin
from django.urls import path, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include("users.urls")),
    path('api/v1/general/', include("api.v1.general.urls")),
    path('api/v1/accounts/', include("api.v1.accounts.urls")),
    path('api/v1/projects/', include("api.v1.projects.urls")),
    path('api/v1/tasks/', include("api.v1.tasks.urls")),
    path('task-tables', include("task_tables.urls")),
]

urlpatterns += staticfiles_urlpatterns()
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
