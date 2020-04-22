# Generated by Django 2.2.6 on 2020-03-25 20:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Panacea', '0010_auto_20200325_1241'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='tribal_reporters_permissions',
            new_name='tribal_reporter_permissions',
        ),
        migrations.AlterField(
            model_name='revenue_source',
            name='funding_type',
            field=models.CharField(blank=True, choices=[('Capital', 'Capital'), ('Operating', 'Operating'), ('Other', 'Other')], max_length=30, null=True),
        ),
    ]