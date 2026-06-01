from django import forms

from apps.agendamentos.models import VagaAgendamento
from apps.ubs.models import Especialidade, Ubs


class AgendamentoFilterForm(forms.Form):
    ubs = forms.ModelChoiceField(queryset=Ubs.objects.none(), required=False, label="UBS")
    especialidade = forms.ModelChoiceField(queryset=Especialidade.objects.none(), required=False, label="Especialidade")
    data_inicio = forms.DateField(required=False, label="De", widget=forms.DateInput(attrs={"type": "date"}))
    data_fim = forms.DateField(required=False, label="Até", widget=forms.DateInput(attrs={"type": "date"}))
    cidadao_busca = forms.CharField(
        required=False,
        label="CPF ou nome do cidadão",
        widget=forms.TextInput(attrs={"data-cidadao-autocomplete": "", "autocomplete": "off"}),
    )
    status = forms.ChoiceField(
        required=False,
        label="Status",
        choices=[("", "Todos os status")] + VagaAgendamento.Status.choices,
    )

    def __init__(self, *args, **kwargs):
        ubs_queryset = kwargs.pop("ubs_queryset", Ubs.objects.none())
        especialidade_queryset = kwargs.pop("especialidade_queryset", Especialidade.objects.none())
        super().__init__(*args, **kwargs)
        self.fields["ubs"].queryset = ubs_queryset
        self.fields["especialidade"].queryset = especialidade_queryset

        for field in self.fields.values():
            existing_class = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing_class} field-input".strip()


class AgendamentoBaseForm(forms.ModelForm):
    class Meta:
        model = VagaAgendamento
        fields = ["ubs", "especialidade", "data_vaga", "hora_inicio", "hora_fim"]
        widgets = {
            "data_vaga": forms.DateInput(attrs={"type": "date"}),
            "hora_inicio": forms.TimeInput(attrs={"type": "time"}),
            "hora_fim": forms.TimeInput(attrs={"type": "time"}),
        }

    def __init__(self, *args, **kwargs):
        ubs_queryset = kwargs.pop("ubs_queryset", Ubs.objects.none())
        especialidade_queryset = kwargs.pop("especialidade_queryset", Especialidade.objects.none())
        super().__init__(*args, **kwargs)
        self.fields["ubs"].queryset = ubs_queryset
        self.fields["especialidade"].queryset = especialidade_queryset

        for field in self.fields.values():
            existing_class = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing_class} field-input".strip()


class AgendamentoAdminForm(AgendamentoBaseForm):
    cidadao_busca = forms.CharField(
        required=False,
        label="CPF ou nome do cidadão",
        widget=forms.TextInput(attrs={"data-cidadao-autocomplete": "", "autocomplete": "off"}),
    )
    status = forms.ChoiceField(
        required=False,
        label="Status do agendamento",
        choices=VagaAgendamento.Status.choices,
    )

    class Meta(AgendamentoBaseForm.Meta):
        fields = ["ubs", "especialidade", "data_vaga", "hora_inicio", "hora_fim"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Pré-popular o campo status com o valor atual da instância
        if self.instance and self.instance.pk:
            self.fields["status"].initial = self.instance.status

        existing_class = self.fields["cidadao_busca"].widget.attrs.get("class", "")
        self.fields["cidadao_busca"].widget.attrs["class"] = f"{existing_class} field-input".strip()
        self.fields["cidadao_busca"].widget.attrs.update({
            "placeholder": "Ex: 000.000.000-00 ou João Silva",
            "autocomplete": "off",
        })

        existing_class = self.fields["status"].widget.attrs.get("class", "")
        self.fields["status"].widget.attrs["class"] = f"{existing_class} field-input".strip()


class AgendamentoCidadaoForm(AgendamentoBaseForm):
    """
    Formulário para cidadãos: não exibe campo de status nem busca de cidadão.
    A UBS é limitada pelo queryset passado (apenas com agendamento online habilitado).
    """
    pass
