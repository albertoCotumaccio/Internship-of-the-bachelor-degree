# Generated by Django 3.2.5 on 2021-10-15 13:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0057_auto_20211015_1459'),
    ]

    operations = [
        migrations.AlterField(
            model_name='area',
            name='capo',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='app.capoarea'),
        ),
    ]