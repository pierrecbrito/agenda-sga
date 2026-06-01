from django.urls import path

from .views import CpfLoginView, CpfLogoutView, account, home, cidadao_autocomplete

urlpatterns = [
    path("", CpfLoginView.as_view(), name="login"),
    path("home/", home, name="home"),
    path("conta/", account, name="account"),
    path("sair/", CpfLogoutView.as_view(), name="logout"),
    path("api/cidadaos/autocomplete/", cidadao_autocomplete, name="cidadao_autocomplete"),
]
