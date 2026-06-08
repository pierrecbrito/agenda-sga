from django.urls import path

from .views import (
    CpfLoginView,
    CpfLogoutView,
    account,
    home,
    cidadao_autocomplete,
    PremiumPasswordResetView,
    PremiumPasswordResetDoneView,
    PremiumPasswordResetConfirmView,
    PremiumPasswordResetCompleteView,
    register,
    cidadao_list,
)

urlpatterns = [
    path("", CpfLoginView.as_view(), name="login"),
    path("home/", home, name="home"),
    path("conta/", account, name="account"),
    path("sair/", CpfLogoutView.as_view(), name="logout"),
    path("api/cidadaos/autocomplete/", cidadao_autocomplete, name="cidadao_autocomplete"),
    path("cadastrar/", register, name="register"),
    path("cidadaos/", cidadao_list, name="cidadao_list"),
    path("recuperar-senha/", PremiumPasswordResetView.as_view(), name="password_reset"),
    path("recuperar-senha/enviado/", PremiumPasswordResetDoneView.as_view(), name="password_reset_done"),
    path("recuperar-senha/confirmar/<uidb64>/<token>/", PremiumPasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("recuperar-senha/concluido/", PremiumPasswordResetCompleteView.as_view(), name="password_reset_complete"),
]
