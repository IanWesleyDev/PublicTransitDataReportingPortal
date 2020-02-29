from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group  ## A new class is imported. ##
from django.core.validators import MaxValueValidator
from django.db import models
from django.db.models import UniqueConstraint
from django.db.models.functions import datetime

from django.db.models.signals import post_save
from django.dispatch import receiver
from localflavor.us.models import USStateField, USZipCodeField
from phonenumber_field.modelfields import PhoneNumberField
import datetime

from simple_history.models import HistoricalRecords


# Load order of models matters
from Panacea.shared_content.models import *
from Panacea.vanpool.models import *
from Panacea.summary.misc.models import *
from Panacea.summary.coversheet.models import *
from Panacea.summary.data_report.models import *
from Panacea.summary.review_tracking.models import *
from Panacea.summary.tables_and_reports.models import *


#TODO did I forget to include this table in the data entry?
class depreciation(models.Model):
    reported_value = models.IntegerField(blank =False, null=True)
    year = models.IntegerField(blank=True, null=True)
    organization = models.ForeignKey(organization, on_delete=models.PROTECT, blank=True, null=True)
    report_by = models.ForeignKey(custom_user, on_delete=models.PROTECT, blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    history = HistoricalRecords()


#TODO do we sitll need this?
class validation_errors(models.Model):
    DO_OR_PT = (
        ('Direct Operated', 'Direct Operated'),
        ('Purchased', 'Purchased') )
    year = models.IntegerField(blank=True, null=True)
    transit_mode = models.ForeignKey(transit_mode, on_delete=models.PROTECT, related_name= '+', blank=True, null=True)
    administration_of_mode = models.CharField(max_length=80, choices=DO_OR_PT, blank=False, null=True)
    organization = models.ForeignKey(organization, on_delete=models.PROTECT, blank=True, null=True)
    report_by = models.ForeignKey(custom_user, on_delete=models.PROTECT, blank=True, null=True)
    error = models.TextField(blank=True, null=True)
    error_resolution = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['year', 'transit_mode', 'administration_of_mode', 'organization', 'error']








