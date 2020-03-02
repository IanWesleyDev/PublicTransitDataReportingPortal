from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, redirect
from django.utils.baseconv import base64

from Panacea.decorators import group_required
from Panacea.app.summary.coversheet.forms import *
from Panacea.app.user_and_org.forms import *
from Panacea.app.summary.review_tracking.models import *
from Panacea.utilities import get_all_cover_sheet_steps_completed, find_user_organization, get_cover_sheet_submitted, \
    get_current_summary_report_year


@login_required(login_url='/Panacea/login')
@group_required('Summary reporter', 'WSDOT staff')
def summary_instructions(request):
    user_org = find_user_organization(request.user.id)
    if get_cover_sheet_submitted(user_org.id):
        return redirect('cover_sheet_submitted')

    summary_progress, created = summary_organization_progress.objects.get_or_create(organization=user_org)
    summary_progress.started = True
    summary_progress.save()
    ready_to_submit = get_all_cover_sheet_steps_completed(user_org.id)

    return render(request, 'pages/summary/summary_instructions.html', {'ready_to_submit': ready_to_submit})


@login_required(login_url='/Panacea/login')
@group_required('Summary reporter', 'WSDOT staff')
def organizational_information(request):
    user_profile_data = profile.objects.get(custom_user=request.user.id)
    org = user_profile_data.organization
    org_name = org.name
    form = organization_profile(instance=org)
    if request.POST:
        if form.is_valid():
            # most times this form get submitted to the OrganizationProfile view so this is never called
            form.save()

            return redirect('organizational_information')

    ready_to_submit = get_all_cover_sheet_steps_completed(org.id)

    return render(request, 'pages/summary/organizational_information.html', {'org_name': org_name,
                                                                             'form': form,
                                                                             'ready_to_submit': ready_to_submit})


@login_required(login_url='/Panacea/login')
@group_required('Summary reporter', 'WSDOT staff')
def cover_sheet_organization_view(request):
    user_profile_data = profile.objects.get(custom_user=request.user.id)
    org = user_profile_data.organization
    org_name = org.name
    cover_sheet_instance, created = cover_sheet.objects.get_or_create(organization_id=org.id)
    form = cover_sheet_organization(instance=cover_sheet_instance)
    try:
        base64_logo = base64.encodebytes(cover_sheet_instance.organization_logo).decode("utf-8")
    except:
        base64_logo = ""

    if request.POST:
        form = cover_sheet_organization(instance=cover_sheet_instance, data=request.POST, files=request.FILES)

        if form.is_valid():
            instance = form.save(commit=False)
            filepath = request.FILES.get('organization_logo_input', False)
            # TODO correct this view now that it redirects to the next page if it is submitted
            if filepath:
                instance.organization_logo = filepath.read()
                base64_logo = base64.encodebytes(instance.organization_logo).decode("utf-8")
            else:
                if cover_sheet_instance.organization_logo:
                    instance.organization_logo = cover_sheet_instance.organization_logo
                else:
                    instance.organization_logo = None

            instance.save()
            summary_progress, created = summary_organization_progress.objects.get_or_create(
                organization=find_user_organization(request.user.id))
            summary_progress.organization_details = True
            summary_progress.save()
            return redirect('cover_sheets_service')

    ready_to_submit = get_all_cover_sheet_steps_completed(org.id)
    return render(request, 'pages/summary/cover_sheet_organization.html', {'form': form,
                                                                           'org_name': org_name,
                                                                           'base64_logo': base64_logo,
                                                                           'year': get_current_summary_report_year(),
                                                                           'ready_to_submit': ready_to_submit})


@login_required(login_url='/Panacea/login')
@group_required('Summary reporter', 'WSDOT staff')
def cover_sheet_service_view(request):
    user_profile_data = profile.objects.get(custom_user=request.user.id)
    org = user_profile_data.organization
    service_type = org.summary_organization_classifications

    cover_sheet_instance, created = cover_sheet.objects.get_or_create(organization=org)

    form = cover_sheet_service(instance=cover_sheet_instance)
    ready_to_submit = get_all_cover_sheet_steps_completed(org.id)

    if request.POST:
        form = cover_sheet_service(data=request.POST, instance=cover_sheet_instance)

        if form.is_valid():
            print("valid")
            form.save()
            summary_progress, created = summary_organization_progress.objects.get_or_create(
                organization=find_user_organization(request.user.id))
            summary_progress.service_cover_sheet = True
            summary_progress.save()

            return redirect('submit_cover_sheet')
        else:
            print("Error")
            for error in form.errors:
                print(error)

    return render(request, 'pages/summary/cover_sheet_service.html', {'service_type': service_type,
                                                                      'form': form,
                                                                      'ready_to_submit': ready_to_submit})


@login_required(login_url='/Panacea/login')
@group_required('Summary reporter', 'WSDOT staff')
def submit_cover_sheet(request):
    return render(request, 'pages/summary/submit_cover_sheet.html', {})


@login_required(login_url='/Panacea/login')
@group_required('Summary reporter', 'WSDOT staff')
def submit_cover_sheet_submit(request):
    user_org = find_user_organization(request.user.id)
    ready_to_submit = get_all_cover_sheet_steps_completed(user_org.id)
    if not ready_to_submit:
        raise Http404("Your coversheet is not ready to be submitted. Please go through each tab and confirm your data has been updated.")

    report_status = summary_report_status.objects.get(year=get_current_summary_report_year(), organization=user_org)
    report_status.cover_sheet_submitted_for_review = True
    report_status.cover_sheet_status = "With WSDOT"
    report_status.save()

    return redirect('summary_report_data')


@login_required(login_url='/Panacea/login')
@group_required('Summary reporter', 'WSDOT staff')
def cover_sheet_submitted(request):
    cover_sheet_status = summary_report_status.objects.get(year=get_current_summary_report_year(), organization=find_user_organization(request.user.id)).cover_sheet_status
    return render(request, 'pages/summary/cover_sheet_submitted.html', {'cover_sheet_status': cover_sheet_status})