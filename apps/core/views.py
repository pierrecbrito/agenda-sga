from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.shortcuts import render

from apps.agendamentos.models import VagaAgendamento
from apps.ubs.models import Ubs

from .forms import CpfAuthenticationForm


class CpfLoginView(LoginView):
    template_name = "registration/login.html"
    authentication_form = CpfAuthenticationForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["show_global_header"] = False
        context["show_global_footer"] = True
        context["footer_variant"] = "login"
        return context

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
    total_ubs = Ubs.objects.count()
    total_vagas_confirmadas = VagaAgendamento.objects.filter(status=VagaAgendamento.Status.CONFIRMADO).count()
    total_vagas_executadas = VagaAgendamento.objects.filter(status=VagaAgendamento.Status.EXECUTADO).count()
    total_agendamentos_vinculados = VagaAgendamento.objects.filter(cidadao__isnull=False).count()

    context = {
        "total_ubs": total_ubs,
        "total_vagas_confirmadas": total_vagas_confirmadas,
        "total_vagas_executadas": total_vagas_executadas,
        "total_agendamentos_vinculados": total_agendamentos_vinculados,
    }
    return render(request, "core/home.html", context)


@login_required
def account(request):
    return render(request, "core/account.html")
