from django.db import models
from Panacea.models import *


class vanpool_report(models.Model):
    REPORT_MONTH = (
        (1, 'January'),
        (2, 'February'),
        (3, 'March'),
        (4, 'April'),
        (5, 'May'),
        (6, 'June'),
        (7, 'July'),
        (8, 'August'),
        (9, 'September'),
        (10, 'October'),
        (11, 'November'),
        (12, 'December'),
    )

    report_type = models.ForeignKey(ReportType, on_delete=models.PROTECT)
    report_year = models.IntegerField()
    report_month = models.IntegerField(choices=REPORT_MONTH)
    # TODO we should come back and look at if these need to be here
    # report_due_date = models.DateField()
    #report_day = models.IntegerField(default = 1, null=True)
    report_date = models.DateTimeField(default=None, null=True)
    update_date = models.DateTimeField(auto_now=True, blank=True, null=True)
    report_by = models.ForeignKey(custom_user, on_delete=models.PROTECT, blank=True, null=True)
    organization = models.ForeignKey(organization, on_delete=models.PROTECT)
    vanshare_groups_in_operation = models.IntegerField(blank=True, null=True)
    vanshare_group_starts = models.IntegerField(blank=True, null=True)
    vanshare_group_folds = models.IntegerField(blank=True, null=True)
    vanshare_passenger_trips = models.IntegerField(blank=True, null=True)
    vanshare_miles_traveled = models.FloatField(blank=True, null=True)
    vanpool_groups_in_operation = models.IntegerField(blank=True, null=True)
    vanpool_group_starts = models.IntegerField(blank=True, null=True)
    vanpool_group_folds = models.IntegerField(blank=True, null=True)
    vans_available = models.IntegerField(blank=True, null=True)
    loaner_spare_vans_in_fleet = models.IntegerField(blank=True, null=True)
    vanpool_passenger_trips = models.IntegerField(blank=True, null=True)
    vanpool_miles_traveled = models.FloatField(blank=True, null=True)
    average_riders_per_van = models.FloatField(blank=True, null=True, validators=[MaxValueValidator(15)])
    average_round_trip_miles = models.FloatField(blank=True, null=True)
    frequency_of_claims = models.FloatField(blank=True, null=True)
    operating_cost = models.FloatField(blank=True, null=True)
    history = HistoricalRecords()

    @property
    def report_due_date(self):
        month = self.report_month
        year = self.report_year + month // 12
        month = month % 12 + 1
        day = 1
        return datetime.date(year, month, day)


    @property
    def status(self):
        if self.report_date is None:
            if datetime.datetime.now().date() > self.report_due_date:
                return "Past due"
            else:
                return "Not due yet"
        elif self.report_date is not None:
            return "Submitted"
        else:
            return "Error"



    @property
    def report_year_month_label(self):
        return str(self.report_year) + " - " + str(self.report_month)

    @property
    def total_miles_traveled(self):
        result = sum(filter(None, {self.vanpool_miles_traveled, self.vanshare_miles_traveled}))
        if result == 0:
            result = None
        return result

    @property
    def total_passenger_trips(self):
        result = sum(filter(None, {self.vanpool_passenger_trips, self.vanshare_passenger_trips}))
        if result == 0:
            result = None
        return result

    @property
    def total_groups_in_operation(self):
        result = sum(filter(None, {self.vanpool_groups_in_operation, self.vanshare_groups_in_operation}))
        if result == 0:
            result = None
        return result

    def save(self, no_report_date=False, *args, **kwargs):
        if not no_report_date and self.report_date is None:
            self.report_date = datetime.datetime.now().date()
        super(vanpool_report, self).save(*args, **kwargs)

    class Meta:
        unique_together = ('organization', 'report_year', 'report_month',)


class vanpool_expansion_analysis(models.Model):
    # TODO change to our biennium function
    CHOICES = (
        ('11-13', '11-13'),
        ('13-15', '13-15'),
        ('15-17', '15-17'),
        ('17-19', '17-19'),
        ('19-21', '19-21'),
        ('21-23', '21-23'),
        ('23-25', '23-25'),
        ('25-27', '25-27')
    )

    organization = models.ForeignKey(organization, on_delete=models.PROTECT, related_name='+')
    vanpools_in_service_at_time_of_award = models.IntegerField(blank=True, null=True)
    date_of_award = models.DateField(blank=True, null=True)
    expansion_vans_awarded = models.IntegerField(blank=True, null=True)
    latest_vehicle_acceptance = models.DateField(blank=True, null=True)
    extension_granted = models.BooleanField(blank=False, null=True)
    vanpool_goal_met = models.BooleanField(blank=False, null=True)
    expired = models.BooleanField(blank=False, null=True)
    notes = models.TextField(blank=False, null=True)
    award_biennium = models.CharField(max_length=50, choices=CHOICES, blank=True, null=True)
    expansion_goal = models.IntegerField(blank=True, null=True)
    deadline = models.DateField(blank=True, null=True)
    service_goal_met_date = models.DateField(blank=True, null=True)
    max_vanpool_numbers = models.IntegerField(blank=True, null=True)
    max_vanpool_date = models.DateField(blank=True, null=True)
    latest_vanpool_number = models.IntegerField(blank=True, null=True)
    latest_report_date = models.DateField(blank=True, null=True)
    months_remaining = models.CharField(blank=True, null=True, max_length=20)
    organization_name = models.CharField(blank=True, null=True, max_length=100)
    history = HistoricalRecords()

    @property
    def adjusted_service_goal(self):
        return int(self.vanpools_in_service_at_time_of_award + round(self.expansion_vans_awarded*.8, 0))

    #TODO Change all the forms so we get good data, put various checks into the views page,
    @property
    def calculate_current_biennium(self):
        import datetime
        from Panacea.utilities import calculate_biennium
        return calculate_biennium(datetime.date.today())