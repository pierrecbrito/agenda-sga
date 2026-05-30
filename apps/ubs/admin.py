from django.contrib import admin

from .models import EnderecoUbs, Ubs


@admin.register(Ubs)
class UbsAdmin(admin.ModelAdmin):
    list_display = (
        "nome_fantasia",
        "razao_social",
        "cnes",
        "cnpj",
        "distrito_sanitario",
        "telefone",
        "email",
        "horario_abertura",
        "horario_fechamento",
        "permite_agendamento_online",
        "antecedencia_maxima_dias",
    )
    search_fields = ("nome_fantasia", "razao_social", "cnes", "cnpj", "distrito_sanitario")
    list_filter = ("permite_agendamento_online", "distrito_sanitario")


@admin.register(EnderecoUbs)
class EnderecoUbsAdmin(admin.ModelAdmin):
    list_display = ("ubs", "logradouro", "numero", "bairro", "cidade", "uf")
    search_fields = ("ubs__nome_fantasia", "logradouro", "cidade", "uf")