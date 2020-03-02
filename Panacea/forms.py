from django import forms
from django.forms import BaseModelFormSet, BaseModelForm, ModelForm
from django.forms.formsets import BaseFormSet
from django.contrib.auth import password_validation, login
from django.contrib.auth.forms import UserChangeForm, AuthenticationForm
import datetime

from Panacea.utilities import find_user_organization, find_vanpool_organizations, calculate_percent_change
from .models import custom_user, \
    profile, \
    organization, \
    ReportType, \
    cover_sheet, \
    transit_data, expense, revenue, revenue_source, transit_mode, service_offered, transit_metrics, expense_source, \
    fund_balance, fund_balance_type, validation_errors, cover_sheet_review_notes

from phonenumber_field.formfields import PhoneNumberField
from localflavor.us.forms import USStateSelect, USZipCodeField
from django.core import serializers
from dateutil.relativedelta import relativedelta
from tempus_dominus.widgets import DatePicker
from .widgets import FengyuanChenDatePickerInput


# region shared


# endregion


# region vanpool

# endregion


# region summary






# class FormsetCleaner(BaseFormSet):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#     def clean(self):
#         """
#         Adds validation to check that no two links have the same anchor or URL
#         and that all links have both an anchor and URL.
#         """
#         if any(self.errors):
#             return

#
# class summary_expense_form(forms.ModelForm):
#
#     id = forms.IntegerField(disabled=True)
#     expense_source = forms.ModelChoiceField(disabled=True, queryset=expense_source.objects.all())
#     year = forms.IntegerField(disabled=True)
#
#     class Meta:
#         model = expense
#         fields = ["id", "expense_source", "year", "reported_value", "comments"]
#         widgets = {
#             'reported_value': forms.TextInput(attrs={'class': 'form-control'}),
#             'comments': forms.Textarea(attrs={'class': 'form-control', "rows": 3}),
#         }
#
#
# class fund_balance_form(forms.ModelForm):
#
#     id = forms.IntegerField(disabled=True)
#     fund_balance_type = forms.ModelChoiceField(disabled=True, queryset=fund_balance_type.objects.all())
#     year = forms.IntegerField(disabled=True)
#
#     class Meta:
#         model = fund_balance
#         fields = ["id", "fund_balance_type", "year", "reported_value", "comments"]
#         widgets = {
#             'reported_value': forms.TextInput(attrs={'class': 'form-control'}),
#             'comments': forms.Textarea(attrs={'class': 'form-control', "rows": 3}),
#         }
#
#
# class summary_revenue_form(forms.ModelForm):
#
#     id = forms.IntegerField(disabled=True)
#     revenue_source = forms.ModelChoiceField(disabled=True, queryset=revenue_source.objects.all())
#     year = forms.IntegerField(disabled=True)
#
#     class Meta:
#         model = revenue
#         fields = ["id", "revenue_source", "year", "reported_value", "comments"]
#         queryset = revenue_source.objects.all()
#         widgets = {
#             'specific_revenue_value': forms.NumberInput(attrs={'class': 'form-control'}),
#             'comments': forms.Textarea(attrs={'class': 'form-control', "rows": 3}),
#         }
#
#
# class transit_data_form(forms.ModelForm):
#
#     id = forms.IntegerField(disabled=True)
#     metric = forms.ModelChoiceField(disabled=True, queryset=transit_metrics.objects.all())
#     year = forms.IntegerField(disabled=True)
#
#     def clean(self):
#         cleaned_data = super(transit_data_form, self).clean()
#         current_year = datetime.now().year-1
#         if cleaned_data['year'] == current_year:
#             if cleaned_data['metric_value'] == None:
#                 pass
#             else:
#                 previous_year = current_year -1
#                 org_id  = cleaned_data['id'].__getattribute__('organization_id')
#                 metric_id = cleaned_data['id'].__getattribute__('metric_id')
#                 mode_id = cleaned_data['id'].__getattribute__('mode_id')
#                 previous_metric_value = transit_data.objects.filter(organization_id=org_id, metric_id = metric_id, year= previous_year, mode_id = mode_id).values('metric_value')
#                 percent_change = calculate_percent_change(cleaned_data['metric_value'], previous_metric_value[0]['metric_value'])
#                 if percent_change > 15 and cleaned_data['comments'] == '':
#                     raise forms.ValidationError('The following data has increased more than 15%. Please revise the data or provide an explanatory comment')
#                 elif percent_change < -15 and cleaned_data['comments'] == '':
#                     raise forms.ValidationError('The following data has declined more than 15%. Please revise the data or provide an explanatory comment')
#             return cleaned_data
#         else:
#             return cleaned_data
#
#     class Meta:
#         model = transit_data
#         fields = ['id', 'transit_metric', 'year', 'reported_value', 'comments']
#         widgets = {
#             'reported_value': forms.TextInput(attrs={'class': 'form-control'}),
#             'comments': forms.Textarea(attrs={'class': 'form-control', "rows": 3}),
#         }
#
#
# class validation_error_form(forms.ModelForm):
#     class Meta:
#         model = validation_errors
#         fields = ['error_resolution', 'year', 'error', 'administration_of_mode', 'transit_mode']
#         widgets = {
#             'error_resolution': forms.Textarea(attrs={'class': 'form-control', "rows": 3}),
#             'year': forms.NumberInput(attrs = {'class': 'form-control', 'readonly': 'readonly'}),
#             'error': forms.Textarea(attrs={'rows':3, 'readonly': 'readonly'}),
#             'administration_of_mode': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
#             'transit_mode': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
#             'id': forms.NumberInput(attrs={ 'class': 'form-control','readonly':'readonly'})
#         }


class email_contact_form(forms.Form):
    from_email = forms.EmailField(required=True, label="Sender Email")
    subject = forms.CharField(required=True, label="Subject of Message")
    message = forms.CharField(widget=forms.Textarea, required=True)


# class source_id_formset(BaseModelFormSet):
#     def __init__(self, source_ids, year, my_user, *args, **kwargs):
#         super(source_id_formset, self).__init__(*args, **kwargs)
#         self.source_ids = source_ids
#         self.year = year
#         self.my_user = my_user
#
#     def get_form_kwargs(self, form_index):
#         form_kwargs = super(source_id_formset, self).get_form_kwargs(form_index)
#         if form_index < len(self.source_ids):
#             form_kwargs = {'source_id': self.source_ids[form_index],
#                            'year': self.year,
#                            'my_user': self.my_user}
#         else:
#             form_kwargs = {'source_id': None,
#                            'year': self.year,
#                            'my_user': self.my_user}
#
#         print(form_kwargs)
#         return form_kwargs


# class summary_expense_form(base_summary_expense_form):
#
#     def __init__(self, year, my_user, source_id, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.source_id = source_id
#         self.year = year
#         self.my_user = my_user
#
#     def save(self, commit=True):
#         instance = super().save(commit=False)
#         instance.specific_expense_source_id = self.source_id
#         instance.organization = find_user_organization(self.my_user.id)
#         instance.year = self.year
#         instance.report_by = self.my_user
#         instance.save()


# endregion


class change_user_org(forms.ModelForm):
    class Meta:
        model = profile
        fields = ['custom_user', 'organization']
        widgets = {
            'custom_user': forms.Select(),
            'organization': forms.Select(),
        }