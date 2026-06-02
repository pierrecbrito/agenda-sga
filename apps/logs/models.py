from django.conf import settings
from django.db import models


class LogAuditoria(models.Model):
    """
    Registra todas as operações realizadas no sistema.
    Campos não-sensíveis são salvos em `detalhes` (JSON).
    Erros têm `eh_erro=True` e um traceback completo em `traceback`.
    """

    class Categoria(models.TextChoices):
        AUTENTICACAO = "AUTH",  "Autenticação"
        AGENDAMENTO  = "AGEND", "Agendamento"
        UBS          = "UBS",   "UBS"
        CIDADAO      = "CID",   "Cidadão"
        ERRO         = "ERRO",  "Erro"
        SISTEMA      = "SIS",   "Sistema"

    categoria   = models.CharField(
        max_length=5,
        choices=Categoria.choices,
        default=Categoria.SISTEMA,
        db_index=True,
    )
    acao        = models.CharField(max_length=200)
    usuario     = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="logs_auditoria",
    )
    # Snapshot do identificador do usuário no momento do log
    usuario_str = models.CharField(max_length=150, blank=True)
    ip          = models.GenericIPAddressField(null=True, blank=True)
    detalhes    = models.JSONField(default=dict, blank=True)
    eh_erro     = models.BooleanField(default=False, db_index=True)
    traceback   = models.TextField(blank=True)
    criado_em   = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "log de auditoria"
        verbose_name_plural = "logs de auditoria"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"[{self.get_categoria_display()}] {self.acao} — {self.usuario_str} @ {self.criado_em:%d/%m/%Y %H:%M}"
