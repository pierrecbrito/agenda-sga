from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.core.models import Cidadao
from apps.ubs.models import Especialidade, Ubs


def gerar_protocolo():
    return uuid4().hex[:12].upper()


class VagaAgendamento(models.Model):
    class Status(models.TextChoices):
        CONFIRMADO = "CONFIRMADO", "Confirmado"
        EXECUTADO = "EXECUTADO", "Executado"
        CANCELADO_PACIENTE = "CANCELADO_PACIENTE", "Cancelado pelo paciente"
        CANCELADO_UBS = "CANCELADO_UBS", "Cancelado pela UBS"
        FALTA = "FALTA", "Falta"

    class DiaSemana(models.IntegerChoices):
        SEGUNDA = 1, "Segunda-feira"
        TERCA = 2, "Terça-feira"
        QUARTA = 3, "Quarta-feira"
        QUINTA = 4, "Quinta-feira"
        SEXTA = 5, "Sexta-feira"
        SABADO = 6, "Sábado"
        DOMINGO = 7, "Domingo"

    ubs = models.ForeignKey(Ubs, on_delete=models.CASCADE, related_name="vagas_agendamento")
    especialidade = models.ForeignKey(Especialidade, on_delete=models.PROTECT, related_name="vagas_agendamento")
    cidadao = models.ForeignKey(
        Cidadao,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agendamentos",
    )
    recorrente = models.BooleanField(default=False)
    dia_semana = models.PositiveSmallIntegerField(choices=DiaSemana.choices, null=True, blank=True)
    data_vaga = models.DateField(null=True, blank=True)
    data_inicio_recorrencia = models.DateField(null=True, blank=True)
    data_fim_recorrencia = models.DateField(null=True, blank=True)
    hora_inicio = models.TimeField()
    hora_fim = models.TimeField()
    cadastro_abre_em = models.DateTimeField()
    cadastro_fecha_em = models.DateTimeField()
    data_solicitacao = models.DateTimeField(auto_now_add=True)
    protocolo = models.CharField(max_length=32, unique=True, default=gerar_protocolo, editable=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CONFIRMADO)

    class Meta:
        verbose_name = "vaga de agendamento"
        verbose_name_plural = "vagas de agendamento"
        ordering = ["data_vaga", "hora_inicio"]
        constraints = [
            models.UniqueConstraint(
                fields=["ubs", "especialidade", "data_vaga", "hora_inicio"],
                condition=Q(data_vaga__isnull=False),
                name="uniq_vaga_especifica_por_ubs_especialidade_horario",
            ),
        ]

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def clean(self):
        super().clean()

        if self.ubs_id and self.especialidade_id:
            if not self.ubs.especialidades.filter(pk=self.especialidade_id).exists():
                raise ValidationError({"especialidade": "A especialidade selecionada nao esta disponivel nesta UBS."})

        if self.recorrente:
            campos_obrigatorios = {
                "dia_semana": self.dia_semana,
                "data_inicio_recorrencia": self.data_inicio_recorrencia,
                "data_fim_recorrencia": self.data_fim_recorrencia,
            }
            faltando = [nome for nome, valor in campos_obrigatorios.items() if valor is None]
            if faltando:
                raise ValidationError({campo: "Este campo e obrigatorio para vagas recorrentes." for campo in faltando})
            if self.data_vaga is not None:
                raise ValidationError({"data_vaga": "Vagas recorrentes nao devem usar data_vaga fixa."})
        else:
            if self.data_vaga is None:
                raise ValidationError({"data_vaga": "Informe a data da vaga para vagas nao recorrentes."})
            if any([self.dia_semana, self.data_inicio_recorrencia, self.data_fim_recorrencia]):
                raise ValidationError("Vagas nao recorrentes nao devem conter campos de recorrencia.")

        if self.hora_inicio and self.hora_fim and self.hora_inicio >= self.hora_fim:
            raise ValidationError({"hora_fim": "O horario final deve ser maior que o horario inicial."})

        if self.cadastro_abre_em and self.cadastro_fecha_em and self.cadastro_abre_em >= self.cadastro_fecha_em:
            raise ValidationError({"cadastro_fecha_em": "O fechamento do cadastro deve ser posterior a abertura."})

        if self.cadastro_abre_em and self.cadastro_abre_em.tzinfo is None:
            self.cadastro_abre_em = timezone.make_aware(self.cadastro_abre_em)
        if self.cadastro_fecha_em and self.cadastro_fecha_em.tzinfo is None:
            self.cadastro_fecha_em = timezone.make_aware(self.cadastro_fecha_em)

    def __str__(self):
        dia = self.data_vaga.isoformat() if self.data_vaga else f"recorrente {self.get_dia_semana_display()}"
        return f"{self.ubs} - {self.especialidade} - {dia} {self.hora_inicio}"