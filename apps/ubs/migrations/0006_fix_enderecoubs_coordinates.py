from django.db import migrations


COORDENADAS_CORRETAS = {
    "UNIDADE BÁSICA DE SAÚDE BARRO DURO": (-5.7786189, -35.3044061),
    "UNIDADE BÁSICA DE SAÚDE BELA VISTA": (-5.8043340, -35.4374309),
    "UNIDADE BÁSICA DE SAÚDE CIDADE DAS FLORES": (-5.7488773, -35.3080436),
    "UNIDADE BÁSICA DE SAÚDE CIDADE DAS ROSAS": (-5.7483443, -35.3001660),
    "CENTRO DE SAÚDE SANTO ANTONIO": (-5.7889662, -35.3091921),
}


def forwards(apps, schema_editor):
    EnderecoUbs = apps.get_model("ubs", "EnderecoUbs")

    for nome_fantasia, (latitude, longitude) in COORDENADAS_CORRETAS.items():
        endereco = EnderecoUbs.objects.select_related("ubs").filter(ubs__nome_fantasia=nome_fantasia).first()
        if not endereco:
            continue

        endereco.latitude = latitude
        endereco.longitude = longitude
        endereco.save(update_fields=["latitude", "longitude"])


def backwards(apps, schema_editor):
    EnderecoUbs = apps.get_model("ubs", "EnderecoUbs")
    EnderecoUbs.objects.update(latitude=None, longitude=None)


class Migration(migrations.Migration):

    dependencies = [
        ("ubs", "0005_seed_enderecos_com_coordenadas"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]