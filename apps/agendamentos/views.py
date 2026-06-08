from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.urls import reverse

from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from apps.core.access import get_user_role
from apps.core.models import Cidadao, UbsAdmin
from apps.ubs.models import Especialidade, Ubs

from .forms import AgendamentoAdminForm, AgendamentoCidadaoForm, AgendamentoFilterForm
from .models import VagaAgendamento

from apps.logs.utils import registrar_log
from apps.logs.models import LogAuditoria


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _somente_digitos(valor):
    return "".join(ch for ch in valor if ch.isdigit())


def _buscar_cidadao(termo):
    termo = (termo or "").strip()
    if not termo:
        return None, "Informe o CPF ou nome do cidadão."

    digits = _somente_digitos(termo)
    qs = Cidadao.objects.all()
    if digits:
        qs = qs.filter(Q(cpf__icontains=digits) | Q(nome_completo__icontains=termo))
    else:
        qs = qs.filter(nome_completo__icontains=termo)

    total = qs.count()
    if total == 1:
        return qs.first(), None
    if total == 0:
        return None, "Nenhum cidadão encontrado com esse CPF ou nome."
    return None, "Mais de um cidadão encontrado. Informe o CPF completo."


def _get_allowed_ubs(user, role):
    """Retorna o queryset de UBSs que o usuário pode visualizar/gerenciar."""
    if role == "super_admin":
        return Ubs.objects.all()
    if role == "ubs_admin":
        return Ubs.objects.filter(admins__user=user)
    # Cidadão: apenas UBSs com agendamento online habilitado
    return Ubs.objects.filter(permite_agendamento_online=True)


def _resolve_cadastro_window(data_vaga, hora_inicio):
    if not data_vaga or not hora_inicio:
        return timezone.now(), timezone.now() + timedelta(hours=1)

    target = datetime.combine(data_vaga, hora_inicio)
    aware_target = timezone.make_aware(target)
    now = timezone.now()

    if aware_target <= now:
        return aware_target - timedelta(hours=1), aware_target
    return now, aware_target


def _can_manage_agendamento(user, role, agendamento, allowed_ubs):
    if role == "super_admin":
        return True
    if role == "ubs_admin":
        return allowed_ubs.filter(pk=agendamento.ubs_id).exists()
    if role == "cidadao" and hasattr(user, "cidadao"):
        return agendamento.cidadao_id == user.cidadao.pk
    return False


def _is_status_final(status):
    """Retorna True se o status não permite mais edição/cancelamento."""
    return status in {
        VagaAgendamento.Status.EXECUTADO,
        VagaAgendamento.Status.FALTA,
        VagaAgendamento.Status.CANCELADO_PACIENTE,
        VagaAgendamento.Status.CANCELADO_UBS,
    }


def _base_queryset(role, user, allowed_ubs):
    qs = VagaAgendamento.objects.select_related("ubs", "especialidade", "cidadao").order_by(
        "-data_vaga", "-hora_inicio"
    )

    if role == "cidadao" and hasattr(user, "cidadao"):
        return qs.filter(cidadao=user.cidadao)
    if role == "ubs_admin":
        return qs.filter(ubs__in=allowed_ubs)
    if role == "super_admin":
        return qs
    return qs.none()


def _calcular_metricas(qs):
    """Agrega contagens de status para exibição no painel."""
    agg = qs.aggregate(
        total=Count("pk"),
        confirmados=Count("pk", filter=Q(status=VagaAgendamento.Status.CONFIRMADO)),
        executados=Count("pk", filter=Q(status=VagaAgendamento.Status.EXECUTADO)),
        faltas=Count("pk", filter=Q(status=VagaAgendamento.Status.FALTA)),
        cancelados_paciente=Count("pk", filter=Q(status=VagaAgendamento.Status.CANCELADO_PACIENTE)),
        cancelados_ubs=Count("pk", filter=Q(status=VagaAgendamento.Status.CANCELADO_UBS)),
    )
    agg["cancelados"] = agg["cancelados_paciente"] + agg["cancelados_ubs"]
    return agg


