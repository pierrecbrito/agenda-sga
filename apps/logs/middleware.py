"""
Middleware que captura exceções não tratadas e as registra como logs de erro.
O erro é re-levantado após o registro para que o Django continue o fluxo normal
(exibir página 500, enviar e-mail de erro, etc.).
"""

from .models import LogAuditoria
from .utils import registrar_log


class AuditErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        """Chamado pelo Django sempre que uma view levanta uma exceção."""
        try:
            path = request.path
            method = request.method
            usuario_str = ""
            if hasattr(request, "user") and request.user.is_authenticated:
                usuario_str = request.user.username

            registrar_log(
                categoria=LogAuditoria.Categoria.ERRO,
                acao=f"Erro em {method} {path}: {type(exception).__name__}",
                request=request,
                detalhes={
                    "path": path,
                    "method": method,
                    "exception_type": type(exception).__name__,
                    "exception_msg": str(exception)[:500],
                    "usuario": usuario_str,
                },
                eh_erro=True,
                exc=exception,
            )
        except Exception:
            pass
        # Retorna None para deixar o Django continuar o tratamento padrão do erro
        return None
