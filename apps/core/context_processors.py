from apps.core.access import get_user_role


def user_role(request):
    """Injeta o papel do usuário autenticado em todos os templates."""
    if request.user.is_authenticated:
        return {"user_role": get_user_role(request.user)}
    return {"user_role": None}
