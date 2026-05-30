from django.urls import path

from .views import CpfLoginView, CpfLogoutView, home

urlpatterns = [
    path("", CpfLoginView.as_view(), name="login"),
    path("home/", home, name="home"),
    path("sair/", CpfLogoutView.as_view(), name="logout"),
]
