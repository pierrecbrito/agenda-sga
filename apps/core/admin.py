from django.contrib import admin

from .models import Cidadao, Endereco


@admin.register(Cidadao)
class CidadaoAdmin(admin.ModelAdmin):
    list_display = ("nome_completo", "cpf", "data_nascimento", "genero", "cartao_sus")
    search_fields = ("nome_completo", "cpf", "cartao_sus")
    list_filter = ("genero",)


@admin.register(Endereco)
class EnderecoAdmin(admin.ModelAdmin):
    list_display = ("cidadao", "logradouro", "numero", "bairro", "cidade", "uf")
    search_fields = ("cidadao__nome_completo", "logradouro", "cidade", "uf")