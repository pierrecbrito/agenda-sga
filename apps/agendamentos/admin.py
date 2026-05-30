from django.contrib import admin

from .models import VagaAgendamento


@admin.register(VagaAgendamento)
class VagaAgendamentoAdmin(admin.ModelAdmin):
    list_display = (
        "protocolo",
        "ubs",
        "especialidade",
        "data_vaga",
        "dia_semana",
        "hora_inicio",
        "hora_fim",
        "cidadao",
        "status",
        "recorrente",
    )
    search_fields = ("protocolo", "ubs__nome_fantasia", "especialidade__nome", "cidadao__nome_completo")
    list_filter = ("status", "recorrente", "ubs", "especialidade")
    autocomplete_fields = ("ubs", "especialidade", "cidadao")