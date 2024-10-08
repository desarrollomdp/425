# Generated by Django 5.0.3 on 2024-08-31 18:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('formulario', '0003_delete_curso_alter_inscripcion_cursos'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inscripcion',
            name='celular',
            field=models.CharField(max_length=15, unique=True),
        ),
        migrations.AlterField(
            model_name='inscripcion',
            name='email',
            field=models.EmailField(max_length=254, unique=True),
        ),
    ]
