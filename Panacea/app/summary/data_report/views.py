from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from Panacea.app.summary.classes.builders import SummaryDataEntryBuilder, SummaryDataEntryTemplateData
from Panacea.app.summary.coversheet.forms import service_offered_form
from Panacea.app.summary.data_report.models import *
from Panacea.app.summary.misc.models import transit_mode
from Panacea.app.summary.review_tracking.models import *
from Panacea.decorators import group_required
from Panacea.utilities import get_current_summary_report_year, find_user_organization, get_all_data_steps_completed, \
    find_user_organization_id


@login_required(login_url='/Panacea/login')
@group_required('Summary reporter', 'WSDOT staff')
def data_submitted(request):
    data_status = summary_report_status.objects.get(year=get_current_summary_report_year(), organization=find_user_organization(request.user.id)).data_report_status
    return render(request, 'pages/summary/data_submitted.html', {'data_status': data_status})


@login_required(login_url='/Panacea/login')
@group_required('Summary reporter', 'WSDOT staff')
def summary_modes(request):
    org = find_user_organization(request.user.id)

    # TODO add in date time of changes and user id to this dataset date time as native, foreign key for user
    if request.method == 'POST':
        form = service_offered_form(data=request.POST)
        if form.is_valid():
            print(form.is_valid())
            instance, created = service_offered.objects.get_or_create(organization_id=org.id,
                                                                      transit_mode=form.cleaned_data["transit_mode"],
                                                                      administration_of_mode=form.cleaned_data[
                                                                          "administration_of_mode"])
            if not created:
                print("not created")
                messages.error(request, "This name has already been added")
    else:
        form = service_offered_form()
    print(form)
    modes = service_offered.objects.filter(organization_id=org).all()
    ready_to_submit = get_all_data_steps_completed(find_user_organization_id(request.user.id))
    return render(request, 'pages/summary/summary_modes.html', {'form': form,
                                                                'modes': modes,
                                                                'org': org,
                                                                'ready_to_submit': ready_to_submit})


@login_required(login_url='/Panacea/login')
@group_required('Summary reporter', 'WSDOT staff')
def accept_modes(request):
    org_progress, created = summary_organization_progress.objects.get_or_create(organization=find_user_organization(request.user.id))
    org_progress.confirm_service = True
    org_progress.save()
    return redirect('summary_reporting')


@login_required(login_url='/Panacea/login')
@group_required('Summary reporter', 'WSDOT staff')
def delete_summary_mode(request, name, admin_of_mode):
    if transit_mode.objects.filter(name=name).count() < 1:
        raise ValueError("invalid name - transit mode")
    elif admin_of_mode in transit_data.DO_OR_PT:
        raise ValueError("invalid name - administration of mode")
    else:
        user_id = request.user.id
        transit_mode_id = transit_mode.objects.get(name=name).id
        user_org_id = profile.objects.get(custom_user_id=user_id).organization_id
        service_to_delete = service_offered.objects.get(organization_id=user_org_id,
                                                        administration_of_mode=admin_of_mode,
                                                        transit_mode_id=transit_mode_id)
        service_to_delete.delete()
        return redirect('summary_modes')

@login_required(login_url='/Panacea/login')
@group_required('Summary reporter', 'WSDOT staff')
def summary_reporting(request, report_type=None, form_filter_1=None, form_filter_2=None):
    user_org = find_user_organization(request.user.id)

    if report_type is None:
        report_type = "transit_data"

    requested_form = SummaryDataEntryBuilder(report_type, user_org, form_filter_1=form_filter_1,
                                             form_filter_2=form_filter_2)
    if request.method == 'POST':
        requested_form.save_with_post_data(request.POST)
        return requested_form.go_to_next_form()

    template_data = SummaryDataEntryTemplateData(requested_form, report_type)

    ready_to_submit = get_all_data_steps_completed(find_user_organization_id(request.user.id))

    return render(request, 'pages/summary/summary_reporting.html', {'template_data': template_data,
                                                                    'ready_to_submit': ready_to_submit})


@login_required(login_url='/Panacea/login')
@group_required('Summary reporter', 'WSDOT staff')
def submit_data(request):
    ready_to_submit = get_all_data_steps_completed(find_user_organization_id(request.user.id))
    return render(request, 'pages/summary/submit_data.html', {'ready_to_submit': ready_to_submit})


@login_required(login_url='/Panacea/login')
@group_required('Summary reporter', 'WSDOT staff')
def submit_data_submit(request):
    status = summary_report_status.objects.get(year=get_current_summary_report_year(), organization=find_user_organization(request.user.id))
    status.data_report_submitted_for_review = True
    status.data_report_status = "With WSDOT"
    status.save()
    return redirect('dashboard')