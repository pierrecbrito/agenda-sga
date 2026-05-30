from django.db import migrations


UBS_FIXTURES = [
    {
        "cnes": "9000001",
        "cnpj": "90.000.001/0001-91",
        "nome_fantasia": "UNIDADE BÁSICA DE SAÚDE BARRO DURO",
        "razao_social": "UNIDADE BÁSICA DE SAÚDE BARRO DURO",
        "distrito_sanitario": "Barro Duro",
        "telefone": "(84) 99621-7337",
        "email": "barro-duro@agenda-sga.local",
        "horario_abertura": "08:00",
        "horario_fechamento": "16:00",
        "cep": "00000-000",
        "logradouro": "Vereador Edson Coelho da Silva",
        "numero": "480",
        "bairro": "Barro Duro",
        "cidade": "São Gonçalo do Amarante",
        "uf": "RN",
    },
    {
        "cnes": "9000002",
        "cnpj": "90.000.002/0001-92",
        "nome_fantasia": "UNIDADE BÁSICA DE SAÚDE BELA VISTA",
        "razao_social": "UNIDADE BÁSICA DE SAÚDE BELA VISTA",
        "distrito_sanitario": "Bela Vista",
        "telefone": "(84) 99992-0002",
        "email": "bela-vista@agenda-sga.local",
        "horario_abertura": "08:00",
        "horario_fechamento": "16:30",
        "cep": "00000-000",
        "logradouro": "Rua Geraldo Monteiro",
        "numero": "01",
        "bairro": "Bela Vista",
        "cidade": "São Gonçalo do Amarante",
        "uf": "RN",
    },
    {
        "cnes": "9000003",
        "cnpj": "90.000.003/0001-93",
        "nome_fantasia": "UNIDADE BÁSICA DE SAÚDE CIDADE DAS FLORES",
        "razao_social": "UNIDADE BÁSICA DE SAÚDE CIDADE DAS FLORES",
        "distrito_sanitario": "Jardins",
        "telefone": "(84) 99992-0003",
        "email": "cidade-das-flores@agenda-sga.local",
        "horario_abertura": "08:00",
        "horario_fechamento": "16:30",
        "cep": "00000-000",
        "logradouro": "R. Flores do Campo",
        "numero": "37",
        "bairro": "Jardins",
        "cidade": "São Gonçalo do Amarante",
        "uf": "RN",
    },
    {
        "cnes": "9000004",
        "cnpj": "90.000.004/0001-94",
        "nome_fantasia": "UNIDADE BÁSICA DE SAÚDE CIDADE DAS ROSAS",
        "razao_social": "UNIDADE BÁSICA DE SAÚDE CIDADE DAS ROSAS",
        "distrito_sanitario": "Jardins",
        "telefone": "(84) 99992-0004",
        "email": "cidade-das-rosas@agenda-sga.local",
        "horario_abertura": "08:00",
        "horario_fechamento": "16:30",
        "cep": "00000-000",
        "logradouro": "R. das Verbenas",
        "numero": "50",
        "bairro": "Jardins",
        "cidade": "São Gonçalo do Amarante",
        "uf": "RN",
    },
    {
        "cnes": "9000005",
        "cnpj": "90.000.005/0001-95",
        "nome_fantasia": "CENTRO DE SAÚDE SANTO ANTONIO",
        "razao_social": "CENTRO DE SAÚDE SANTO ANTONIO",
        "distrito_sanitario": "Santo Antonio",
        "telefone": "(84) 99992-0005",
        "email": "santo-antonio@agenda-sga.local",
        "horario_abertura": "08:00",
        "horario_fechamento": "16:30",
        "cep": "00000-000",
        "logradouro": "Av. Joaquim Rodrigues da Silva",
        "numero": "108",
        "bairro": "Santo Antonio",
        "cidade": "São Gonçalo do Amarante",
        "uf": "RN",
    },
]


def load_ubs(apps, schema_editor):
    Ubs = apps.get_model("ubs", "Ubs")
    EnderecoUbs = apps.get_model("ubs", "EnderecoUbs")

    for item in UBS_FIXTURES:
        endereco = {
            "cep": item["cep"],
            "logradouro": item["logradouro"],
            "numero": item["numero"],
            "bairro": item["bairro"],
            "cidade": item["cidade"],
            "uf": item["uf"],
        }

        ubs, _ = Ubs.objects.update_or_create(
            cnes=item["cnes"],
            defaults={
                "cnpj": item["cnpj"],
                "nome_fantasia": item["nome_fantasia"],
                "razao_social": item["razao_social"],
                "distrito_sanitario": item["distrito_sanitario"],
                "telefone": item["telefone"],
                "email": item["email"],
                "horario_abertura": item["horario_abertura"],
                "horario_fechamento": item["horario_fechamento"],
                "permite_agendamento_online": False,
                "antecedencia_maxima_dias": 0,
            },
        )

        EnderecoUbs.objects.update_or_create(ubs=ubs, defaults=endereco)


def unload_ubs(apps, schema_editor):
    Ubs = apps.get_model("ubs", "Ubs")
    Ubs.objects.filter(cnes__in=[item["cnes"] for item in UBS_FIXTURES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("ubs", "0002_especialidade_ubs_especialidades"),
    ]

    operations = [
        migrations.RunPython(load_ubs, unload_ubs),
    ]