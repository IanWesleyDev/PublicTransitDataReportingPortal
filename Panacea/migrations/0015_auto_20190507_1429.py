# Generated by Django 2.1.7 on 2019-05-07 21:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Panacea', '0014_auto_20190429_1016'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='reports_on',
            field=models.ManyToManyField(blank=True, to='Panacea.ReportType'),
        ),
    ]