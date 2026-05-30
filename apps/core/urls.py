from django.contrib.auth.views import LoginView
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
]
