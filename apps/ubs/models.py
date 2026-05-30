from django.db import models


class Ubs(models.Model):
    especialidades = models.ManyToManyField(
        "Especialidade",
        blank=True,
        related_name="ubs",
    )
    cnes = models.CharField(max_length=20, unique=True)
    cnpj = models.CharField(max_length=18, unique=True)
    nome_fantasia = models.CharField(max_length=255)
    razao_social = models.CharField(max_length=255)
    distrito_sanitario = models.CharField(max_length=120)
    telefone = models.CharField(max_length=20)
    email = models.EmailField()
    horario_abertura = models.TimeField()
    horario_fechamento = models.TimeField()
    permite_agendamento_online = models.BooleanField(default=False)
    antecedencia_maxima_dias = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "ubs"
        verbose_name_plural = "ubs"

    def __str__(self):
        return f"{self.nome_fantasia} ({self.cnes})"


class Especialidade(models.Model):
    cbo_codigo = models.CharField(max_length=6, unique=True)
    nome = models.CharField(max_length=255)

    class Meta:
        verbose_name = "especialidade"
        verbose_name_plural = "especialidades"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.cbo_codigo} - {self.nome}"


class EnderecoUbs(models.Model):
    ubs = models.OneToOneField(Ubs, on_delete=models.CASCADE, related_name="endereco")
    cep = models.CharField(max_length=9)
    logradouro = models.CharField(max_length=255)
    numero = models.CharField(max_length=20)
    complemento = models.CharField(max_length=100, blank=True)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100)
    uf = models.CharField(max_length=2)

    class Meta:
        verbose_name = "endereco da ubs"
        verbose_name_plural = "enderecos das ubs"

    def __str__(self):
        return f"{self.logradouro}, {self.numero} - {self.cidade}/{self.uf}"