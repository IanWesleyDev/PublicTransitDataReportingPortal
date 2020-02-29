from Panacea.models import *


class revenue_source(models.Model):
    LEVIATHANS = (
        ('Federal', 'Federal'),
        ('State', 'State'),
        ('Local', 'Local'),
        ('Other', 'Other')
    )

    FUNDING_KIND = (
        ('Capital', 'Capital'),
        ('Operating', 'Operating')
    )

    TRUE_FALSE_CHOICES = (
        (True, 'inactive'),
        (False, 'active')
    )

    name = models.CharField(max_length=120, null=True, blank=True)
    order_in_summary = models.IntegerField(null=True, blank=True)
    government_type = models.CharField(max_length=100, choices=LEVIATHANS, null=True, blank=True)
    funding_type = models.CharField(max_length=30, choices=FUNDING_KIND, null=True, blank=True)
    agency_classification = models.ManyToManyField(summary_organization_type, blank=True)
    heading = models.CharField(max_length = 200, null=True, blank = True)
    inactive_flag = models.BooleanField(default=False, choices=TRUE_FALSE_CHOICES)

    def __str__(self):
        return self.name


class revenue(models.Model):
    organization = models.ForeignKey(organization, on_delete=models.PROTECT, related_name='+')
    year = models.IntegerField()
    revenue_source = models.ForeignKey(revenue_source, on_delete=models.PROTECT, related_name='+')
    reported_value = models.FloatField(null=True, blank=True)
    report_by = models.ForeignKey(custom_user, on_delete=models.PROTECT, blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    history = HistoricalRecords()


class expense_source(models.Model):
    name = models.CharField(max_length=100)
    heading = models.CharField(max_length=200, null=True, blank=True)
    agency_classification = models.ManyToManyField(summary_organization_type, blank=True)

    def __str__(self):
        return self.name


class expense(models.Model):

    organization = models.ForeignKey(organization, on_delete=models.PROTECT, related_name='+')
    year = models.IntegerField()
    expense_source = models.ForeignKey(expense_source, on_delete=models.PROTECT, related_name='+')
    reported_value = models.IntegerField(blank=True, null=True)
    report_by = models.ForeignKey(custom_user, on_delete=models.PROTECT, blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    # history = HistoricalRecords()

    class Meta:
        constraints = [
            UniqueConstraint(fields=['organization', 'year', 'expense_source'], name='unique_source_report'),
        ]


class transit_metrics(models.Model):
    FORM_MASKING_CLASSES = (
        ("Int", "Int"),
        ("Float", "Float"),
        ("Money", "Money"),
    )

    name = models.CharField(max_length=120)
    agency_classification = models.ManyToManyField(summary_organization_type, blank=True)
    order_in_summary = models.IntegerField(null=True, blank=True)
    form_masking_class = models.CharField(max_length=25, choices=FORM_MASKING_CLASSES, null=True, blank=True)

    def __str__(self):
        return self.name


class transit_data(models.Model):

    DO_OR_PT = (
        ('Direct Operated', 'Direct Operated'),
        ('Purchased', 'Purchased')
    )

    organization = models.ForeignKey(organization, on_delete=models.PROTECT, related_name='+')
    year = models.IntegerField()
    transit_mode = models.ForeignKey(transit_mode, on_delete=models.PROTECT, related_name='+')
    # TODO remove rollup_mode
    rollup_mode = models.ForeignKey(rollup_mode, on_delete=models.PROTECT,  related_name='+', blank=True, null=True)
    administration_of_mode = models.CharField(max_length=80, choices=DO_OR_PT)
    transit_metric = models.ForeignKey(transit_metrics, on_delete=models.PROTECT, related_name='+')
    reported_value = models.FloatField(blank=True, null=True)
    report_by = models.ForeignKey(custom_user, on_delete=models.PROTECT, blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    history = HistoricalRecords()

    #TODO make this contraint work

    # class Meta:
    #     unique_together = ['year', 'transit_mode', 'transit_metric', 'organization', 'administration_of_mode']


class fund_balance_type(models.Model):
    name = models.CharField(max_length=100)
    heading = models.CharField(max_length=50, default = 'Ending Balances, December 31')
    agency_classification = models.ManyToManyField(summary_organization_type, blank=True)

    def __str__(self):
        return self.name


class fund_balance(models.Model):
    organization = models.ForeignKey(organization, on_delete=models.PROTECT, related_name='+')
    year = models.IntegerField()
    fund_balance_type = models.ForeignKey(fund_balance_type, on_delete=models.PROTECT, related_name='+')
    reported_value = models.IntegerField(blank=True, null=True)
    report_by = models.ForeignKey(custom_user, on_delete=models.PROTECT, blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    heading = models.CharField(max_length= 50, blank=True, null=True, default = 'Ending Balances, December 31')
    history = HistoricalRecords()

    class Meta:
        constraints = [
            UniqueConstraint(fields=['organization', 'year', 'fund_balance_type'], name='unique_end_balance'),
        ]
