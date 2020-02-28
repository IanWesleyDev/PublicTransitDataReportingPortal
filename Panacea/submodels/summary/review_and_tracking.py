from Panacea.models import *

class summary_report_status(models.Model):

    STATUS = (
        ("With user", "With user"),
        ("With WSDOT", "With WSDOT"),
        ("Complete", "Complete")
    )

    year = models.IntegerField()
    organization = models.ForeignKey(organization, on_delete=models.PROTECT)
    cover_sheet_status = models.CharField(default="With user", max_length=80, choices=STATUS)
    cover_sheet_submitted_for_review = models.BooleanField(default=False)
    data_report_status = models.CharField(default="With user", max_length=80, choices=STATUS)
    data_report_submitted_for_review = models.BooleanField(default=False)
    history = HistoricalRecords()

    class Meta:
        unique_together = ('year', 'organization',)


class summary_organization_progress(models.Model):

    organization = models.ForeignKey(organization, on_delete=models.PROTECT)
    started = models.BooleanField(default=False)
    address_and_organization = models.BooleanField(default=False)
    organization_details = models.BooleanField(default=False)
    service_cover_sheet = models.BooleanField(default=False)
    confirm_service = models.BooleanField(default=False)
    transit_data = models.BooleanField(default=False)
    revenue = models.BooleanField(default=False)
    expenses = models.BooleanField(default=False)
    ending_balances = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['organization'], name='unique_status'),
        ]


class cover_sheet_review_notes(models.Model):
    NOTE_AREAS = (
        ("Address", "Address"),
        ("Organization", "Organization"),
        ("Service", "Service"),
    )

    NOTE_STATUS = (
        ("Open", "Open"),
        ("Closed", "Closed"),
        ("Waiting", "Waiting"),
    )

    year = models.IntegerField()
    summary_report_status = models.ForeignKey(summary_report_status, on_delete=models.PROTECT)
    note = models.TextField(blank=True, null=True)
    note_area = models.CharField(max_length=80, choices=NOTE_AREAS)
    note_field = models.CharField(max_length=80, blank=True, null=True)
    wsdot_note = models.BooleanField(default=True)
    parent_note = models.IntegerField(blank=True, null=True)
    note_status = models.CharField(max_length=50, choices=NOTE_STATUS, default="Open")
    custom_user = models.ForeignKey(custom_user, on_delete=models.PROTECT, blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.id:
            if self.parent_note:
                parent_note = cover_sheet_review_notes.objects.get(id=self.parent_note)
                if self.wsdot_note:
                    parent_note.note_status = "Open"
                else:
                    parent_note.note_status = "Waiting"
                parent_note.save()

        super(cover_sheet_review_notes, self).save(*args, **kwargs)