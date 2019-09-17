# Generated by Django 2.2.5 on 2019-09-17 19:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Panacea', '0002_cover_sheet'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cover_sheet',
            name='community_medicaid_days_of_service',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='cover_sheet',
            name='community_medicaid_revenue_service_vehicles',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='cover_sheet',
            name='community_medicaid_service_and_eligibility',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='cover_sheet',
            name='congressional_districts',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='cover_sheet',
            name='current_operations',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='cover_sheet',
            name='fares_desc',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='cover_sheet',
            name='governing_body',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='cover_sheet',
            name='intermodal_connections',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='cover_sheet',
            name='legislative_districts',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='cover_sheet',
            name='service_area_desc',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='cover_sheet',
            name='service_website_url',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='cover_sheet',
            name='tax_authorized_desc',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='cover_sheet',
            name='transit_development_plan_url',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='cover_sheet',
            name='type_of_government',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]