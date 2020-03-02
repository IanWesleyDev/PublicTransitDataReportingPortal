from django.db import models

from Panacea.models import *


#TODO remove this table
class rollup_mode(models.Model):
    name = models.CharField(max_length=80)

    def __str__(self):
        return self.name

class transit_mode(models.Model):
    name = models.CharField(max_length=90, blank=True)
    rollup_mode = models.CharField(max_length=90, blank=True, null=True)

    def __str__(self):
        return self.name

class service_offered(models.Model):
    DO_OR_PT = (
        ('Direct Operated', 'Direct Operated'),
        ('Purchased', 'Purchased')
    )
    transit_mode = models.ForeignKey(transit_mode, on_delete=models.PROTECT, related_name ='+', blank=True)
    administration_of_mode = models.CharField(max_length=80, choices=DO_OR_PT, blank=False)
    organization = models.ForeignKey(organization, on_delete=models.PROTECT, blank=True, null=False)
    service_mode_discontinued = models.BooleanField(default=False, blank=False, null=False)
