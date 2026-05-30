from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


def _somente_digitos(valor):
    return "".join(ch for ch in valor if ch.isdigit())


class CpfBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        user_model = get_user_model()
        identifier = username or kwargs.get(user_model.USERNAME_FIELD)
        identifier_digits = _somente_digitos(identifier or "")

        if not identifier or not password:
            return None

        try:
            user = user_model.objects.select_related("cidadao").get(username=identifier)
        except user_model.DoesNotExist:
            try:
                if identifier_digits:
                    user = user_model.objects.select_related("cidadao").get(username=identifier_digits)
                else:
                    raise user_model.DoesNotExist
            except user_model.DoesNotExist:
                try:
                    user = user_model.objects.select_related("cidadao").get(cidadao__cpf=identifier_digits or identifier)
                except user_model.DoesNotExist:
                    return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None