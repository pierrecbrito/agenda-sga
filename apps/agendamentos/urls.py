from django.urls import path

from .views import cancel, create, update, vagas_disponiveis

urlpatterns = [
    path("", vagas_disponiveis, name="vagas_disponiveis"),
    path("novo/", create, name="agendamento_create"),
    path("<int:pk>/editar/", update, name="agendamento_update"),
    path("<int:pk>/cancelar/", cancel, name="agendamento_cancel"),
]