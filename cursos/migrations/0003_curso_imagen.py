# Generated by Django 5.1.1 on 2024-09-04 14:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cursos', '0002_categoria_curso_categoria'),
    ]

    operations = [
        migrations.AddField(
            model_name='curso',
            name='imagen',
            field=models.ImageField(blank=True, null=True, upload_to='cursos_imagenes/'),
        ),
    ]
