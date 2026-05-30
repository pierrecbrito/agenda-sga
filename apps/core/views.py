from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.shortcuts import render

from .forms import CpfAuthenticationForm


class CpfLoginView(LoginView):
    template_name = "registration/login.html"
    authentication_form = CpfAuthenticationForm

    def form_valid(self, form):
        messages.success(self.request, "Login realizado com sucesso.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "CPF ou senha inválidos.")
        return super().form_invalid(form)


class CpfLogoutView(LogoutView):
    next_page = reverse_lazy("login")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "Você saiu do sistema.")
        return super().dispatch(request, *args, **kwargs)


@login_required
def home(request):
    return render(request, "core/home.html")
