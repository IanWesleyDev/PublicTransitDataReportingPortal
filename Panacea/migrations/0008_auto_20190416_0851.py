# Generated by Django 2.1.7 on 2019-04-16 15:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Panacea', '0007_auto_20190416_0847'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vanpool_report',
            name='average_riders_per_van',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True),
        ),
        migrations.AlterField(
            model_name='vanpool_report',
            name='average_round_trip_miles',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True),
        ),
        migrations.AlterField(
            model_name='vanpool_report',
            name='loaner_spare_vans_in_fleet',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='vanpool_report',
            name='vanpool_group_folds',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='vanpool_report',
            name='vanpool_group_starts',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='vanpool_report',
            name='vanpool_groups_in_operation',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='vanpool_report',
            name='vanpool_miles_traveled',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True),
        ),
        migrations.AlterField(
            model_name='vanpool_report',
            name='vanpool_passenger_trips',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='vanpool_report',
            name='vans_available',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='vanpool_report',
            name='vanshare_group_folds',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='vanpool_report',
            name='vanshare_group_starts',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='vanpool_report',
            name='vanshare_groups_in_operation',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='vanpool_report',
            name='vanshare_miles_traveled',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True),
        ),
        migrations.AlterField(
            model_name='vanpool_report',
            name='vanshare_passenger_trips',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
