from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.shortcuts import render
from django.utils import timezone

from apps.agendamentos.models import VagaAgendamento
from apps.core.models import Cidadao
from apps.core.access import get_user_role
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
    role = get_user_role(request.user)
    hoje = timezone.localdate()

    # Métricas gerais (super admin vê tudo, admin de UBS filtra por UBS)
    if role == "super_admin":
        vagas_qs = VagaAgendamento.objects.all()
        ubs_qs = Ubs.objects.all()
    elif role == "ubs_admin":
        ubs_gerenciadas = Ubs.objects.filter(admins__user=request.user)
        vagas_qs = VagaAgendamento.objects.filter(ubs__in=ubs_gerenciadas)
        ubs_qs = ubs_gerenciadas
    elif role == "cidadao" and hasattr(request.user, "cidadao"):
        vagas_qs = VagaAgendamento.objects.filter(cidadao=request.user.cidadao)
        ubs_qs = Ubs.objects.none()
    else:
        vagas_qs = VagaAgendamento.objects.none()
        ubs_qs = Ubs.objects.none()

    total_ubs = ubs_qs.count()
    total_cidadaos = Cidadao.objects.count() if role == "super_admin" else 0

    total_confirmados = vagas_qs.filter(status=VagaAgendamento.Status.CONFIRMADO).count()
    total_executados = vagas_qs.filter(status=VagaAgendamento.Status.EXECUTADO).count()
    total_cancelados = vagas_qs.filter(
        status__in=[VagaAgendamento.Status.CANCELADO_PACIENTE, VagaAgendamento.Status.CANCELADO_UBS]
    ).count()
    total_faltas = vagas_qs.filter(status=VagaAgendamento.Status.FALTA).count()
    total_agendamentos = vagas_qs.count()

    # Agendamentos de hoje
    agendamentos_hoje = vagas_qs.filter(
        data_vaga=hoje, status=VagaAgendamento.Status.CONFIRMADO
    ).count()

    # Agendamentos desta semana
    from datetime import timedelta
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    fim_semana = inicio_semana + timedelta(days=6)
    agendamentos_semana = vagas_qs.filter(
        data_vaga__range=(inicio_semana, fim_semana),
        status=VagaAgendamento.Status.CONFIRMADO,
    ).count()

    # Taxa de execução (executados / total com status final * 100)
    total_finalizados = total_executados + total_cancelados + total_faltas
    taxa_execucao = round((total_executados / total_finalizados * 100) if total_finalizados > 0 else 0)

    # Próximos agendamentos confirmados
    proximos = (
        vagas_qs
        .filter(status=VagaAgendamento.Status.CONFIRMADO, data_vaga__gte=hoje)
        .select_related("ubs", "especialidade", "cidadao")
        .order_by("data_vaga", "hora_inicio")[:8]
    )

    context = {
        "role": role,
        "total_ubs": total_ubs,
        "total_cidadaos": total_cidadaos,
        "total_confirmados": total_confirmados,
        "total_executados": total_executados,
        "total_cancelados": total_cancelados,
        "total_faltas": total_faltas,
        "total_agendamentos": total_agendamentos,
        "agendamentos_hoje": agendamentos_hoje,
        "agendamentos_semana": agendamentos_semana,
        "taxa_execucao": taxa_execucao,
        "proximos": proximos,
        "hoje": hoje,
    }
    return render(request, "core/home.html", context)


@login_required
def account(request):
    return render(request, "core/account.html")


@login_required
def cidadao_autocomplete(request):
    """Endpoint JSON para autocomplete de cidadãos por CPF ou nome."""
    q = (request.GET.get("q") or "").strip()
    if len(q) < 2:
        return JsonResponse({"results": []})

    digits = "".join(ch for ch in q if ch.isdigit())
    if digits:
        qs = Cidadao.objects.filter(
            Q(cpf__icontains=digits) | Q(nome_completo__icontains=q)
        )
    else:
        qs = Cidadao.objects.filter(nome_completo__icontains=q)

    results = [
        {"id": c.pk, "nome": c.nome_completo, "cpf": c.cpf}
        for c in qs[:10]
    ]
    return JsonResponse({"results": results})
