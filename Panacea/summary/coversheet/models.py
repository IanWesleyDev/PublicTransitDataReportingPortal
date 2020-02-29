from Panacea.models import *


class cover_sheet(models.Model):
    organization = models.ForeignKey(organization, on_delete=models.PROTECT, blank=True, null=True)
    executive_officer_first_name = models.CharField(max_length=50, blank=True, null=True)
    executive_officer_last_name = models.CharField(max_length=50, blank=True, null=True)
    executive_officer_title = models.CharField(max_length=50, blank=True, null=True)
    service_website_url = models.URLField(verbose_name="Service website URL", max_length=255, blank=True, null=True)
    service_area_description = models.CharField(max_length=500, blank=True, null=True)
    congressional_districts = models.CharField(max_length=100, blank=True, null=True)
    legislative_districts = models.CharField(max_length=100, blank=True, null=True)
    type_of_government = models.CharField(max_length=100, blank=True, null=True)
    governing_body = models.TextField(blank=True, null=True)
    tax_rate_description = models.CharField(max_length=250, blank=True, null=True)
    transit_development_plan_url = models.CharField(verbose_name="Transit development plan URL", max_length=250, blank=True, null=True)
    intermodal_connections = models.TextField(verbose_name="Connections to other systems", blank=True, null=True)
    fares_description = models.TextField(blank=True, null=True)
    service_and_eligibility = models.TextField(verbose_name="Service and eligibility description", blank=True, null=True)
    current_operations = models.TextField(blank=True, null=True)
    revenue_service_vehicles = models.TextField(verbose_name="Revenue service vehicles", blank=True, null=True)
    days_of_service = models.CharField(verbose_name="Days of service", max_length=250, blank=True, null=True)
    monorail_ownership = models.CharField(max_length=250, blank=True, null=True)
    community_planning_region = models.CharField(max_length=50, blank=True, null=True)
    organization_logo = models.BinaryField(editable=True, blank=True, null=True)
    published_version = models.BooleanField(blank=True, null=True, default=False)
    history = HistoricalRecords()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['organization'], name="unique_organization")
        ]

    def is_identical_to_published_version(self):
        try:
            db_record = cover_sheet.objects.get(id=self.id)
        except:
            return False

        published_record = cover_sheet.history.filter(id=self.id, published_version=True).order_by('-history_date').first()
        if not published_record:
            if db_record.published_version:
                print('using db_record')
                published_record = db_record
            else:
                return False

        new_values = [(k, v) for k, v in self.__dict__.items() if k != '_state' and k != "published_version"]
        equals_published_record = True
        for key, value in new_values:
            if not published_record.__dict__[key] == value:
                equals_published_record = False

        return equals_published_record

    def save(self, *args, **kwargs):
        self.published_version = self.is_identical_to_published_version()
        super(cover_sheet, self).save(*args, **kwargs)


