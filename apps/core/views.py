import logging
from django.contrib import messages
from django.contrib.auth import get_user_model, login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone

from apps.agendamentos.models import VagaAgendamento
from apps.core.access import get_user_role
from apps.core.models import Cidadao, Endereco, UbsAdmin
from apps.ubs.models import Ubs

from .forms import CidadaoRegistrationForm, CpfAuthenticationForm


logger = logging.getLogger(__name__)


class ResetHeaderMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["show_global_header"] = False
        return context


class PremiumPasswordResetView(ResetHeaderMixin, PasswordResetView):
    template_name = "registration/password_reset_form.html"
    email_template_name = "registration/password_reset_email.html"
    subject_template_name = "registration/password_reset_subject.txt"


class PremiumPasswordResetDoneView(ResetHeaderMixin, PasswordResetDoneView):
    template_name = "registration/password_reset_done.html"


class PremiumPasswordResetConfirmView(ResetHeaderMixin, PasswordResetConfirmView):
    template_name = "registration/password_reset_confirm.html"


class PremiumPasswordResetCompleteView(ResetHeaderMixin, PasswordResetCompleteView):
    template_name = "registration/password_reset_complete.html"



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


def handler404(request, exception=None):
    return render(request, "404.html", status=404)


def register(request):
    is_super_admin = False
    
    if request.user.is_authenticated:
        role = get_user_role(request.user)
        if role == "super_admin":
            is_super_admin = True
        else:
            return redirect("account")

    if request.method == "POST":
        form = CidadaoRegistrationForm(request.POST, is_super_admin=is_super_admin)
        if form.is_valid():
            try:
                with transaction.atomic():
                    User = get_user_model()
                    cpf = form.cleaned_data["cpf"]
                    email = form.cleaned_data["email"]
                    password = form.cleaned_data["password"]
                    tipo_usuario = form.cleaned_data.get("tipo_usuario", "cidadao")
                    nome_completo = form.cleaned_data.get("nome_completo")
                    
                    # Cria o usuário Django padrão
                    user = User.objects.create_user(
                        username=cpf,
                        email=email,
                        password=password,
                        first_name=nome_completo
                    )
                    
                    if tipo_usuario == "super_admin":
                        user.is_superuser = True
                        user.is_staff = True
                        user.save()
                        
                    elif tipo_usuario == "ubs_admin":
                        user.is_staff = True
                        user.save()
                        
                        # Vincula o administrador à UBS selecionada
                        ubs = form.cleaned_data["ubs"]
                        UbsAdmin.objects.create(user=user, ubs=ubs)
                        
                    else:  # cidadao
                        # Cria o cidadão vinculado ao usuário
                        cidadao = Cidadao.objects.create(
                            user=user,
                            nome_completo=nome_completo,
                            cpf=cpf,
                            rg_numero=form.cleaned_data["rg_numero"],
                            rg_orgao_emissor=form.cleaned_data["rg_orgao_emissor"],
                            rg_data_expedicao=form.cleaned_data["rg_data_expedicao"],
                            naturalidade=form.cleaned_data["naturalidade"],
                            data_nascimento=form.cleaned_data["data_nascimento"],
                            genero=form.cleaned_data["genero"],
                            cartao_sus=form.cleaned_data["cartao_sus"],
                            whatsapp=form.cleaned_data["whatsapp"],
                        )
                        
                        # Cria o endereço vinculado ao cidadão
                        Endereco.objects.create(
                            cidadao=cidadao,
                            cep=form.cleaned_data["cep"],
                            logradouro=form.cleaned_data["logradouro"],
                            numero=form.cleaned_data["numero"],
                            complemento=form.cleaned_data["complemento"],
                            bairro=form.cleaned_data["bairro"],
                            cidade=form.cleaned_data["cidade"],
                            uf=form.cleaned_data["uf"],
                        )
                
                # Se quem cadastrou for um super_admin, mantém a sessão do super_admin ativa
                if is_super_admin:
                    messages.success(request, f"Usuário {nome_completo} ({tipo_usuario.upper()}) cadastrado com sucesso!")
                    return redirect("home")
                else:
                    # Se for auto-cadastro anônimo, faz login e envia para a página de perfil
                    auth_login(request, user, backend="apps.core.backends.CpfBackend")
                    messages.success(request, "Cadastro realizado com sucesso! Bem-vindo ao Agenda SGA.")
                    return redirect("account")
                
            except Exception as e:
                logger.exception("Erro ao salvar cadastro")
                form.add_error(None, "Ocorreu um erro ao processar o cadastro. Tente novamente.")
    else:
        form = CidadaoRegistrationForm(is_super_admin=is_super_admin)

    context = {
        "form": form,
        "show_global_header": is_super_admin,  # Se for super_admin logado, mantém o shell do dashboard
        "show_global_footer": True,
        "footer_variant": "login" if not is_super_admin else "",
    }
    return render(request, "registration/register.html", context)


@login_required
def cidadao_list(request):
    role = get_user_role(request.user)
    if role not in {"super_admin", "ubs_admin"}:
        messages.error(request, "Acesso negado. Apenas administradores podem visualizar a lista de cidadãos.")
        from apps.logs.utils import registrar_log
        from apps.logs.models import LogAuditoria
        registrar_log(
            categoria=LogAuditoria.Categoria.AUTENTICACAO,
            acao="Tentativa de visualização de lista de cidadãos não autorizada",
            request=request,
            detalhes={"role": role},
        )
        return redirect("home")

    from django.core.paginator import Paginator
    qs = Cidadao.objects.select_related("user", "endereco").all().order_by("nome_completo")

    q = (request.GET.get("q") or "").strip()
    if q:
        digits = "".join(ch for ch in q if ch.isdigit())
        if digits:
            qs = qs.filter(Q(cpf__icontains=digits) | Q(nome_completo__icontains=q))
        else:
            qs = qs.filter(nome_completo__icontains=q)

    total = qs.count()

    paginator = Paginator(qs, 25)
    page_num = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_num)

    context = {
        "role": role,
        "page_obj": page_obj,
        "q": q,
        "total": total,
    }
    return render(request, "core/cidadao_list.html", context)