def _build_context(
    request,
    agendamentos,
    allowed_ubs,
    role,
    *,
    create_form=None,
    edit_form=None,
    open_create=False,
    open_edit_pk=None,
):
    especialidades = Especialidade.objects.filter(ubs__in=allowed_ubs).distinct().order_by("nome")
    filter_form = AgendamentoFilterForm(
        request.GET or None,
        ubs_queryset=allowed_ubs,
        especialidade_queryset=especialidades,
    )

    if filter_form.is_valid():
        cleaned = filter_form.cleaned_data
        if cleaned.get("ubs"):
            agendamentos = agendamentos.filter(ubs=cleaned["ubs"])
        if cleaned.get("especialidade"):
            agendamentos = agendamentos.filter(especialidade=cleaned["especialidade"])
        if cleaned.get("data_inicio"):
            agendamentos = agendamentos.filter(data_vaga__gte=cleaned["data_inicio"])
        if cleaned.get("data_fim"):
            agendamentos = agendamentos.filter(data_vaga__lte=cleaned["data_fim"])
        if cleaned.get("status"):
            agendamentos = agendamentos.filter(status=cleaned["status"])
        if cleaned.get("cidadao_busca") and role in {"super_admin", "ubs_admin"}:
            termo = cleaned["cidadao_busca"]
            digits = _somente_digitos(termo)
            agendamentos = agendamentos.filter(
                Q(cidadao__cpf__icontains=digits) | Q(cidadao__nome_completo__icontains=termo)
            )

    form_class = AgendamentoAdminForm if role in {"super_admin", "ubs_admin"} else AgendamentoCidadaoForm
    create_form = create_form or form_class(
        prefix="create", ubs_queryset=allowed_ubs, especialidade_queryset=especialidades
    )
    edit_form = edit_form or form_class(
        prefix="edit", ubs_queryset=allowed_ubs, especialidade_queryset=especialidades
    )

    # Calcula métricas do queryset filtrado
    metricas = _calcular_metricas(agendamentos)

    # Paginação dos agendamentos
    from django.core.paginator import Paginator
    paginator = Paginator(agendamentos, 25)
    page_num = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_num)

    # Serializa dados para o JS dos dialogs (apenas os itens da página atual)
    agendamentos_data = []
    for ag in page_obj:
        agendamentos_data.append(
            {
                "pk": ag.pk,
                "ubs_id": ag.ubs_id,
                "especialidade_id": ag.especialidade_id,
                "status": ag.status,
                "status_final": _is_status_final(ag.status),
                "cidadao": {
                    "id": ag.cidadao_id,
                    "nome": ag.cidadao.nome_completo if ag.cidadao else "",
                    "cpf": ag.cidadao.cpf if ag.cidadao else "",
                },
                "data_vaga": ag.data_vaga.isoformat() if ag.data_vaga else "",
                "hora_inicio": ag.hora_inicio.strftime("%H:%M"),
                "hora_fim": ag.hora_fim.strftime("%H:%M"),
            }
        )

    return {
        "agendamentos": page_obj,
        "agendamentos_data": agendamentos_data,
        "filter_form": filter_form,
        "create_form": create_form,
        "edit_form": edit_form,
        "open_create_dialog": open_create,
        "open_edit_pk": open_edit_pk,
        "role": role,
        "metricas": metricas,
        "status_choices": VagaAgendamento.Status.choices,
    }


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

@login_required
def vagas_disponiveis(request):
    role = get_user_role(request.user)
    allowed_ubs = _get_allowed_ubs(request.user, role)
    agendamentos = _base_queryset(role, request.user, allowed_ubs)

    context = _build_context(request, agendamentos, allowed_ubs, role)
    return render(request, "agendamentos/vagas_disponiveis.html", context)


