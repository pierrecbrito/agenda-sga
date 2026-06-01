from django.urls import path

from .views import index

app_name = "processos"

urlpatterns = [
    path("", index, name="index"),
]
