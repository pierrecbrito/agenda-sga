from django.urls import path

from .views import (
    cancel, create, update, vagas_disponiveis,
    fila_controle, fila_chamar, fila_concluir, fila_falta, fila_rechamar,
    fila_painel, fila_painel_api, fila_acompanhar, fila_acompanhar_api
)

urlpatterns = [
    path("", vagas_disponiveis, name="vagas_disponiveis"),
    path("novo/", create, name="agendamento_create"),
    path("<int:pk>/editar/", update, name="agendamento_update"),
    path("<int:pk>/cancelar/", cancel, name="agendamento_cancel"),
    
    # Fila de chamadas
    path("fila/", fila_controle, name="fila_controle"),
    path("fila/chamar/<int:vaga_id>/", fila_chamar, name="fila_chamar"),
    path("fila/concluir/<int:vaga_id>/", fila_concluir, name="fila_concluir"),
    path("fila/falta/<int:vaga_id>/", fila_falta, name="fila_falta"),
    path("fila/rechamar/<int:vaga_id>/", fila_rechamar, name="fila_rechamar"),
    path("fila/painel/<int:ubs_id>/", fila_painel, name="fila_painel"),
    path("fila/painel/api/<int:ubs_id>/", fila_painel_api, name="fila_painel_api"),
    path("fila/acompanhar/", fila_acompanhar, name="fila_acompanhar"),
    path("fila/acompanhar/api/", fila_acompanhar_api, name="fila_acompanhar_api"),
]