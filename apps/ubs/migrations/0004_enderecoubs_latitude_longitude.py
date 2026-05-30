from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ubs", "0003_load_ubs_from_txt"),
    ]

    operations = [
        migrations.AddField(
            model_name="enderecoubs",
            name="latitude",
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name="enderecoubs",
            name="longitude",
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
    ]