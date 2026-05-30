from django.contrib import admin

from .models import Cidadao, Endereco


@admin.register(Cidadao)
class CidadaoAdmin(admin.ModelAdmin):
    list_display = (
        "nome_completo",
        "cpf",
        "rg_numero",
        "rg_data_expedicao",
        "naturalidade",
        "data_nascimento",
        "genero",
        "cartao_sus",
    )
    search_fields = ("nome_completo", "cpf", "rg_numero", "cartao_sus", "naturalidade")
    list_filter = ("genero",)


@admin.register(Endereco)
class EnderecoAdmin(admin.ModelAdmin):
    list_display = ("cidadao", "logradouro", "numero", "bairro", "cidade", "uf")
    search_fields = ("cidadao__nome_completo", "logradouro", "cidade", "uf")