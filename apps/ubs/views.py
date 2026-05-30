from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.agendamentos.models import VagaAgendamento

from .forms import EnderecoUbsForm, UbsForm
from .models import EnderecoUbs, Ubs


def _estado_agendamento(qs):
    hoje = timezone.localdate()
    return {
        "total": qs.count(),
        "confirmadas": qs.filter(status=VagaAgendamento.Status.CONFIRMADO).count(),
        "executadas": qs.filter(status=VagaAgendamento.Status.EXECUTADO).count(),
        "canceladas": qs.filter(status__in=[VagaAgendamento.Status.CANCELADO_PACIENTE, VagaAgendamento.Status.CANCELADO_UBS]).count(),
        "faltas": qs.filter(status=VagaAgendamento.Status.FALTA).count(),
        "agendamentos_vinculados": qs.filter(cidadao__isnull=False).count(),
        "proximas": qs.filter(data_vaga__gte=hoje).count(),
    }


@login_required
def index(request):
    ubs_queryset = (
        Ubs.objects.select_related("endereco")
        .annotate(
            total_vagas=Count("vagas_agendamento", distinct=True),
            vagas_confirmadas=Count("vagas_agendamento", filter=Q(vagas_agendamento__status=VagaAgendamento.Status.CONFIRMADO), distinct=True),
            vagas_executadas=Count("vagas_agendamento", filter=Q(vagas_agendamento__status=VagaAgendamento.Status.EXECUTADO), distinct=True),
        )
        .order_by("nome_fantasia")
    )

    total_com_endereco = EnderecoUbs.objects.count()
    total_com_agendamento_online = ubs_queryset.filter(permite_agendamento_online=True).count()
    total_vagas_confirmadas = VagaAgendamento.objects.filter(status=VagaAgendamento.Status.CONFIRMADO).count()

    ubs_dialog_data = []
    for ubs in ubs_queryset:
        endereco = getattr(ubs, "endereco", None)
        ubs_dialog_data.append(
            {
                "pk": ubs.pk,
                "cnes": ubs.cnes,
                "cnpj": ubs.cnpj,
                "nome_fantasia": ubs.nome_fantasia,
                "razao_social": ubs.razao_social,
                "distrito_sanitario": ubs.distrito_sanitario,
                "telefone": ubs.telefone,
                "email": ubs.email,
                "horario_abertura": ubs.horario_abertura.strftime("%H:%M"),
                "horario_fechamento": ubs.horario_fechamento.strftime("%H:%M"),
                "permite_agendamento_online": ubs.permite_agendamento_online,
                "antecedencia_maxima_dias": ubs.antecedencia_maxima_dias,
                "total_vagas": ubs.total_vagas,
                "vagas_confirmadas": ubs.vagas_confirmadas,
                "vagas_executadas": ubs.vagas_executadas,
                "especialidades": list(ubs.especialidades.values_list("id", flat=True)),
                "endereco": {
                    "cep": endereco.cep if endereco else "",
                    "logradouro": endereco.logradouro if endereco else "",
                    "numero": endereco.numero if endereco else "",
                    "complemento": endereco.complemento if endereco else "",
                    "bairro": endereco.bairro if endereco else "",
                    "cidade": endereco.cidade if endereco else "",
                    "uf": endereco.uf if endereco else "",
                    "latitude": float(endereco.latitude) if endereco and endereco.latitude is not None else None,
                    "longitude": float(endereco.longitude) if endereco and endereco.longitude is not None else None,
                },
            }
        )

    return render(
        request,
        "ubs/ubs_list.html",
        {
            "ubs_list": ubs_queryset,
            "ubs_form": UbsForm(prefix="ubs"),
            "endereco_form": EnderecoUbsForm(prefix="endereco"),
            "ubs_dialog_data": ubs_dialog_data,
            "stats": {
                "total_ubs": ubs_queryset.count(),
                "total_com_endereco": total_com_endereco,
                "total_com_agendamento_online": total_com_agendamento_online,
                "total_vagas_confirmadas": total_vagas_confirmadas,
            },
        },
    )


@login_required
def detail(request, pk):
    ubs = get_object_or_404(
        Ubs.objects.select_related("endereco").prefetch_related("especialidades"),
        pk=pk,
    )
    vagas = VagaAgendamento.objects.select_related("especialidade", "cidadao").filter(ubs=ubs).order_by("-data_vaga", "-hora_inicio")
    stats = _estado_agendamento(vagas)
    recentes = vagas[:8]

    return render(
        request,
        "ubs/ubs_detail.html",
        {
            "ubs": ubs,
            "stats": stats,
            "recentes": recentes,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def create(request):
    endereco_instance = None
    if request.method == "POST":
        ubs_form = UbsForm(request.POST, prefix="ubs")
        endereco_form = EnderecoUbsForm(request.POST, prefix="endereco")
        if ubs_form.is_valid() and endereco_form.is_valid():
            ubs = ubs_form.save(commit=False)
            ubs.save()
            ubs_form.save_m2m()

            endereco = endereco_form.save(commit=False)
            endereco.ubs = ubs
            endereco.save()

            messages.success(request, "UBS cadastrada com sucesso.")
            return redirect("ubs:detail", pk=ubs.pk)
    else:
        ubs_form = UbsForm(prefix="ubs")
        endereco_form = EnderecoUbsForm(prefix="endereco")

    return render(
        request,
        "ubs/ubs_form.html",
        {
            "form_mode": "create",
            "ubs_form": ubs_form,
            "endereco_form": endereco_form,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def update(request, pk):
    ubs = get_object_or_404(Ubs, pk=pk)
    endereco_instance = getattr(ubs, "endereco", None)

    if request.method == "POST":
        ubs_form = UbsForm(request.POST, prefix="ubs", instance=ubs)
        endereco_form = EnderecoUbsForm(request.POST, prefix="endereco", instance=endereco_instance)
        if ubs_form.is_valid() and endereco_form.is_valid():
            ubs = ubs_form.save(commit=False)
            ubs.save()
            ubs_form.save_m2m()

            endereco = endereco_form.save(commit=False)
            endereco.ubs = ubs
            endereco.save()

            messages.success(request, "UBS atualizada com sucesso.")
            return redirect("ubs:detail", pk=ubs.pk)
    else:
        ubs_form = UbsForm(prefix="ubs", instance=ubs)
        endereco_form = EnderecoUbsForm(prefix="endereco", instance=endereco_instance)

    return render(
        request,
        "ubs/ubs_form.html",
        {
            "form_mode": "update",
            "ubs": ubs,
            "ubs_form": ubs_form,
            "endereco_form": endereco_form,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def delete(request, pk):
    ubs = get_object_or_404(Ubs, pk=pk)

    if request.method == "POST":
        nome = ubs.nome_fantasia
        ubs.delete()
        messages.success(request, f"UBS {nome} excluída com sucesso.")
        return redirect("ubs:index")

    return render(
        request,
        "ubs/ubs_confirm_delete.html",
        {
            "ubs": ubs,
        },
    )