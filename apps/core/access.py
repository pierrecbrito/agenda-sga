from apps.core.models import UbsAdmin


def get_user_role(user):
    if not user or not user.is_authenticated:
        return "anonymous"
    if user.is_superuser:
        return "super_admin"
    if UbsAdmin.objects.filter(user=user).exists():
        return "ubs_admin"
    if hasattr(user, "cidadao"):
        return "cidadao"
    return "usuario"


def user_can_manage_ubs(user, ubs):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return UbsAdmin.objects.filter(user=user, ubs=ubs).exists()
