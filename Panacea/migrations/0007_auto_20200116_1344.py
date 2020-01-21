# Generated by Django 2.2.6 on 2020-01-16 21:44

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Panacea', '0006_delete_historicalcover_sheet_review_notes'),
    ]

    operations = [
        migrations.AddField(
            model_name='cover_sheet_review_notes',
            name='custom_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='cover_sheet_review_notes',
            name='date',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
