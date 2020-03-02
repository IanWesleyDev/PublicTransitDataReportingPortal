from dateutil.relativedelta import relativedelta
from django import forms

from Panacea.vanpool.models import *
from Panacea.user_and_org.models import *
from Panacea.utilities import find_vanpool_organizations


class VanpoolMonthlyReport(forms.ModelForm):

    def __init__(self, user_organization, record_id, report_month, report_year, *args, **kwargs):
        self.report_month = report_month
        self.report_year = report_year
        self.user_organization = user_organization
        self.record_id = record_id
        super(VanpoolMonthlyReport, self).__init__(*args, **kwargs)

    changeReason = forms.CharField(required=False, widget=forms.Textarea(
        attrs={'class': 'form-control input-sm', 'rows': 3, 'display': False})
                                   )

    acknowledge_validation_errors = forms.BooleanField(
        label='Check this box to confirm that your submitted numbers are correct, even though there are validation errors.',
        widget=forms.CheckboxInput(attrs={'class': 'checkbox', 'style': 'zoom:200%;margin-right:.35rem'}),
        required=False)

    def validator_method(self):

        # instantiate the error list
        error_list = []

        # Validation is not run on these fields
        untracked_categories = ['vanpool_group_starts',
                                'vanpool_group_folds',
                                'vans_available',
                                'loaner_spare_vans_in_fleet',
                                'average_riders_per_van',
                                'average_round_trip_miles',
                                'changeReason',
                                'data_change_record',
                                'acknowledge_validation_errors']

        report_month = self.report_month
        report_year = self.report_year
        if report_month == 1:
            report_year = report_year - 1
            report_month = 12
        else:
            report_month = report_month - 1

        vp_ops = vanpool_report.objects.filter(organization_id=self.user_organization,
                                               report_year=report_year,
                                               report_month=report_month).values('vanpool_groups_in_operation')
        if vp_ops[0]['vanpool_groups_in_operation'] == None:
            raise forms.ValidationError('You must fill out the data for the previous month first. Please refer to the previous reporting month')
            error_list.append('You must fill out the data for the previous month first. Please refer to the previous reporting month')
            return error_list
        else:
            for category in self.cleaned_data.keys():
                if self.cleaned_data[category] == None:
                    continue
                if category in untracked_categories:
                    continue

                new_data = self.cleaned_data[category]
                old_data = vanpool_report.objects.filter(organization_id=self.user_organization,
                                                         vanpool_groups_in_operation__isnull=False,
                                                         report_year=report_year,
                                                         report_month=report_month).values(category)
                old_data = old_data[0][category]

                # Should not happen but in case there is old data that is missing a value (came up during testing)
                if old_data is None:
                    continue
                if category == 'vanpool_groups_in_operation':
                    old_van_number = vanpool_report.objects.filter(
                        organization_id=self.user_organization,
                        report_year=report_year,
                        report_month=report_month).values('vanpool_groups_in_operation', 'vanpool_group_starts',
                                                          'vanpool_group_folds')
                    old_van_number = old_van_number[0]
                    if new_data != (
                            int(old_van_number['vanpool_groups_in_operation']) + int(old_van_number['vanpool_group_starts']) -
                            int(old_van_number['vanpool_group_folds'])):
                        old_total = int(old_van_number['vanpool_groups_in_operation']) + int(old_van_number['vanpool_group_starts']) -int(old_van_number['vanpool_group_folds'])
                        error_list.append(
                            'The Vanpool Groups in Operation are not equal to the projected number of vanpool groups in operation of {}, based on the {} fold(s) and {} start(s) recorded last month.'.format(old_total,old_van_number['vanpool_group_starts'], old_van_number['vanpool_group_folds']))

                if category == 'vanshare_groups_in_operation':
                    old_van_number = vanpool_report.objects.filter(
                        organization_id=self.user_organization,
                        report_year=report_year,
                        report_month=report_month).values('vanshare_groups_in_operation', 'vanshare_group_starts',
                                                          'vanshare_group_folds')
                    old_van_number = old_van_number[0]
                    if new_data != (
                            int(old_van_number['vanshare_groups_in_operation']) + int(old_van_number['vanshare_group_starts']) -int(old_van_number['vanshare_group_folds'])):
                        old_total = int(old_van_number['vanshare_groups_in_operation']) + int(old_van_number['vanshare_group_starts']) -int(old_van_number['vanshare_group_folds'])
                        error_list.append(
                            'The Vanshare Groups in Operation are not equal to the projected number of vanshare groups in operation of {}, based on the {} fold(s) and {} start(s) recorded last month.'.format(old_total, old_van_number['vanshare_group_folds'],old_van_number['vanshare_group_starts'] ))

                if new_data > old_data * 1.2:
                    category = category.replace('_', ' ')
                    category = category.title()
                    error_list.append('{} have increased more than 20%. Please confirm this number.'.format(category))

                elif new_data < old_data * 0.8:
                    category = category.replace('_', ' ')
                    category = category.title()
                    error_list.append('{} have decreased more than 20%. Please confirm this number'.format(category))

                if category == 'vanpool_groups_in_operation':
                    old_van_number = vanpool_report.objects.filter(
                        organization_id=self.user_organization,
                        report_year=report_year,
                        report_month=report_month).values('vanpool_groups_in_operation', 'vanpool_group_starts', 'vanpool_group_folds')
                    old_van_number = old_van_number[0]

                    if new_data != (old_van_number['vanpool_groups_in_operation'] + old_van_number['vanpool_group_starts'] - old_van_number['vanpool_group_folds']):
                        error_list.append('The Vanpool Groups in Operation do not reflect the folds and started recorded last month')

            return error_list

    def clean(self):
        cleaned_data = super(VanpoolMonthlyReport, self).clean()
        # try except block because acknowledge validation errors only exists after the validation has taken place
        try:
            if cleaned_data['acknowledge_validation_errors'] == True:
                return cleaned_data
            else:
                raise NameError('run_validator')
        except:
            error_list = self.validator_method()
            if len(error_list) > 0:
                raise forms.ValidationError(error_list)
            return cleaned_data

    class Meta:
        model = vanpool_report
        exclude = ('report_date', 'report_year', 'report_month', 'report_by', 'organization', 'report_type',
                   'report_due_date')
        widgets = {
            'vanshare_groups_in_operation': forms.TextInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'vanshare_group_starts': forms.TextInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'vanshare_group_folds': forms.TextInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'vanshare_passenger_trips': forms.TextInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'vanshare_miles_traveled': forms.TextInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'vanpool_groups_in_operation': forms.TextInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'vanpool_group_starts': forms.TextInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'vanpool_group_folds': forms.TextInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'vans_available': forms.TextInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'loaner_spare_vans_in_fleet': forms.TextInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'vanpool_passenger_trips': forms.TextInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'vanpool_miles_traveled': forms.TextInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'average_riders_per_van': forms.TextInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'average_round_trip_miles': forms.TextInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'operating_cost': forms.TextInput(
                attrs={'required': False, 'class': 'form-control input-sm'}),
            'frequency_of_claims': forms.TextInput(
                attrs={'required': False, 'class': 'form-control input-sm'}),

        }

    def save(self, commit=True):
        instance = super(VanpoolMonthlyReport, self).save(commit=False)
        if commit:
            instance.save()
        return instance