@login_required
def create(request):
    role = get_user_role(request.user)
    allowed_ubs = _get_allowed_ubs(request.user, role)
    especialidades = Especialidade.objects.filter(ubs__in=allowed_ubs).distinct().order_by("nome")
    form_class = AgendamentoAdminForm if role in {"super_admin", "ubs_admin"} else AgendamentoCidadaoForm

    if role not in {"super_admin", "ubs_admin", "cidadao"}:
        messages.error(request, "Você não tem permissão para criar agendamentos.")
        return redirect("vagas_disponiveis")

    form = form_class(
        request.POST or None,
        prefix="create",
        ubs_queryset=allowed_ubs,
        especialidade_queryset=especialidades,
    )

    if request.method == "POST" and form.is_valid():
        agendamento = form.save(commit=False)

        if role in {"super_admin", "ubs_admin"}:
            cidadao, erro = _buscar_cidadao(form.cleaned_data.get("cidadao_busca"))
            if erro:
                form.add_error("cidadao_busca", erro)
            else:
                agendamento.cidadao = cidadao
        else:
            if not hasattr(request.user, "cidadao"):
                form.add_error(None, "Seu usuário não está vinculado a um cidadão.")
            else:
                agendamento.cidadao = request.user.cidadao

        if not form.errors:
            agendamento.status = VagaAgendamento.Status.CONFIRMADO
            agendamento.cadastro_abre_em, agendamento.cadastro_fecha_em = _resolve_cadastro_window(
                agendamento.data_vaga,
                agendamento.hora_inicio,
            )
            agendamento.save()
            registrar_log(
                categoria=LogAuditoria.Categoria.AGENDAMENTO,
                acao="Agendamento criado",
                request=request,
                detalhes={
                    "protocolo": agendamento.protocolo,
                    "ubs": agendamento.ubs.nome_fantasia,
                    "especialidade": agendamento.especialidade.nome,
                    "data_vaga": str(agendamento.data_vaga) if agendamento.data_vaga else None,
                    "hora_inicio": agendamento.hora_inicio.strftime("%H:%M"),
                    "cidadao": agendamento.cidadao.nome_completo if agendamento.cidadao else None,
                },
            )
            messages.success(request, "Agendamento criado com sucesso.")
            return redirect("vagas_disponiveis")

    agendamentos = _base_queryset(role, request.user, allowed_ubs)
    context = _build_context(request, agendamentos, allowed_ubs, role, create_form=form, open_create=True)
    return render(request, "agendamentos/vagas_disponiveis.html", context)


@login_required
def update(request, pk):
    role = get_user_role(request.user)
    allowed_ubs = _get_allowed_ubs(request.user, role)
    agendamento = get_object_or_404(VagaAgendamento, pk=pk)

    if not _can_manage_agendamento(request.user, role, agendamento, allowed_ubs):
        messages.error(request, "Você não tem permissão para editar este agendamento.")
        return redirect("vagas_disponiveis")

    # Cidadão não pode editar agendamento com status final
    if role == "cidadao" and _is_status_final(agendamento.status):
        messages.error(request, "Este agendamento não pode mais ser editado.")
        return redirect("vagas_disponiveis")

    especialidades = Especialidade.objects.filter(ubs__in=allowed_ubs).distinct().order_by("nome")
    form_class = AgendamentoAdminForm if role in {"super_admin", "ubs_admin"} else AgendamentoCidadaoForm
    form = form_class(
        request.POST or None,
        prefix="edit",
        instance=agendamento,
        ubs_queryset=allowed_ubs,
        especialidade_queryset=especialidades,
    )

    if request.method == "POST" and form.is_valid():
        agendamento_editado = form.save(commit=False)

        if role in {"super_admin", "ubs_admin"}:
            busca = form.cleaned_data.get("cidadao_busca")
            if busca:
                cidadao, erro = _buscar_cidadao(busca)
                if erro:
                    form.add_error("cidadao_busca", erro)
                else:
                    agendamento_editado.cidadao = cidadao

            # Admins podem atualizar o status diretamente
            novo_status = form.cleaned_data.get("status")
            if novo_status:
                agendamento_editado.status = novo_status
        else:
            agendamento_editado.cidadao = request.user.cidadao

        if not form.errors:
            agendamento_editado.cadastro_abre_em, agendamento_editado.cadastro_fecha_em = _resolve_cadastro_window(
                agendamento_editado.data_vaga,
                agendamento_editado.hora_inicio,
            )
            agendamento_editado.save()
            registrar_log(
                categoria=LogAuditoria.Categoria.AGENDAMENTO,
                acao="Agendamento editado",
                request=request,
                detalhes={
                    "protocolo": agendamento_editado.protocolo,
                    "ubs": agendamento_editado.ubs.nome_fantasia,
                    "especialidade": agendamento_editado.especialidade.nome,
                    "data_vaga": str(agendamento_editado.data_vaga) if agendamento_editado.data_vaga else None,
                    "status_novo": agendamento_editado.status,
                    "cidadao": agendamento_editado.cidadao.nome_completo if agendamento_editado.cidadao else None,
                },
            )
            messages.success(request, "Agendamento atualizado com sucesso.")
            return redirect("vagas_disponiveis")

    # Erro: reabre o dialog de edição com o pk correto
    agendamentos = _base_queryset(role, request.user, allowed_ubs)
    context = _build_context(
        request, agendamentos, allowed_ubs, role, edit_form=form, open_edit_pk=pk
    )
    return render(request, "agendamentos/vagas_disponiveis.html", context)


