from django.conf import settings
from django.db import models


class Cidadao(models.Model):
    class Genero(models.TextChoices):
        MASCULINO = "M", "Masculino"
        FEMININO = "F", "Feminino"
        OUTRO = "O", "Outro"
        NAO_INFORMAR = "N", "Nao informar"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cidadao",
        null=True,
        blank=True,
    )
    nome_completo = models.CharField(max_length=255)
    cpf = models.CharField(max_length=14, unique=True)
    rg_numero = models.CharField(max_length=20, unique=True)
    rg_data_expedicao = models.DateField()
    naturalidade = models.CharField(max_length=120)
    data_nascimento = models.DateField()
    genero = models.CharField(max_length=1, choices=Genero.choices)
    cartao_sus = models.CharField(max_length=20, unique=True)
    whatsapp = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name = "cidadao"
        verbose_name_plural = "cidadaos"

    def __str__(self):
        return self.nome_completo


class Endereco(models.Model):
    cidadao = models.OneToOneField(
        Cidadao,
        on_delete=models.CASCADE,
        related_name="endereco",
    )
    cep = models.CharField(max_length=9)
    logradouro = models.CharField(max_length=255)
    numero = models.CharField(max_length=20)
    complemento = models.CharField(max_length=100, blank=True)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100)
    uf = models.CharField(max_length=2)

    class Meta:
        verbose_name = "endereco"
        verbose_name_plural = "enderecos"

    def __str__(self):
        return f"{self.logradouro}, {self.numero} - {self.cidade}/{self.uf}"