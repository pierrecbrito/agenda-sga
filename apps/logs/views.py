from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render

from apps.core.access import get_user_role

from .models import LogAuditoria


@login_required
def relatorio_logs(request):
    role = get_user_role(request.user)

    # Apenas admins acessam relatórios
    if role not in {"super_admin", "ubs_admin"}:
        from django.shortcuts import redirect
        from django.contrib import messages
        messages.error(request, "Acesso restrito a administradores.")
        return redirect("home")

    # Base queryset — admin de UBS vê apenas seus próprios logs
    if role == "super_admin":
        qs = LogAuditoria.objects.select_related("usuario").all()
    else:
        qs = LogAuditoria.objects.select_related("usuario").filter(usuario=request.user)

    # ── Filtros ────────────────────────────────────────────────────────────
    filtro_categoria  = request.GET.get("categoria", "").strip()
    filtro_usuario    = request.GET.get("usuario", "").strip()
    filtro_data_ini   = request.GET.get("data_inicio", "").strip()
    filtro_data_fim   = request.GET.get("data_fim", "").strip()
    filtro_apenas_erros = request.GET.get("apenas_erros", "")
    filtro_busca      = request.GET.get("busca", "").strip()

    if filtro_categoria:
        qs = qs.filter(categoria=filtro_categoria)
    if filtro_usuario and role == "super_admin":
        qs = qs.filter(usuario_str__icontains=filtro_usuario)
    if filtro_data_ini:
        qs = qs.filter(criado_em__date__gte=filtro_data_ini)
    if filtro_data_fim:
        qs = qs.filter(criado_em__date__lte=filtro_data_fim)
    if filtro_apenas_erros:
        qs = qs.filter(eh_erro=True)
    if filtro_busca:
        from django.db.models import Q
        qs = qs.filter(
            Q(acao__icontains=filtro_busca)
            | Q(usuario_str__icontains=filtro_busca)
            | Q(detalhes__icontains=filtro_busca)
        )

    # ── Erros recentes em destaque (últimos 50 não filtrados pelo usuário) ─
    erros_recentes = LogAuditoria.objects.filter(eh_erro=True).order_by("-criado_em")[:10]
    if role == "ubs_admin":
        erros_recentes = erros_recentes.filter(usuario=request.user)

    # ── Paginação ──────────────────────────────────────────────────────────
    paginator  = Paginator(qs, 25)
    page_num   = request.GET.get("page", 1)
    page_obj   = paginator.get_page(page_num)

    # Usuários disponíveis para filtro (só super_admin)
    usuarios_disponíveis = []
    if role == "super_admin":
        from django.contrib.auth import get_user_model
        User = get_user_model()
        usuarios_disponíveis = (
            User.objects.filter(logs_auditoria__isnull=False)
            .distinct()
            .order_by("username")
        )

    context = {
        "role": role,
        "page_obj": page_obj,
        "erros_recentes": erros_recentes,
        "categorias": LogAuditoria.Categoria.choices,
        "usuarios_disponiveis": usuarios_disponíveis,
        # Filtros ativos
        "filtro_categoria": filtro_categoria,
        "filtro_usuario": filtro_usuario,
        "filtro_data_ini": filtro_data_ini,
        "filtro_data_fim": filtro_data_fim,
        "filtro_apenas_erros": filtro_apenas_erros,
        "filtro_busca": filtro_busca,
        "total": qs.count(),
    }
    return render(request, "logs/relatorio.html", context)
