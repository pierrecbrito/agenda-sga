from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.shortcuts import render

from .forms import CpfAuthenticationForm
from apps.ubs.models import EnderecoUbs, Ubs


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
    ubs_queryset = Ubs.objects.select_related("endereco").order_by("nome_fantasia")
    ubs_lista = []
    ubs_localizadas = []

    for ubs in ubs_queryset:
        try:
            endereco = ubs.endereco
        except EnderecoUbs.DoesNotExist:
            endereco = None

        endereco_contexto = None
        if endereco:
            endereco_contexto = {
                "logradouro": endereco.logradouro,
                "numero": endereco.numero,
                "bairro": endereco.bairro,
                "cidade": endereco.cidade,
                "uf": endereco.uf,
                "latitude": float(endereco.latitude) if endereco.latitude is not None else None,
                "longitude": float(endereco.longitude) if endereco.longitude is not None else None,
            }

            if endereco.latitude is not None and endereco.longitude is not None:
                ubs_localizadas.append(
                    {
                        "nome": ubs.nome_fantasia,
                        "cnes": ubs.cnes,
                        "distrito_sanitario": ubs.distrito_sanitario,
                        "logradouro": endereco.logradouro,
                        "numero": endereco.numero,
                        "bairro": endereco.bairro,
                        "cidade": endereco.cidade,
                        "uf": endereco.uf,
                        "latitude": float(endereco.latitude),
                        "longitude": float(endereco.longitude),
                    }
                )

        ubs_lista.append(
            {
                "nome": ubs.nome_fantasia,
                "cnes": ubs.cnes,
                "distrito_sanitario": ubs.distrito_sanitario,
                "telefone": ubs.telefone,
                "endereco": endereco_contexto,
            }
        )

    context = {
        "total_ubs": ubs_queryset.count(),
        "total_enderecos_ubs": EnderecoUbs.objects.count(),
        "total_ubs_localizadas": len(ubs_localizadas),
        "ubs_localizadas": ubs_localizadas,
        "ubs_lista": ubs_lista,
    }
    return render(request, "core/home.html", context)
