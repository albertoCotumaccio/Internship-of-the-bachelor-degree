# Generated by Django 3.2.5 on 2021-10-09 09:35

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('app', '0032_alter_menusettimana_creatore'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ingredienteimpianto',
            options={'ordering': ('ingrediente__nome_generico',)},
        ),
        migrations.AlterField(
            model_name='menusettimana',
            name='approvatore',
            field=models.ForeignKey(blank=True, limit_choices_to={'is_staff': True}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approvatore', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='menusettimana',
            name='creatore',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='creatore', to=settings.AUTH_USER_MODEL),
        ),
    ]