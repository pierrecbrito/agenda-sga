from apps.core.models import UbsAdmin


def get_user_role(user):
    if not user or not user.is_authenticated:
        return "anonymous"
    if hasattr(user, "_cached_role"):
        return user._cached_role
        
    if user.is_superuser:
        role = "super_admin"
    elif UbsAdmin.objects.filter(user=user).exists():
        role = "ubs_admin"
    elif hasattr(user, "cidadao"):
        role = "cidadao"
    else:
        role = "usuario"
        
    user._cached_role = role
    return role


def user_can_manage_ubs(user, ubs):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return UbsAdmin.objects.filter(user=user, ubs=ubs).exists()
