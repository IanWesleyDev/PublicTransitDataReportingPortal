from django import forms
from Panacea.app.user_and_org.models import *
from Panacea.app.summary.coversheet.models import *
from Panacea.app.summary.misc.models import *


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