# TODO rename this form to something less generic
class vanpool_metric_chart_form(forms.Form):
    MEASURE_CHOICES_DICT = {
        "total_miles_traveled": "Total Miles Traveled",
        "total_passenger_trips": "Total Passenger Trips",
        "average_riders_per_van": "Average Riders per Van",
        "average_round_trip_miles": "Average Round Trip Miles",
        "total_groups_in_operation": "Total Groups in Operation",
        "vans_available": "Vans Available",
        "loaner_spare_vans_in_fleet": "Loaner Spare Vans in Fleet"
    }

    MEASURE_CHOICES = (
        ("total_miles_traveled", "Total Miles Traveled"),
        ("total_passenger_trips", "Total Passenger Trips"),
        ("average_riders_per_van", "Average Riders per Van"),
        ("average_round_trip_miles", "Average Round Trip Miles"),
        ("total_groups_in_operation", "Total Groups in Operation"),
        ("vans_available", "Vans Available"),
        ("loaner_spare_vans_in_fleet", "Loaner Spare Vans in Fleet")
    )

    ORGANIZATION_CHOICES = organization.objects.all().values('name')
    TIMEFRAME_CHOICES = (
        (3, "Three Months"),
        (6, "Six Months"),
        (12, "One Year"),
        (36, "Three Years"),
        (60, "Five Years"),
        (120, "Ten Years"),
        (999, "All")
    )

    chart_measure = forms.CharField(widget=forms.Select(choices=MEASURE_CHOICES,
                                                        attrs={'class': 'form-control my_chart_control',
                                                               'data-form-name': "vanpool_metric_chart_form"}))
    chart_organizations = forms.ModelChoiceField(queryset=find_vanpool_organizations().order_by('name'), empty_label=None,
                                                 widget=forms.CheckboxSelectMultiple(
                                                     attrs={'class': 'form-check checkbox-grid',
                                                            'data-form-name': "vanpool_metric_chart_form"}))
    chart_time_frame = forms.CharField(widget=forms.Select(choices=TIMEFRAME_CHOICES,
                                                           attrs={'class': 'form-control my_chart_control',
                                                                  'data-form-name': "vanpool_metric_chart_form"}))


class statewide_summary_settings(forms.Form):
    INCLUDE_YEARS_CHOICES = (
        (1, "One Year"),
        (2, "Two Years"),
        (3, "Three Years"),
        (5, "Five Years"),
        (10, "Ten Years"),
        (99, "All")
    )

    INCLUDE_REGION_CHOICES = (
        ("Puget Sound", "Puget Sound"),
        ("Outside Puget Sound", "Outside Puget Sound"),
        ("Statewide", "Statewide")
    )

    include_years = forms.CharField(widget=forms.Select(choices=INCLUDE_YEARS_CHOICES,
                                                        attrs={'class': 'form-control',
                                                               'data-form-name': "vanpool_metric_chart_form"}))

    include_regions = forms.CharField(widget=forms.Select(choices=INCLUDE_REGION_CHOICES,
                                                          attrs={'class': 'form-control ',
                                                                 'data-form-name': "vanpool_metric_chart_form"}))
    include_agency_classifications = forms.MultipleChoiceField(choices=organization.AGENCY_CLASSIFICATIONS,
                                                               widget=forms.CheckboxSelectMultiple(
                                                                   attrs={'class': 'form-check',
                                                                          'data-form-name': "vanpool_metric_chart_form"}))


