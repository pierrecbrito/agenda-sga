from django.db import migrations


COORDENADAS = {
    "UNIDADE BÁSICA DE SAÚDE BARRO DURO": (-5.804211, -35.323932),
    "UNIDADE BÁSICA DE SAÚDE BELA VISTA": (-5.794892, -35.334772),
    "UNIDADE BÁSICA DE SAÚDE CIDADE DAS FLORES": (-5.789961, -35.347446),
    "UNIDADE BÁSICA DE SAÚDE CIDADE DAS ROSAS": (-5.792883, -35.343001),
    "CENTRO DE SAÚDE SANTO ANTONIO": (-5.790571, -35.331702),
}


def load_coordinates(apps, schema_editor):
    EnderecoUbs = apps.get_model("ubs", "EnderecoUbs")

    for nome_fantasia, (latitude, longitude) in COORDENADAS.items():
        endereco = EnderecoUbs.objects.select_related("ubs").filter(ubs__nome_fantasia=nome_fantasia).first()
        if not endereco:
            continue

        endereco.latitude = latitude
        endereco.longitude = longitude
        endereco.save(update_fields=["latitude", "longitude"])


def unload_coordinates(apps, schema_editor):
    EnderecoUbs = apps.get_model("ubs", "EnderecoUbs")
    EnderecoUbs.objects.update(latitude=None, longitude=None)


class Migration(migrations.Migration):

    dependencies = [
        ("ubs", "0004_enderecoubs_latitude_longitude"),
    ]

    operations = [
        migrations.RunPython(load_coordinates, unload_coordinates),
    ]