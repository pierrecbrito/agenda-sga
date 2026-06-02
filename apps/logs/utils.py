"""
Utilitários de registro de log de auditoria.

Uso típico:
    from apps.logs.utils import registrar_log
    from apps.logs.models import LogAuditoria

    registrar_log(
        categoria=LogAuditoria.Categoria.AGENDAMENTO,
        acao="Agendamento criado",
        request=request,
        detalhes={"protocolo": ag.protocolo, "ubs": ag.ubs.nome_fantasia},
    )
"""

import traceback as tb_module

from .models import LogAuditoria


def _get_ip(request):
    """Extrai o IP real do cliente respeitando proxies."""
    if not request:
        return None
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _get_usuario_str(usuario):
    """Snapshot legível do usuário."""
    if not usuario or not usuario.pk:
        return "Anônimo"
    nome = usuario.get_full_name() or usuario.username
    return f"{nome} ({usuario.username})"


def registrar_log(
    categoria,
    acao,
    *,
    request=None,
    usuario=None,
    detalhes=None,
    eh_erro=False,
    exc=None,
):
    """
    Cria um registro de log de auditoria.

    Args:
        categoria: LogAuditoria.Categoria.*
        acao: Descrição curta da operação realizada.
        request: HttpRequest (opcional) — extrai usuário e IP automaticamente.
        usuario: User explícito (sobrepõe o do request).
        detalhes: dict de dados não-sensíveis envolvidos na operação.
        eh_erro: True quando é um erro/exceção.
        exc: Exception capturada para extrair o traceback.
    """
    try:
        # Resolve usuário
        user = usuario
        if user is None and request is not None:
            u = getattr(request, "user", None)
            user = u if (u and u.is_authenticated) else None

        traceback_str = ""
        if exc is not None:
            traceback_str = "".join(
                tb_module.format_exception(type(exc), exc, exc.__traceback__)
            )
        elif eh_erro:
            # Captura o traceback atual se não foi fornecido
            traceback_str = tb_module.format_exc()

        LogAuditoria.objects.create(
            categoria=categoria,
            acao=acao,
            usuario=user,
            usuario_str=_get_usuario_str(user),
            ip=_get_ip(request),
            detalhes=detalhes or {},
            eh_erro=eh_erro,
            traceback=traceback_str,
        )
    except Exception:
        # Nunca deixar que o próprio log quebre a aplicação
        pass
