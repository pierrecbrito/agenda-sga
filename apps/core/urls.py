from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from .forms import CpfAuthenticationForm
from .views import home

urlpatterns = [
    path(
        "",
        LoginView.as_view(template_name="registration/login.html", authentication_form=CpfAuthenticationForm),
        name="login",
    ),
    path("home/", home, name="home"),
    path("sair/", LogoutView.as_view(next_page="login"), name="logout"),
]
