# Generated by Django 2.2.6 on 2020-02-24 19:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Panacea', '0003_auto_20200224_1117'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='fund_balance_type',
            name='heading',
        ),
    ]