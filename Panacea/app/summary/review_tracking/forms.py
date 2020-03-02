from django import forms
from Panacea.app.summary.review_tracking.models import *
from Panacea.app.summary.coversheet.models import *
from Panacea.app.summary.misc.models import *

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