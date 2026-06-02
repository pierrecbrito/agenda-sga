"""
Signals para rastreamento de autenticação:
- user_logged_in  → login bem-sucedido
- user_logged_out → logout
- user_login_failed → tentativa de login falha (registrado como erro)
"""

from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.dispatch import receiver

from .models import LogAuditoria
from .utils import registrar_log, _get_ip


@receiver(user_logged_in)
def on_login(sender, request, user, **kwargs):
    registrar_log(
        categoria=LogAuditoria.Categoria.AUTENTICACAO,
        acao="Login realizado",
        request=request,
        usuario=user,
        detalhes={
            "username": user.username,
            "nome": user.get_full_name() or user.username,
        },
    )


@receiver(user_logged_out)
def on_logout(sender, request, user, **kwargs):
    registrar_log(
        categoria=LogAuditoria.Categoria.AUTENTICACAO,
        acao="Logout realizado",
        request=request,
        usuario=user,
        detalhes={
            "username": getattr(user, "username", "desconhecido"),
        },
    )


@receiver(user_login_failed)
def on_login_failed(sender, credentials, request, **kwargs):
    # Não salva a senha — apenas o username tentado
    username_tentado = credentials.get("username", "?")
    registrar_log(
        categoria=LogAuditoria.Categoria.AUTENTICACAO,
        acao="Tentativa de login falha",
        request=request,
        usuario=None,
        detalhes={
            "username_tentado": username_tentado,
            "ip": _get_ip(request),
        },
        eh_erro=True,
    )
