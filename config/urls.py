from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
    path("agendamentos/", include("apps.agendamentos.urls")),
    path("ubs/", include("apps.ubs.urls")),
    path("relatorio/", include("apps.logs.urls", namespace="logs")),
]

handler404 = "apps.core.views.handler404"
