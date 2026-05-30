from django.contrib.auth.forms import AuthenticationForm


class CpfAuthenticationForm(AuthenticationForm):
    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self.fields["username"].label = "CPF"
        self.fields["username"].widget.attrs.update(
            {
                "placeholder": "Digite seu CPF",
                "autocomplete": "username",
                "inputmode": "numeric",
            }
        )