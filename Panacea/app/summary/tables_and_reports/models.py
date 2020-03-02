from django.db import models

class stylesheets(models.Model):
    transit_revenue = models.CharField(max_length=200, blank=True, null=True)
    transit_expense = models.CharField(max_length=200, blank=True, null=True)
    ferry_expense = models.CharField(max_length=200, blank=True, null=True)
    ferry_revenue = models.CharField(max_length=200, blank=True, null=True)
    transit_data = models.CharField(max_length=200, blank=True, null=True)
    ferry_data = models.CharField(max_length=200, blank=True, null=True)
    cp_data = models.CharField(max_length=200, blank=True, null=True)
    cp_revenue_source = models.CharField(max_length=200, blank=True, null=True)
    cp_revenue_federal = models.CharField(max_length=200, blank=True, null=True)


class statewide_measures(models.Model):
    title = models.CharField(max_length=200, null=True, blank=True)
    transit_data_files = models.CharField(max_length=500, blank=True, null=True)
    data_type = models.CharField(max_length=40, null=True, blank=True)
    measure_type = models.CharField(max_length=40, null=True, blank=True)




# class ending_balance_categories(models.Model):
#     ending_balance_category = models.CharField(max_length=100, blank=False, null=False)
#     def __str__(self):
#         return self.ending_balance_category
#
#
# class ending_balances(models.Model):
#     ending_balance_category = models.ForeignKey(ending_balance_categories, on_delete=models.PROTECT ,related_name = '+')
#     ending_balance_value = models.FloatField()
#     year = models.IntegerField(blank=True, null=True)
#     organization = models.ForeignKey(organization, on_delete=models.PROTECT, blank=True, null=True)
#     report_by = models.ForeignKey(custom_user, on_delete=models.PROTECT, blank=True, null=True)
#     comments = models.TextField(blank=True, null=True)
#     history = HistoricalRecords()


# class ending_balance_categories(models.Model):
#     ending_balance_category = models.CharField(max_length=100, blank=False, null=False)
#     def __str__(self):
#         return self.ending_balance_category
#
#
# class ending_balances(models.Model):
#     ending_balance_category = models.ForeignKey(ending_balance_categories, on_delete=models.PROTECT ,related_name = '+')
#     ending_balance_value = models.FloatField()
#     year = models.IntegerField(blank=True, null=True)
#     organization = models.ForeignKey(organization, on_delete=models.PROTECT, blank=True, null=True)
#     report_by = models.ForeignKey(custom_user, on_delete=models.PROTECT, blank=True, null=True)
#     comments = models.TextField(blank=True, null=True)
#     history = HistoricalRecords()
