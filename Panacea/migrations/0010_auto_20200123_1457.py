# Generated by Django 2.2.6 on 2020-01-23 22:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Panacea', '0009_auto_20200121_1227'),
    ]

    operations = [
        migrations.AddField(
            model_name='cover_sheet',
            name='published_version',
            field=models.BooleanField(blank=True, default=True, null=True),
        ),
        migrations.AddField(
            model_name='historicalcover_sheet',
            name='published_version',
            field=models.BooleanField(blank=True, default=True, null=True),
        ),
    ]