@login_required
def cancel(request, pk):
    role = get_user_role(request.user)
    allowed_ubs = _get_allowed_ubs(request.user, role)
    agendamento = get_object_or_404(VagaAgendamento, pk=pk)

    if not _can_manage_agendamento(request.user, role, agendamento, allowed_ubs):
        messages.error(request, "Você não tem permissão para cancelar este agendamento.")
        return redirect("vagas_disponiveis")

    # Bloqueia cancelamento de agendamentos já finalizados
    if _is_status_final(agendamento.status):
        messages.error(request, "Este agendamento já foi finalizado e não pode ser cancelado.")
        return redirect("vagas_disponiveis")

    if request.method == "POST":
        status_anterior = agendamento.status
        if role == "cidadao":
            agendamento.status = VagaAgendamento.Status.CANCELADO_PACIENTE
        else:
            agendamento.status = VagaAgendamento.Status.CANCELADO_UBS
        agendamento.save()
        registrar_log(
            categoria=LogAuditoria.Categoria.AGENDAMENTO,
            acao="Agendamento cancelado",
            request=request,
            detalhes={
                "protocolo": agendamento.protocolo,
                "ubs": agendamento.ubs.nome_fantasia,
                "especialidade": agendamento.especialidade.nome,
                "status_anterior": status_anterior,
                "status_novo": agendamento.status,
                "cidadao": agendamento.cidadao.nome_completo if agendamento.cidadao else None,
            },
        )
        messages.info(request, "Agendamento cancelado.")
        return redirect("vagas_disponiveis")

    return redirect("vagas_disponiveis")


# ---------------------------------------------------------------------------
# Fila de Chamada / Painel Views
# ---------------------------------------------------------------------------

@login_required
def fila_controle(request):
    role = get_user_role(request.user)
    if role not in {"super_admin", "ubs_admin"}:
        messages.error(request, "Acesso negado. Apenas administradores podem gerenciar a fila.")
        return redirect("home")

    # Get allowed UBSs
    allowed_ubs = _get_allowed_ubs(request.user, role)
    
    # Selected UBS filter
    ubs_id = request.GET.get("ubs")
    if ubs_id:
        selected_ubs = get_object_or_404(allowed_ubs, pk=ubs_id)
    else:
        selected_ubs = allowed_ubs.first()

    # Get specialties for filtering
    specialties = Especialidade.objects.none()
    selected_specialty_id = request.GET.get("especialidade")
    selected_specialty = None
    if selected_ubs:
        specialties = selected_ubs.especialidades.all().order_by("nome")
        if selected_specialty_id:
            selected_specialty = get_object_or_404(specialties, pk=selected_specialty_id)

    hoje = timezone.localdate()
    
    # Query for appointments of today at the selected UBS
    vagas_hoje = VagaAgendamento.objects.filter(
        ubs=selected_ubs,
        data_vaga=hoje,
        cidadao__isnull=False
    ).select_related("cidadao", "especialidade")

    if selected_specialty:
        vagas_hoje = vagas_hoje.filter(especialidade=selected_specialty)

    # Active chamado
    vaga_chamada = vagas_hoje.filter(status=VagaAgendamento.Status.CHAMADO).order_by("-chamado_em").first()

    # Waiting (status = CONFIRMADO)
    proximos = vagas_hoje.filter(status=VagaAgendamento.Status.CONFIRMADO).order_by("hora_inicio")

    # Metrics
    total_aguardando = vagas_hoje.filter(status=VagaAgendamento.Status.CONFIRMADO).count()
    total_atendidos = vagas_hoje.filter(status=VagaAgendamento.Status.EXECUTADO).count()
    total_faltas = vagas_hoje.filter(status=VagaAgendamento.Status.FALTA).count()

    context = {
        "role": role,
        "allowed_ubs": allowed_ubs,
        "selected_ubs": selected_ubs,
        "specialties": specialties,
        "selected_specialty": selected_specialty,
        "vaga_chamada": vaga_chamada,
        "proximos": proximos,
        "total_aguardando": total_aguardando,
        "total_atendidos": total_atendidos,
        "total_faltas": total_faltas,
    }
    return render(request, "agendamentos/fila_controle.html", context)


