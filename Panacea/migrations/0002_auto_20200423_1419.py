# Generated by Django 2.2.6 on 2020-04-23 21:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Panacea', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cover_sheet',
            name='organization_logo',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='historicalcover_sheet',
            name='organization_logo',
            field=models.TextField(blank=True, null=True),
        ),
    ]