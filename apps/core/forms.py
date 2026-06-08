from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from apps.core.models import Cidadao
from apps.ubs.models import Ubs


def validar_cpf(cpf):
    if not cpf or len(cpf) != 11:
        return False
    if cpf in [d * 11 for d in "0123456789"]:
        return False
    # Calcula primeiro dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = soma % 11
    digito_1 = 0 if resto < 2 else 11 - resto
    if int(cpf[9]) != digito_1:
        return False
    # Calcula segundo dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = soma % 11
    digito_2 = 0 if resto < 2 else 11 - resto
    if int(cpf[10]) != digito_2:
        return False
    return True


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


class CidadaoRegistrationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        is_super_admin = kwargs.pop("is_super_admin", False)
        super().__init__(*args, **kwargs)
        
        # Se não for super admin, remove os campos administrativos
        if not is_super_admin:
            self.fields.pop("tipo_usuario", None)
            self.fields.pop("ubs", None)
            
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.Select):
                field.widget.attrs.update({"class": "field-input"})

    # Dados de Acesso
    tipo_usuario = forms.ChoiceField(
        choices=[
            ("cidadao", "Cidadão"),
            ("ubs_admin", "Administrador de UBS"),
            ("super_admin", "Super Administrador")
        ],
        label="Tipo de Usuário",
        required=False,
        initial="cidadao",
        widget=forms.Select(attrs={"class": "field-select"}),
    )
    
    ubs = forms.ModelChoiceField(
        queryset=Ubs.objects.all(),
        label="UBS Gerenciada",
        required=False,
        widget=forms.Select(attrs={"class": "field-select"}),
    )

    cpf = forms.CharField(
        max_length=14,
        label="CPF",
        widget=forms.TextInput(attrs={"placeholder": "000.000.000-00", "data-cpf-mask": "", "inputmode": "numeric"}),
    )
    email = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(attrs={"placeholder": "exemplo@email.com"}),
    )
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(attrs={"placeholder": "Digite sua senha"}),
    )
    confirm_password = forms.CharField(
        label="Confirme a Senha",
        widget=forms.PasswordInput(attrs={"placeholder": "Repita a senha"}),
    )

    # Dados Pessoais
    nome_completo = forms.CharField(
        max_length=255,
        label="Nome Completo",
        widget=forms.TextInput(attrs={"placeholder": "Seu nome completo"}),
    )
    rg_numero = forms.CharField(
        max_length=20,
        required=False,
        label="RG (número)",
        widget=forms.TextInput(attrs={"placeholder": "Apenas letras e números"}),
    )
    rg_orgao_emissor = forms.CharField(
        max_length=50,
        required=False,
        label="Órgão Emissor",
        widget=forms.TextInput(attrs={"placeholder": "Ex: SSP"}),
    )
    rg_data_expedicao = forms.DateField(
        required=False,
        label="Data de Expedição",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    naturalidade = forms.CharField(
        max_length=120,
        required=False,
        label="Naturalidade",
        widget=forms.TextInput(attrs={"placeholder": "Cidade de nascimento"}),
    )
    data_nascimento = forms.DateField(
        required=False,
        label="Data de Nascimento",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    genero = forms.ChoiceField(
        choices=Cidadao.Genero.choices,
        required=False,
        label="Gênero",
        widget=forms.Select(attrs={"class": "field-select"}),
    )
    cartao_sus = forms.CharField(
        max_length=20,
        required=False,
        label="Cartão SUS",
        widget=forms.TextInput(attrs={"placeholder": "Número do Cartão SUS"}),
    )
    whatsapp = forms.CharField(
        max_length=20,
        required=False,
        label="WhatsApp",
        widget=forms.TextInput(attrs={"placeholder": "Ex: (11) 99999-9999"}),
    )

    # Endereço
    cep = forms.CharField(
        max_length=9,
        required=False,
        label="CEP",
        widget=forms.TextInput(attrs={"placeholder": "00000-000", "inputmode": "numeric"}),
    )
    logradouro = forms.CharField(
        max_length=255,
        required=False,
        label="Logradouro",
        widget=forms.TextInput(attrs={"placeholder": "Rua, Avenida, etc."}),
    )
    numero = forms.CharField(
        max_length=20,
        required=False,
        label="Número",
        widget=forms.TextInput(attrs={"placeholder": "Ex: 123"}),
    )
    complemento = forms.CharField(
        max_length=100,
        required=False,
        label="Complemento",
        widget=forms.TextInput(attrs={"placeholder": "Ex: Apto 42 (Opcional)"}),
    )
    bairro = forms.CharField(
        max_length=100,
        required=False,
        label="Bairro",
        widget=forms.TextInput(attrs={"placeholder": "Bairro"}),
    )
    cidade = forms.CharField(
        max_length=100,
        required=False,
        label="Cidade",
        widget=forms.TextInput(attrs={"placeholder": "Cidade"}),
    )
    uf = forms.CharField(
        max_length=2,
        required=False,
        label="UF",
        widget=forms.TextInput(attrs={"placeholder": "Ex: SP"}),
    )

    def clean_cpf(self):
        cpf = self.cleaned_data.get("cpf")
        if not cpf:
            return cpf
        cpf_digits = "".join(ch for ch in cpf if ch.isdigit())
        if len(cpf_digits) != 11:
            raise ValidationError("CPF deve conter exatamente 11 dígitos.")
        
        # Validação algorítmica
        if not validar_cpf(cpf_digits):
            raise ValidationError("CPF inválido. Verifique os números digitados.")
        
        # Unicidade
        User = get_user_model()
        if User.objects.filter(username=cpf_digits).exists():
            raise ValidationError("Este CPF já está cadastrado como usuário.")
        if Cidadao.objects.filter(cpf=cpf_digits).exists():
            raise ValidationError("Este CPF já está cadastrado.")
            
        return cpf_digits

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not email:
            return email
        User = get_user_model()
        if User.objects.filter(email=email).exists():
            raise ValidationError("Este e-mail já está cadastrado.")
        return email

    def clean_rg_numero(self):
        rg = self.cleaned_data.get("rg_numero")
        if not rg:
            return rg
        rg_digits = "".join(ch for ch in rg if ch.isalnum())
        if Cidadao.objects.filter(rg_numero=rg_digits).exists():
            raise ValidationError("Este RG já está cadastrado.")
        return rg_digits

    def clean_cartao_sus(self):
        sus = self.cleaned_data.get("cartao_sus")
        if not sus:
            return sus
        sus_digits = "".join(ch for ch in sus if ch.isdigit())
        if Cidadao.objects.filter(cartao_sus=sus_digits).exists():
            raise ValidationError("Este Cartão SUS já está cadastrado.")
        return sus_digits

    def clean(self):
        cleaned_data = super().clean()
        tipo_usuario = cleaned_data.get("tipo_usuario", "cidadao")
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        
        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "As senhas não coincidem.")
            
        # Se for cidadão, exigir campos obrigatórios de cidadão
        if tipo_usuario == "cidadao":
            obrigatorios = [
                ("rg_numero", "RG é obrigatório para cidadãos."),
                ("rg_orgao_emissor", "Órgão emissor do RG é obrigatório."),
                ("rg_data_expedicao", "Data de expedição do RG é obrigatória."),
                ("naturalidade", "Naturalidade é obrigatória."),
                ("data_nascimento", "Data de nascimento é obrigatória."),
                ("cartao_sus", "Cartão SUS é obrigatório para cidadãos."),
                ("cep", "CEP é obrigatório."),
                ("logradouro", "Logradouro é obrigatório."),
                ("numero", "Número residencial é obrigatório."),
                ("bairro", "Bairro é obrigatório."),
                ("cidade", "Cidade é obrigatória."),
                ("uf", "UF é obrigatória."),
            ]
            for campo, msg in obrigatorios:
                if not cleaned_data.get(campo):
                    self.add_error(campo, msg)
                    
        # Se for admin de UBS, exigir a UBS
        elif tipo_usuario == "ubs_admin":
            if not cleaned_data.get("ubs"):
                self.add_error("ubs", "Por favor, selecione a UBS que este administrador gerenciará.")
                
        return cleaned_data