@login_required
@require_POST
def fila_chamar(request, vaga_id):
    from django.db import transaction
    role = get_user_role(request.user)
    if role not in {"super_admin", "ubs_admin"}:
        return HttpResponseForbidden("Acesso negado.")

    allowed_ubs = _get_allowed_ubs(request.user, role)
    vaga = get_object_or_404(VagaAgendamento, pk=vaga_id, ubs__in=allowed_ubs)

    with transaction.atomic():
        # Auto-concluir outro paciente CHAMADO na mesma UBS e especialidade
        outras_chamadas = VagaAgendamento.objects.filter(
            ubs=vaga.ubs,
            especialidade=vaga.especialidade,
            data_vaga=timezone.localdate(),
            status=VagaAgendamento.Status.CHAMADO
        )
        for v in outras_chamadas:
            v.status = VagaAgendamento.Status.EXECUTADO
            v.save()

        vaga.status = VagaAgendamento.Status.CHAMADO
        vaga.chamado_em = timezone.now()
        vaga.save()

    registrar_log(
        categoria=LogAuditoria.Categoria.AGENDAMENTO,
        acao="Paciente chamado para atendimento",
        request=request,
        detalhes={
            "vaga_id": vaga.pk,
            "senha": vaga.senha_atendimento,
            "paciente": vaga.cidadao.nome_completo if vaga.cidadao else None,
            "ubs": vaga.ubs.nome_fantasia,
            "especialidade": vaga.especialidade.nome,
        }
    )

    messages.success(request, f"Paciente {vaga.cidadao.nome_completo} chamado com sucesso.")
    
    redirect_url = f"{reverse('fila_controle')}?ubs={vaga.ubs.pk}"
    if request.GET.get("especialidade"):
        redirect_url += f"&especialidade={request.GET.get('especialidade')}"
    return redirect(redirect_url)


@login_required
@require_POST
def fila_concluir(request, vaga_id):
    from django.db import transaction
    role = get_user_role(request.user)
    if role not in {"super_admin", "ubs_admin"}:
        return HttpResponseForbidden("Acesso negado.")

    allowed_ubs = _get_allowed_ubs(request.user, role)
    vaga = get_object_or_404(VagaAgendamento, pk=vaga_id, ubs__in=allowed_ubs)

    with transaction.atomic():
        vaga.status = VagaAgendamento.Status.EXECUTADO
        vaga.save()

    registrar_log(
        categoria=LogAuditoria.Categoria.AGENDAMENTO,
        acao="Atendimento concluído",
        request=request,
        detalhes={
            "vaga_id": vaga.pk,
            "senha": vaga.senha_atendimento,
            "paciente": vaga.cidadao.nome_completo if vaga.cidadao else None,
        }
    )

    messages.success(request, f"Atendimento de {vaga.cidadao.nome_completo} concluído.")
    
    redirect_url = f"{reverse('fila_controle')}?ubs={vaga.ubs.pk}"
    if request.GET.get("especialidade"):
        redirect_url += f"&especialidade={request.GET.get('especialidade')}"
    return redirect(redirect_url)


