from django.urls import path

from .views import relatorio_logs

app_name = "logs"

urlpatterns = [
    path("", relatorio_logs, name="index"),
]
