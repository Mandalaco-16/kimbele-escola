from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('escola', '0031_boletimpagamento_visto'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Nota',
        ),
        migrations.DeleteModel(
            name='Disciplina',
        ),
    ]
