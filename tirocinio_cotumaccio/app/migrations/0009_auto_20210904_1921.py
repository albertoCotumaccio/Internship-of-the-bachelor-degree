# Generated by Django 3.2.5 on 2021-09-04 17:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0008_remove_menusettimana_tag'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='menusettimana',
            name='ricette',
        ),
        migrations.CreateModel(
            name='tagRicetta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ricetta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.ricetta')),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.tag')),
            ],
        ),
    ]