class submit_a_new_vanpool_expansion(forms.ModelForm):
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

    queryset = organization.objects.all().order_by('name')
    organization = forms.ModelChoiceField(queryset=queryset,
                                          widget=forms.Select(attrs={'class': 'form-control'}))
    date_of_award = forms.DateTimeField(input_formats=['%Y-%m-%d'],
                                        widget=forms.DateInput(attrs={'class': 'form-control'}))
    latest_vehicle_acceptance = forms.DateTimeField(input_formats=['%Y-%m-%d'],
                                                    widget=forms.DateInput(attrs={'class': 'form-control'}))

    awarded_biennium = forms.CharField(widget=forms.Select(choices = CHOICES, attrs = {'class': 'form-control'}))

    notes = forms.CharField(widget = forms.Textarea(attrs={'class': 'form-control', 'rows':3}), required = False)



    class Meta:
        model = vanpool_expansion_analysis

        fields = ['organization', 'date_of_award', 'expansion_vans_awarded', 'latest_vehicle_acceptance',
                  'vanpools_in_service_at_time_of_award', 'notes', 'award_biennium', 'expansion_goal', 'deadline']
        required = ['organization', 'date_of_award', 'expansion_vans_awarded', 'latest_vehicle_acceptance',
                    'extension_granted', 'vanpools_in_service_at_time_of_award', 'expired', 'vanpool_goal_met']

        labels = {'organization': "Please Select Your Agency",
                  'date_of_award': 'When was the vanpool expansion awarded? Use format YYYY-MM-DD',
                  'expansion_vans_awarded': 'Number of vans awarded in the expansion',
                  'latest_vehicle_acceptance': 'Latest date that vehicle was accepted? Use format YYYY-MM-DD',
                  'extension_granted': 'Extenstion Granted? Set this to no',
                  'vanpools_in_service_at_time_of_award': 'Vanpools in service at time of award',
                  'expired': 'Has the expansion award expired? Set this to no (as it is used later for reporting)',
                  'Notes': False
                  }

        widgets = {
            # 'date_of_award': forms.DateInput(attrs={'class': 'form-control'}),
            'latest_vehicle_acceptance': forms.DateInput(attrs={'class': 'form-control'}),
            'expansion_vans_awarded': forms.NumberInput(attrs={'class': 'form-control'}),
            'vanpools_in_service_at_time_of_award': forms.NumberInput(attrs={'class': 'form-control'}),

        }


class Modify_A_Vanpool_Expansion(forms.ModelForm):
    class Meta:
        model = vanpool_expansion_analysis
        latest_vehicle_acceptance = forms.DateTimeField(input_formats=['%Y-%m-%d'],
                                                        widget=forms.DateInput(attrs={'class': 'form-control'}))

        fields = ['expansion_vans_awarded', 'latest_vehicle_acceptance', 'extension_granted', 'expired', 'notes']
        widgets = {'expansion_vans_awarded': forms.NumberInput(attrs={'class': 'form-control'}),
                   'notes': forms.Textarea(attrs={'class': 'form-control', 'rows':3, 'style': 'max-width:600px'}),
                   'extension_granted': forms.CheckboxInput(attrs={'class': 'form-control', 'style': 'width:auto;zoom:200%'}),
                   'expired': forms.CheckboxInput(attrs={'class': 'form-control',
                                                         'style': 'width:auto;zoom:200%;float:left;margin-right:0.5rem',
                                                         'disabled': 'disabled'})
                   }

        #TODO a modal form here for if an extension is granted and one wnated to change the deadline, since at this point the deadline already exists
    def save(self, commit=True):
        instance = super(Modify_A_Vanpool_Expansion, self).save(commit=False)
        self.cleaned_data['deadline'] = self.cleaned_data['latest_vehicle_acceptance'] + relativedelta(months=+18)
        if commit:
            instance.save()
        return instance


class organisation_summary_settings(forms.Form):
    INCLUDE_YEARS_CHOICES = (
        (1, "One Year"),
        (2, "Two Years"),
        (3, "Three Years"),
        (5, "Five Years"),
        (10, "Ten Years"),
        (99, "All")
    )


    include_years = forms.CharField(widget=forms.Select(choices=INCLUDE_YEARS_CHOICES,
                                                        attrs={'class': 'form-control',
                                                               'data-form-name': "vanpool_metric_chart_form"}))
    summary_org = forms.ModelChoiceField(queryset=organization.objects.all(),
                                         widget=forms.Select(attrs={'class': 'form-control',
                                                                    'data-form-name': "vanpool_metric_chart_form"}))