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
from django.utils.translation import gettext, gettext_lazy as _
from phonenumber_field.formfields import PhoneNumberField
from localflavor.us.forms import USStateSelect, USZipCodeField
from django.core import serializers
from dateutil.relativedelta import relativedelta
from tempus_dominus.widgets import DatePicker
from .widgets import FengyuanChenDatePickerInput


# region shared
class CustomUserCreationForm(forms.ModelForm):
    """
    A form that creates a user, with no privileges, from the given username and
    password.
    """
    error_messages = {
        'password_mismatch': _("The two password fields didn't match."),
    }
    password1 = forms.CharField(
        label=False,
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control form-control-user', 'placeholder': 'Password'}),
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label=False,
        widget=forms.PasswordInput(
            attrs={'class': 'form-control form-control-user', 'placeholder': 'Enter Password Again'}),
        strip=False,
        help_text=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self._meta.model.USERNAME_FIELD in self.fields:
            self.fields[self._meta.model.USERNAME_FIELD].widget.attrs.update({'autofocus': True})

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password2

    def _post_clean(self):
        super()._post_clean()
        # Validate the password after self.instance is updated with form data
        # by super().
        password = self.cleaned_data.get('password2')
        if password:
            try:
                password_validation.validate_password(password, self.instance)
            except forms.ValidationError as error:
                self.add_error('password2', error)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()
        return user

    class Meta:
        model = custom_user
        fields = ('first_name', 'last_name', 'email')
        labels = {
            'first_name': False,
            'last_name': False,
            'email': False,
        }
        widgets = {
            'first_name': forms.TextInput(
                attrs={'class': 'form-control form-control-user', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control form-control-user', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(
                attrs={'class': 'form-control form-control-user', 'placeholder': 'Email Address'}),
        }


class custom_user_ChangeForm(forms.ModelForm):
    class Meta:
        model = custom_user
        fields = ('first_name', 'last_name', 'email')
        widgets = {
            'first_name': forms.TextInput(
                attrs={'class': 'form-control form-control-user', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control form-control-user', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(
                attrs={'class': 'form-control form-control-user', 'placeholder': 'Email Address'}),
        }


class ProfileSetup_PhoneAndOrg(forms.ModelForm):
    class Meta:
        model = profile
        fields = ('telephone_number', 'organization')
        widgets = {
            'telephone_number': forms.TextInput(
                attrs={'class': 'form-control form-control-user'})
        }


class user_profile_custom_user(forms.ModelForm):

    class Meta:
        model = custom_user
        fields = ('first_name', 'last_name', 'email')
        widgets = {
            'first_name': forms.TextInput(
                attrs={'class': 'form-control-plaintext'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control-plaintext', 'readonly': 'True'}),
            'email': forms.EmailInput(
                attrs={'class': 'form-control-plaintext', 'readonly': 'True'}),
        }


class user_profile_profile(forms.ModelForm):

    class Meta:
        model = profile
        queryset = organization.objects.all()
        fields = ('telephone_number', 'job_title')
        widgets = {
            'telephone_number': forms.TextInput(
                attrs={'class': 'form-control-plaintext', 'readonly': 'True'}),
            'job_title': forms.TextInput(
                attrs={'class': 'form-control-plaintext', 'readonly': 'True'})
        }


class PhoneOrgSetup(forms.ModelForm):
    queryset = organization.objects.all().order_by('name')

    telephone_number = PhoneNumberField(widget=forms.TextInput(attrs={'class': 'form-control form-control-user'}),
                                        label=_("Phone number:"), required=True)
    job_title = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control form-control-user'}),
                                required=True)
    organization = forms.ModelChoiceField(queryset=queryset,
                                          widget=forms.Select(attrs={'class': 'form-control form-control-user'}))

    class Meta:
        model = profile
        fields = ('telephone_number', 'job_title', 'organization')


class ReportSelection(forms.ModelForm):
    queryset = ReportType.objects.all()

    reports_on = forms.ModelMultipleChoiceField(queryset=queryset, label='',
                                                widget=forms.CheckboxSelectMultiple(choices=queryset,
                                                                                    attrs={'class': 'custom-checkbox'}))

    class Meta:
        model = profile
        fields = ('reports_on', )


class organization_profile(forms.ModelForm):
    class Meta:
        TRUE_FALSE_CHOICES = (
            (False, 'No'),
            (True, 'Yes')
        )

        model = organization
        fields = ('name', 'address_line_1', 'address_line_2', 'city', 'state', 'zip_code', 'vanshare_program',
                  'in_puget_sound_area', 'summary_organization_classifications')
        widgets = {
            'name': forms.TextInput(
                attrs={'class': 'form-control-plaintext', 'readonly': 'True', 'style': "width:350px"}),
            'address_line_1': forms.TextInput(
                attrs={'class': 'form-control-plaintext', 'readonly': 'True', 'style': "width:350px"}),
            'address_line_2': forms.TextInput(
                attrs={'class': 'form-control-plaintext', 'readonly': 'True', 'style': "width:350px"}),
            'city': forms.TextInput(
                attrs={'class': 'form-control-plaintext', 'readonly': 'True'}),
            'state': forms.Select(
                attrs={'class': 'form-control form-control-plaintext', 'readonly': 'True',
                       'style': 'pointer-events: none'}),
            'zip_code': forms.TextInput(
                attrs={'class': 'form-control-plaintext', 'readonly': 'True'}),
            'vanshare_program': forms.Select(choices=TRUE_FALSE_CHOICES,
                                             attrs={'class': 'form-control form-control-plaintext', 'readonly': 'True',
                                                    'style': 'pointer-events: none'}),
            'in_puget_sound_area': forms.Select(choices=TRUE_FALSE_CHOICES,
                                                attrs={'class': 'form-control-plaintext', 'readonly': 'True',
                                                       'style': 'pointer-events: none'}),
            'summary_organization_classifications': forms.Select(choices=organization.SUMMARY_ORG_CLASSIFICATIONS,
                                                                 attrs={'class': 'form-control-plaintext',
                                                                        'readonly': 'True',
                                                                        'style': 'pointer-events: none'}),

        }


class change_user_permissions_group(forms.ModelForm):
    class Meta:
        model = custom_user
        fields = ['first_name', 'last_name', 'email', 'groups', ]
        widgets = {
            'groups': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-inline no-bullet AJAX_instant_submit',
                                                          'data-form-name': "Admin_assignPermissions_all"}),
            'first_name': forms.TextInput(
                attrs={'class': 'form-control-plaintext', 'readonly': 'True',
                       'style': 'display: none; visibility: hidden'}),
            'last_name': forms.TextInput(
                attrs={'class': 'form-control-plaintext', 'readonly': 'True',
                       'style': 'display: none; visibility: hidden'}),
            'email': forms.TextInput(
                attrs={'class': 'form-control-plaintext', 'readonly': 'True',
                       'style': 'display: none; visibility: hidden'}),
        }


class request_user_permissions(forms.ModelForm):
    class Meta:
        model = custom_user
        fields = ['groups', ]
        widgets = {
            'groups': forms.CheckboxSelectMultiple(attrs={'class': 'form-check'})
        }



# endregion


# region vanpool

# endregion


# region summary

class organization_information(forms.ModelForm):
    class Meta:
        model = organization
        fields = ("summary_organization_classifications", )
        widgets = {
            'summary_organization_classifications': forms.Select(choices=organization.SUMMARY_ORG_CLASSIFICATIONS,
                                                                 attrs={'class': 'form-control form-control-plaintext',
                                                                        'readonly': 'True',
                                                                        'style': 'pointer-events: none'}),
        }


class cover_sheet_organization(forms.ModelForm):
    organization_logo_input = forms.FileField(required=False,
                                              widget=forms.FileInput(attrs={'class': 'my-custom-file-input',
                                                                            'accept': '.jpg, .jpeg, .png, .tif'}))

    class Meta:
        model = cover_sheet
        fields = ['executive_officer_first_name', 'executive_officer_last_name', 'executive_officer_title', 'service_website_url',
                  'service_area_description', 'congressional_districts', 'legislative_districts', 'type_of_government',
                  'governing_body']
        widgets = {
            'executive_officer_first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'executive_officer_last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'executive_officer_title': forms.TextInput(attrs={'class': 'form-control'}),
            'service_website_url': forms.URLInput(attrs={'class': 'form-control',
                                                         'label': 'Service website URL'}),
            'service_area_description': forms.TextInput(attrs={'class': 'form-control'}),
            'congressional_districts': forms.TextInput(attrs={'class': 'form-control'}),
            'legislative_districts': forms.TextInput(attrs={'class': 'form-control'}),
            'type_of_government': forms.TextInput(attrs={'class': 'form-control'}),
            'governing_body': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def clean_organization_logo_input(self):
        from Panacea.validators import validate_image_file
        image = self.cleaned_data.get('organization_logo_input')
        # import pdb; pdb.set_trace()

        print(image)
        if image is not None:
            print("validator")
            validate_image_file(image)


class service_offered_form(forms.ModelForm):

    class Meta:
        model = service_offered
        fields = ['administration_of_mode', 'transit_mode']
        widgets = {
            'transit_mode': forms.Select(choices=transit_mode.objects.all(), attrs={'class': 'form-control'}),
            'administration_of_mode': forms.Select(choices=service_offered.DO_OR_PT, attrs={'class': 'form-control'})
        }


class cover_sheet_service(forms.ModelForm):
    class Meta:
        model = cover_sheet
        fields = ['intermodal_connections', 'fares_description', 'service_and_eligibility',
                  'days_of_service', 'current_operations', 'revenue_service_vehicles',
                  'tax_rate_description']
        widgets = {
            'intermodal_connections': forms.Textarea(attrs={'class': 'form-control'}),
            'fares_description': forms.Textarea(attrs={'class': 'form-control'}),
            'service_and_eligibility': forms.Textarea(attrs={'class': 'form-control'}),
            'days_of_service': forms.TextInput(attrs={'class': 'form-control'}),
            'current_operations': forms.Textarea(attrs={'class': 'form-control'}),
            'revenue_service_vehicles': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_rate_description': forms.Textarea(attrs={'class': 'form-control'}),
        }


class cover_sheet_wsdot_review(forms.ModelForm):
    organization_logo_input = forms.FileField(required=False,
                                              widget=forms.FileInput(attrs={'class': 'my-custom-file-input',
                                                                            'accept': '.jpg, .jpeg, .png, .tif'}))

    class Meta:
        model = cover_sheet
        exclude = ['id', 'organization', 'transit_development_plan_url', 'monorail_ownership', 'community_planning_region',]

        widgets = {
            'executive_officer_first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'executive_officer_last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'executive_officer_title': forms.TextInput(attrs={'class': 'form-control'}),
            'service_website_url': forms.URLInput(attrs={'class': 'form-control',
                                                         'label': 'Service website URL'}),
            'service_area_description': forms.TextInput(attrs={'class': 'form-control'}),
            'congressional_districts': forms.TextInput(attrs={'class': 'form-control'}),
            'legislative_districts': forms.TextInput(attrs={'class': 'form-control'}),
            'type_of_government': forms.TextInput(attrs={'class': 'form-control'}),
            'governing_body': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'transit_mode': forms.Select(choices=transit_mode.objects.all(), attrs={'class': 'form-control'}),
            'administration_of_mode': forms.Select(choices=service_offered.DO_OR_PT, attrs={'class': 'form-control'}),
            'intermodal_connections': forms.Textarea(attrs={'class': 'form-control'}),
            'fares_description': forms.Textarea(attrs={'class': 'form-control'}),
            'service_and_eligibility': forms.Textarea(attrs={'class': 'form-control'}),
            'days_of_service': forms.TextInput(attrs={'class': 'form-control'}),
            'current_operations': forms.Textarea(attrs={'class': 'form-control'}),
            'revenue_service_vehicles': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_rate_description': forms.Textarea(attrs={'class': 'form-control'}),
        }

    def clean_organization_logo_input(self):
        from Panacea.validators import validate_image_file
        image = self.cleaned_data.get('organization_logo_input')
        # import pdb; pdb.set_trace()

        print(image)
        if image is not None:
            print("validator")
            validate_image_file(image)


class add_cover_sheet_review_note(forms.ModelForm):
    class Meta:
        model = cover_sheet_review_notes
        fields = ['note', ]
        widgets = {
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows':2}),
        }


class FormsetCleaner(BaseFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def clean(self):
        """
        Adds validation to check that no two links have the same anchor or URL
        and that all links have both an anchor and URL.
        """
        if any(self.errors):
            return


class summary_expense_form(forms.ModelForm):

    id = forms.IntegerField(disabled=True)
    expense_source = forms.ModelChoiceField(disabled=True, queryset=expense_source.objects.all())
    year = forms.IntegerField(disabled=True)

    class Meta:
        model = expense
        fields = ["id", "expense_source", "year", "reported_value", "comments"]
        widgets = {
            'reported_value': forms.TextInput(attrs={'class': 'form-control'}),
            'comments': forms.Textarea(attrs={'class': 'form-control', "rows": 3}),
        }


class fund_balance_form(forms.ModelForm):

    id = forms.IntegerField(disabled=True)
    fund_balance_type = forms.ModelChoiceField(disabled=True, queryset=fund_balance_type.objects.all())
    year = forms.IntegerField(disabled=True)

    class Meta:
        model = fund_balance
        fields = ["id", "fund_balance_type", "year", "reported_value", "comments"]
        widgets = {
            'reported_value': forms.TextInput(attrs={'class': 'form-control'}),
            'comments': forms.Textarea(attrs={'class': 'form-control', "rows": 3}),
        }


class summary_revenue_form(forms.ModelForm):

    id = forms.IntegerField(disabled=True)
    revenue_source = forms.ModelChoiceField(disabled=True, queryset=revenue_source.objects.all())
    year = forms.IntegerField(disabled=True)

    class Meta:
        model = revenue
        fields = ["id", "revenue_source", "year", "reported_value", "comments"]
        queryset = revenue_source.objects.all()
        widgets = {
            'specific_revenue_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'comments': forms.Textarea(attrs={'class': 'form-control', "rows": 3}),
        }


class transit_data_form(forms.ModelForm):

    id = forms.IntegerField(disabled=True)
    metric = forms.ModelChoiceField(disabled=True, queryset=transit_metrics.objects.all())
    year = forms.IntegerField(disabled=True)

    def clean(self):
        cleaned_data = super(transit_data_form, self).clean()
        current_year = datetime.now().year-1
        if cleaned_data['year'] == current_year:
            if cleaned_data['metric_value'] == None:
                pass
            else:
                previous_year = current_year -1
                org_id  = cleaned_data['id'].__getattribute__('organization_id')
                metric_id = cleaned_data['id'].__getattribute__('metric_id')
                mode_id = cleaned_data['id'].__getattribute__('mode_id')
                previous_metric_value = transit_data.objects.filter(organization_id=org_id, metric_id = metric_id, year= previous_year, mode_id = mode_id).values('metric_value')
                percent_change = calculate_percent_change(cleaned_data['metric_value'], previous_metric_value[0]['metric_value'])
                if percent_change > 15 and cleaned_data['comments'] == '':
                    raise forms.ValidationError('The following data has increased more than 15%. Please revise the data or provide an explanatory comment')
                elif percent_change < -15 and cleaned_data['comments'] == '':
                    raise forms.ValidationError('The following data has declined more than 15%. Please revise the data or provide an explanatory comment')
            return cleaned_data
        else:
            return cleaned_data

    class Meta:
        model = transit_data
        fields = ['id', 'transit_metric', 'year', 'reported_value', 'comments']
        widgets = {
            'reported_value': forms.TextInput(attrs={'class': 'form-control'}),
            'comments': forms.Textarea(attrs={'class': 'form-control', "rows": 3}),
        }


class validation_error_form(forms.ModelForm):
    class Meta:
        model = validation_errors
        fields = ['error_resolution', 'year', 'error', 'administration_of_mode', 'transit_mode']
        widgets = {
            'error_resolution': forms.Textarea(attrs={'class': 'form-control', "rows": 3}),
            'year': forms.NumberInput(attrs = {'class': 'form-control', 'readonly': 'readonly'}),
            'error': forms.Textarea(attrs={'rows':3, 'readonly': 'readonly'}),
            'administration_of_mode': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'transit_mode': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'id': forms.NumberInput(attrs={ 'class': 'form-control','readonly':'readonly'})
        }


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