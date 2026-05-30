from django.shortcuts import render

from .models import VagaAgendamento


def vagas_disponiveis(request):
    especialidade_id = request.GET.get("especialidade")
    vagas = (
        VagaAgendamento.objects.select_related("ubs", "especialidade", "cidadao")
        .filter(cidadao__isnull=True, status=VagaAgendamento.Status.CONFIRMADO)
        .order_by("data_vaga", "hora_inicio")
    )

    if especialidade_id:
        vagas = vagas.filter(especialidade_id=especialidade_id)

    especialidades = (
        VagaAgendamento.objects.select_related("especialidade")
        .filter(cidadao__isnull=True, status=VagaAgendamento.Status.CONFIRMADO)
        .values_list("especialidade__id", "especialidade__nome")
        .distinct()
        .order_by("especialidade__nome")
    )

    return render(
        request,
        "agendamentos/vagas_disponiveis.html",
        {
            "vagas": vagas,
            "especialidades": especialidades,
            "especialidade_selecionada": especialidade_id,
        },
    )