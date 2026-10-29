from django.db import migrations

NOMES = [
    "Língua Portuguesa", "Matemática", "Estudo do Meio",
    "Educação Manual e Plástica", "Educação Física", "Educação Musical",
]


def criar(apps, schema_editor):
    Disciplina = apps.get_model("escola", "Disciplina")
    for i, n in enumerate(NOMES, 1):
        Disciplina.objects.get_or_create(nome=n, defaults={"ordem": i})


class Migration(migrations.Migration):
    dependencies = [("escola", "0028_disciplina_nota")]
    operations = [migrations.RunPython(criar, migrations.RunPython.noop)]
