from django import forms

from .models import EnderecoUbs, Especialidade, Ubs


class UbsForm(forms.ModelForm):
    class Meta:
        model = Ubs
        fields = [
            "cnes",
            "cnpj",
            "nome_fantasia",
            "razao_social",
            "distrito_sanitario",
            "telefone",
            "email",
            "horario_abertura",
            "horario_fechamento",
            "permite_agendamento_online",
            "antecedencia_maxima_dias",
            "especialidades",
        ]
        widgets = {
            "horario_abertura": forms.TimeInput(attrs={"type": "time", "class": "field-input"}),
            "horario_fechamento": forms.TimeInput(attrs={"type": "time", "class": "field-input"}),
            "permite_agendamento_online": forms.CheckboxInput(attrs={"class": "field-check"}),
            "antecedencia_maxima_dias": forms.NumberInput(attrs={"min": 0, "class": "field-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["especialidades"].widget = forms.SelectMultiple(attrs={"class": "field-specialties-hidden"})
        self.fields["especialidades"].queryset = Especialidade.objects.order_by("nome")

        for field_name, field in self.fields.items():
            if field_name in {"especialidades", "permite_agendamento_online"}:
                continue
            existing_class = field.widget.attrs.get("class", "")
            classes = f"{existing_class} field-input".strip()
            field.widget.attrs["class"] = classes


class EnderecoUbsForm(forms.ModelForm):
    class Meta:
        model = EnderecoUbs
        fields = [
            "cep",
            "logradouro",
            "numero",
            "complemento",
            "bairro",
            "cidade",
            "uf",
            "latitude",
            "longitude",
        ]
        widgets = {
            "latitude": forms.NumberInput(attrs={"step": "0.000001", "class": "field-input"}),
            "longitude": forms.NumberInput(attrs={"step": "0.000001", "class": "field-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            existing_class = field.widget.attrs.get("class", "")
            classes = f"{existing_class} field-input".strip()
            field.widget.attrs["class"] = classes