@login_required
@require_POST
def fila_falta(request, vaga_id):
    from django.db import transaction
    role = get_user_role(request.user)
    if role not in {"super_admin", "ubs_admin"}:
        return HttpResponseForbidden("Acesso negado.")

    allowed_ubs = _get_allowed_ubs(request.user, role)
    vaga = get_object_or_404(VagaAgendamento, pk=vaga_id, ubs__in=allowed_ubs)

    with transaction.atomic():
        vaga.status = VagaAgendamento.Status.FALTA
        vaga.save()

    registrar_log(
        categoria=LogAuditoria.Categoria.AGENDAMENTO,
        acao="Registrada falta do paciente",
        request=request,
        detalhes={
            "vaga_id": vaga.pk,
            "senha": vaga.senha_atendimento,
            "paciente": vaga.cidadao.nome_completo if vaga.cidadao else None,
        }
    )

    messages.warning(request, f"Registrada falta para {vaga.cidadao.nome_completo}.")
    
    redirect_url = f"{reverse('fila_controle')}?ubs={vaga.ubs.pk}"
    if request.GET.get("especialidade"):
        redirect_url += f"&especialidade={request.GET.get('especialidade')}"
    return redirect(redirect_url)


@login_required
@require_POST
def fila_rechamar(request, vaga_id):
    from django.db import transaction
    role = get_user_role(request.user)
    if role not in {"super_admin", "ubs_admin"}:
        return HttpResponseForbidden("Acesso negado.")

    allowed_ubs = _get_allowed_ubs(request.user, role)
    vaga = get_object_or_404(VagaAgendamento, pk=vaga_id, ubs__in=allowed_ubs)

    with transaction.atomic():
        vaga.chamado_em = timezone.now()
        vaga.save()

    registrar_log(
        categoria=LogAuditoria.Categoria.AGENDAMENTO,
        acao="Paciente chamado novamente (rechamar)",
        request=request,
        detalhes={
            "vaga_id": vaga.pk,
            "senha": vaga.senha_atendimento,
            "paciente": vaga.cidadao.nome_completo if vaga.cidadao else None,
        }
    )

    messages.info(request, f"Rechamado: {vaga.cidadao.nome_completo}.")
    
    redirect_url = f"{reverse('fila_controle')}?ubs={vaga.ubs.pk}"
    if request.GET.get("especialidade"):
        redirect_url += f"&especialidade={request.GET.get('especialidade')}"
    return redirect(redirect_url)


@login_required
def fila_painel(request, ubs_id):
    role = get_user_role(request.user)
    if role not in {"super_admin", "ubs_admin"}:
        return HttpResponseForbidden("Acesso negado.")
    allowed_ubs = _get_allowed_ubs(request.user, role)
    ubs = get_object_or_404(allowed_ubs, pk=ubs_id)
    
    context = {
        "ubs": ubs,
        "show_global_header": False,
        "show_global_footer": False,
    }
    return render(request, "agendamentos/fila_painel.html", context)


@login_required
def fila_painel_api(request, ubs_id):
    role = get_user_role(request.user)
    if role not in {"super_admin", "ubs_admin"}:
        return HttpResponseForbidden("Acesso negado.")
    allowed_ubs = _get_allowed_ubs(request.user, role)
    ubs = get_object_or_404(allowed_ubs, pk=ubs_id)
    hoje = timezone.localdate()
    
    # Find all appointments of the day at this UBS
    vagas_dia = VagaAgendamento.objects.filter(
        ubs=ubs,
        data_vaga=hoje,
        cidadao__isnull=False
    ).select_related("cidadao", "especialidade")
    
    # Active chamado (status=CHAMADO) sorted by chamado_em descending
    vaga_ativa = vagas_dia.filter(status=VagaAgendamento.Status.CHAMADO).order_by("-chamado_em").first()
    
    # History (called today, but not active, sorted by called timestamp)
    historico_vagas = vagas_dia.filter(
        chamado_em__isnull=False
    ).exclude(
        pk=vaga_ativa.pk if vaga_ativa else -1
    ).order_by("-chamado_em")[:5]
    
    active_data = None
    if vaga_ativa:
        active_data = {
            "id": vaga_ativa.pk,
            "paciente": vaga_ativa.cidadao.nome_completo,
            "senha": vaga_ativa.senha_atendimento,
            "especialidade": vaga_ativa.especialidade.nome,
            "chamado_em": vaga_ativa.chamado_em.isoformat() if vaga_ativa.chamado_em else "",
        }
        
    history_list = []
    for h in historico_vagas:
        history_list.append({
            "id": h.pk,
            "paciente": h.cidadao.nome_completo,
            "senha": h.senha_atendimento,
            "especialidade": h.especialidade.nome,
            "status": h.get_status_display(),
            "chamado_em": h.chamado_em.isoformat() if h.chamado_em else "",
        })
        
    return JsonResponse({
        "active": active_data,
        "history": history_list
    })


