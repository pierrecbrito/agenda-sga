from django.urls import path

from .views import vagas_disponiveis

urlpatterns = [
    path("", vagas_disponiveis, name="vagas_disponiveis"),
]