# Generated by Django 2.1.7 on 2019-07-01 18:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Panacea', '0004_profile_requested_permissions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='active_permissions_request',
            field=models.BooleanField(blank=True, null=True),
        ),
    ]
