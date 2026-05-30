from django.urls import path

from .views import create, delete, detail, index, update

app_name = "ubs"

urlpatterns = [
    path("", index, name="index"),
    path("nova/", create, name="create"),
    path("<int:pk>/", detail, name="detail"),
    path("<int:pk>/editar/", update, name="update"),
    path("<int:pk>/excluir/", delete, name="delete"),
]