@login_required
def fila_acompanhar(request):
    role = get_user_role(request.user)
    if role != "cidadao" or not hasattr(request.user, "cidadao"):
        messages.error(request, "Apenas cidadãos podem acompanhar suas filas.")
        return redirect("home")
        
    hoje = timezone.localdate()
    # Find any today's appointment (CONFIRMADO or CHAMADO) for this citizen
    agendamento = VagaAgendamento.objects.filter(
        cidadao=request.user.cidadao,
        data_vaga=hoje,
        status__in=[VagaAgendamento.Status.CONFIRMADO, VagaAgendamento.Status.CHAMADO]
    ).select_related("ubs", "especialidade").first()
    
    context = {
        "agendamento": agendamento,
    }
    return render(request, "agendamentos/fila_acompanhar.html", context)


@login_required
def fila_acompanhar_api(request):
    role = get_user_role(request.user)
    if role != "cidadao" or not hasattr(request.user, "cidadao"):
        return JsonResponse({"error": "Acesso negado."}, status=403)
        
    hoje = timezone.localdate()
    agendamento = VagaAgendamento.objects.filter(
        cidadao=request.user.cidadao,
        data_vaga=hoje,
        status__in=[VagaAgendamento.Status.CONFIRMADO, VagaAgendamento.Status.CHAMADO]
    ).select_related("ubs", "especialidade").first()
    
    if not agendamento:
        return JsonResponse({"ativo": False})
        
    if agendamento.status == VagaAgendamento.Status.CHAMADO:
        return JsonResponse({
            "ativo": True,
            "status": agendamento.status,
            "senha": agendamento.senha_atendimento,
            "especialidade": agendamento.especialidade.nome,
            "ubs": agendamento.ubs.nome_fantasia,
            "posicao": 0,
            "pessoas_na_frente": 0,
            "estimativa_minutos": 0,
        })
        
    # Queue position: count of confirmed appointments of today with earlier start time
    vagas_frente = VagaAgendamento.objects.filter(
        ubs=agendamento.ubs,
        especialidade=agendamento.especialidade,
        data_vaga=hoje,
        status=VagaAgendamento.Status.CONFIRMADO,
        hora_inicio__lt=agendamento.hora_inicio
    )
    
    pessoas_na_frente = vagas_frente.count()
    posicao = pessoas_na_frente + 1
    
    # Estimativa de tempo baseada na duração real configurada das vagas anteriores
    estimativa_minutos = 0
    for v in vagas_frente:
        if v.hora_inicio and v.hora_fim:
            duracao = (datetime.combine(hoje, v.hora_fim) - datetime.combine(hoje, v.hora_inicio)).total_seconds() / 60
            estimativa_minutos += int(max(duracao, 1))
        else:
            estimativa_minutos += 15  # Fallback padrão de 15 minutos
    
    return JsonResponse({
        "ativo": True,
        "status": agendamento.status,
        "senha": agendamento.senha_atendimento,
        "especialidade": agendamento.especialidade.nome,
        "ubs": agendamento.ubs.nome_fantasia,
        "posicao": posicao,
        "pessoas_na_frente": pessoas_na_frente,
        "estimativa_minutos": estimativa_minutos,
        "hora_inicio": agendamento.hora_inicio.strftime("%H:%M"),
    })