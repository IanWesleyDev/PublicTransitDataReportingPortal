import base64
import csv
import datetime
import itertools
import json
import pandas as pd

from Panacea.builders import SummaryDataEntryBuilder, SummaryDataEntryTemplateData, ConfigurationBuilder
from .validators import validation_test_for_transit_data

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.mail import send_mail, BadHeaderError
from django.db import transaction
from django.db.models import Max
from django.db.models import Min, Sum, Avg
from django.db.models.functions import datetime
from django.forms import modelformset_factory, BaseModelFormSet, ModelForm
from django.http import Http404, HttpResponseRedirect
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models.functions import datetime
from django.core.mail import send_mail, BadHeaderError
from django.template.loader import render_to_string
from django.db.models import Max
from dateutil.relativedelta import relativedelta
import datetime
from django.urls import reverse
from Panacea.decorators import group_required
from .utilities import monthdelta, get_wsdot_color, get_vanpool_summary_charts_and_table, percent_change_calculation, \
    find_vanpool_organizations, get_current_summary_report_year, filter_revenue_sheet_by_classification, \
    find_user_organization_id, complete_data, green_house_gas_per_sov_mile, green_house_gas_per_vanpool_mile, \
    generate_performance_measure_table, generate_mode_by_agency_tables, create_statewide_revenue_table, \
    create_statewide_expense_table, create_all_summary_report_statuses
from django.http import Http404
from .filters import VanpoolExpansionFilter, VanpoolReportFilter
from django.conf import settings
from .emails import send_user_registration_email, notify_user_that_permissions_have_been_requested, active_permissions_request_notification
import base64
from django import forms

from .vanpool.forms import *

from .forms import *
from .models import profile, custom_user, organization, cover_sheet, \
    revenue, transit_data, expense, expense_source, service_offered, revenue_source, \
    transit_metrics, transit_mode, fund_balance, fund_balance_type, summary_organization_type, validation_errors,  summary_report_status, cover_sheet_review_notes, summary_organization_progress
from django.contrib.auth.models import Group
from .utilities import calculate_latest_vanpool, find_maximum_vanpool, calculate_remaining_months, \
    calculate_if_goal_has_been_reached, \
    find_user_organization_id, find_user_organization, get_all_cover_sheet_steps_completed, \
    get_cover_sheet_submitted, get_all_data_steps_completed, get_data_submitted, reset_summary_reporter_tracking, \
    reset_all_orgs_summary_progress
from .utilities import monthdelta, get_wsdot_color, get_vanpool_summary_charts_and_table, percent_change_calculation, \
    find_vanpool_organizations, get_current_summary_report_year, filter_revenue_sheet_by_classification, \
    complete_data, green_house_gas_per_sov_mile, green_house_gas_per_vanpool_mile
from .tables import build_operations_data_table, build_investment_table, build_revenue_table, build_total_funds_by_source, build_community_provider_revenue_table
from .validators import validation_test_for_transit_data
from .statewide_tables import create_statewide_revenue_table, create_statewide_expense_table, generate_mode_by_agency_tables, generate_performance_measure_table


# region shared_views
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/register.html', {'form': form})


@login_required(login_url='/Panacea/login')
def index(request):
    return render(request, 'index.html', {})



@login_required(login_url='/Panacea/login')
def dashboard(request):
    current_user_profile = profile.objects.get(custom_user=request.user)

    if not current_user_profile.profile_submitted:
        return redirect('ProfileSetup')

    if current_user_profile.profile_submitted and not current_user_profile.profile_complete:
        return render(request, 'pages/ProfileComplete.html')

    # If the user is registered and has had permissions assigned
    if current_user_profile.profile_complete is True:
        current_user_id = request.user.id
        user_org_id = profile.objects.get(custom_user_id=current_user_id).organization_id
        user_context = {'user_org': user_org_id}

        if not organization.objects.get(id=user_org_id).vanpool_program or not request.user.groups.filter(name__in=['Vanpool reporter']).exists():
            vp_program = False
            user_context.update({'vp_program': vp_program})
        elif organization.objects.get(id=user_org_id).vanpool_program == True and request.user.groups.filter(name__in=['Vanpool reporter']).exists():
            recent_vanpool_report = vanpool_report.objects. \
                filter(organization_id=user_org_id, report_date__isnull=False). \
                order_by('-report_year', '-report_month').first()
            report_month = recent_vanpool_report.report_month
            previous_report_year = recent_vanpool_report.report_year - 1
            last_year_report = vanpool_report.objects.get(organization_id=user_org_id,
                                                          report_year=previous_report_year,
                                                          report_month=report_month)

            def get_most_recent_and_change(measure):
                """Return a list where first item is the current months stat and the second item is the year over year grouwth"""
                current_monthly_stat = getattr(recent_vanpool_report, measure)
                last_year_stat = getattr(last_year_report, measure)
                if last_year_stat is None:
                    year_over_year_growth = "NA"
                else:
                    year_over_year_growth = (current_monthly_stat / last_year_stat) - 1

                return [current_monthly_stat, year_over_year_growth]

            def check_status():
                """Returns the report status (if it is past due) of the report for the report after the most recent report"""

                def get_month_year_addition(month):
                    if month == 12:
                        return -11, 1
                    else:
                        return 1, 0

                month_add, year_add = get_month_year_addition(recent_vanpool_report.report_month)
                next_vanpool_report_status = vanpool_report.objects.get(organization_id=user_org_id,
                                                                        report_month=recent_vanpool_report.report_month + month_add,
                                                                        report_year=recent_vanpool_report.report_year + year_add).status

                return next_vanpool_report_status

            def ghg_calculator():
                current_monthly_sov = green_house_gas_per_sov_mile() * recent_vanpool_report.average_riders_per_van * (
                        recent_vanpool_report.vanpool_miles_traveled + recent_vanpool_report.vanshare_miles_traveled)
                current_monthly_vanpool_emissions = recent_vanpool_report.vanpool_miles_traveled * green_house_gas_per_vanpool_mile()
                current_monthly_emissions = current_monthly_sov - current_monthly_vanpool_emissions
                last_year_monthly_sov = green_house_gas_per_sov_mile() * last_year_report.average_riders_per_van * (
                        last_year_report.vanpool_miles_traveled + last_year_report.vanshare_miles_traveled)
                last_year_monthly_vanpool_emissions = (
                                                              last_year_report.vanpool_miles_traveled + last_year_report.vanshare_miles_traveled) * green_house_gas_per_vanpool_mile()
                last_year_monthly_emissions = last_year_monthly_sov - last_year_monthly_vanpool_emissions

                ghg_percent = ((current_monthly_emissions - last_year_monthly_emissions) / last_year_monthly_emissions)
                return [round(current_monthly_emissions, 2), ghg_percent]

            user_context.update({'user_org': user_org_id,
                                 'groups_in_operation': get_most_recent_and_change(
                                     "total_groups_in_operation"),
                                 'total_passenger_trips': get_most_recent_and_change(
                                     "total_passenger_trips"),
                                 'average_riders_per_van': get_most_recent_and_change(
                                     "average_riders_per_van"),
                                 'total_miles_traveled': get_most_recent_and_change(
                                     "total_miles_traveled"),
                                 'co2_emissions_avoided': ghg_calculator(),
                                 'report_status': check_status(),
                                 'report_month': report_month,
                                 'previous_report_year': previous_report_year,
                                 'last_report_year': recent_vanpool_report.report_year
                                 })

        if not organization.objects.get(id=user_org_id).summary_reporter or not request.user.groups.filter(name__in=['Summary reporter']).exists():
            user_context.update({'summary_reporter': False})
        elif organization.objects.get(id=user_org_id).summary_reporter and request.user.groups.filter(name__in=['Summary reporter']).exists():
            org_progress, created = summary_organization_progress.objects.get_or_create(organization_id=user_org_id)

            user_context.update({'summary_reporter': True,
                                 'summary_report_status': summary_report_status.objects.get(year=get_current_summary_report_year(), organization_id=user_org_id),
                                 'summary_organization_progress': org_progress
                                 })

    return render(request, 'pages/dashboard.html', user_context)


# TODO rename forms to not be camel case
@login_required(login_url='/Panacea/login')
def ProfileSetup(request):
    user_change_form = custom_user_ChangeForm(instance=request.user)
    current_user_instance = profile.objects.get(custom_user=request.user.id)
    phone_org_form = PhoneOrgSetup(instance=current_user_instance)
    report_selection_form = ReportSelection(instance=current_user_instance)
    return render(request, 'pages/ProfileSetup.html', {'ProfileSetup_PhoneAndOrg': phone_org_form,
                                                       'custom_user_ChangeForm': user_change_form,
                                                       'ProfileSetup_ReportSelection': report_selection_form})


@login_required(login_url='/Panacea/login')
def ProfileSetup_Review(request):
    if request.method == 'POST':
        current_user = request.user
        if request.POST:
            form = custom_user_ChangeForm(request.POST, instance=current_user)
            if form.is_valid():
                form.user = request.user
                form = form.save(commit=False)
                form.save()
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'error': form.errors})


@login_required(login_url='/Panacea/login')
def ProfileSetup_PhoneAndOrg(request):
    if request.method == 'POST':
        current_user_instance = profile.objects.get(custom_user=request.user.id)
        if request.POST:
            form = PhoneOrgSetup(request.POST, instance=current_user_instance)
            if form.is_valid():
                form.user = request.user
                form = form.save(commit=False)
                form.save()
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'error': form.errors}, status=200)


@login_required(login_url='/Panacea/login')
def ProfileSetup_ReportSelection(request):
    if request.method == 'POST':
        current_user_instance = profile.objects.get(custom_user=request.user.id)
        if request.POST:
            form = ReportSelection(request.POST, instance=current_user_instance)
            if form.is_valid():
                # form.user = request.user
                form.save()
                current_user_instance.profile_submitted = True
                current_user_instance.active_permissions_request = True
                current_user_instance.save()
                send_user_registration_email(request.user.id)
                return JsonResponse({'redirect': '../dashboard'})
            else:
                return JsonResponse({'error': form.errors})


@login_required(login_url='/Panacea/login')
def handler404(request, exception):
    return render(request, 'pages/error_404.html', status=404)


@login_required(login_url='/Panacea/login')
def UserProfile(request):
    user_name = request.user.get_full_name()
    form_custom_user = user_profile_custom_user(instance=request.user)
    profile_data = profile.objects.get(custom_user=request.user.id)
    form_profile = user_profile_profile(instance=profile_data)
    user_org = profile_data.organization.name

    if request.POST:
        form_custom_user = user_profile_custom_user(data=request.POST.copy(), instance=request.user)
        form_profile = user_profile_profile(data=request.POST.copy(), instance=profile_data)
        if form_custom_user.is_valid() & form_profile.is_valid():
            form_custom_user.save()
            form_profile.save()
            return redirect('UserProfile')
        else:
            form_custom_user.data['first_name'] = request.user.first_name
            form_custom_user.data['last_name'] = request.user.last_name
            form_profile.data['telephone_number'] = profile_data.telephone_number

    return render(request, 'pages/UserProfile.html', {'user_name': user_name,
                                                      'form_custom_user': form_custom_user,
                                                      'form_profile': form_profile,
                                                      'user_org': user_org})


@login_required(login_url='/Panacea/login')
def OrganizationProfileUsers(request):
    user_profile_data = profile.objects.get(custom_user=request.user.id)
    org = user_profile_data.organization
    org_id = organization.objects.filter(name=org).values('id')
    org_id = org_id[0]['id']
    # TODO could this be valueslist?
    vals = profile.objects.filter(organization_id=org_id).values('custom_user')
    vals = [i['custom_user'] for i in vals]
    cust = custom_user.objects.filter(id__in=vals).values('first_name', 'last_name', 'email', 'date_joined',
                                                          'last_login')
    org_name = org.name
    return render(request, 'pages/OrganizationProfileUsers.html', {'org_name': org_name, 'users': cust})


@login_required(login_url='/Panacea/login')
@group_required('Vanpool reporter', 'WSDOT staff', 'Summary reporter')
def OrganizationProfile(request, redirect_to=None):
    user_profile_data = profile.objects.get(custom_user=request.user.id)
    org = user_profile_data.organization
    org_name = org.name
    form = organization_profile(instance=org)
    if request.POST:
        form = organization_profile(data=request.POST.copy(), instance=org)
        if form.is_valid():
            # TODO figure out why is this here
            if not 'state' in form.data:
                form.data['state'] = user_profile_data.organization.state
            form.save()
            if redirect_to:
                print(redirect_to)
                if redirect_to == "organizational_information":
                    summary_progress, created = summary_organization_progress.objects.get_or_create(
                        organization=find_user_organization(request.user.id))
                    summary_progress.address_and_organization = True
                    summary_progress.save()
                    return redirect("cover_sheets_organization")

                return redirect(redirect_to)
            else:
                return redirect('OrganizationProfile')
        else:
            form.data['name'] = org.name
            form.data['address_line_1'] = org.address_line_1
            form.data['address_line_2'] = org.address_line_2
            form.data['city'] = org.city
            # form.data['state'] = org.state
            form.data['zip_code'] = org.zip_code
            form.data['vanshare_program'] = org.vanshare_program

    return render(request, 'pages/OrganizationProfile.html', {'org_name': org_name, 'form': form})


@login_required(login_url='/Panacea/login')
def Permissions(request):
    submit_success = False
    if request.POST:
        form = request_user_permissions(data=request.POST)
        if form.is_valid():

            groups = ' & '.join(str(s[1]) for s in form.cleaned_data['groups'].values_list())
            notify_user_that_permissions_have_been_requested(request.user.get_full_name(), groups, request.user.email)
            active_permissions_request_notification()
            current_user_profile = profile.objects.get(custom_user_id=request.user.id)
            current_user_profile.requested_permissions.set(form.cleaned_data['groups'])
            current_user_profile.active_permissions_request = True
            current_user_profile.save()
            submit_success = True

    user = request.user
    auth_groups = Group.objects.all()
    form = request_user_permissions(instance=user)

    return render(request, 'pages/Permissions.html', {'auth_groups': auth_groups,
                                                      'user_name': request.user.get_full_name(),
                                                      'form': form,
                                                      'submit_success': submit_success})


@login_required(login_url='/Panacea/login')
# @group_required('WSDOT staff')
def Admin_assignPermissions(request, active=None):
    if not active:
        active = 'active'
    active_requests = profile.objects.filter(active_permissions_request=True).exists()
    if active_requests and active == 'active':
        profile_data = profile.objects.filter(active_permissions_request=True).all()
    else:
        profile_data = profile.objects.all()

    assign_permissions_formset = modelformset_factory(custom_user, change_user_permissions_group, extra=0)

    if request.method == 'POST':
        formset = assign_permissions_formset(request.POST)
        # if formset.is_valid():
        #     formset.save()
        #     return JsonResponse({'success': True})
        # else:
        for form in formset:
            if form.is_valid():
                if len(form.changed_data) > 0:
                    data = form.cleaned_data
                    email = data['email']
                    this_user_id = custom_user.objects.get(email=email).id
                    my_profile = profile.objects.get(custom_user_id=this_user_id)
                    my_profile.profile_complete = True
                    my_profile.active_permissions_request = False
                    my_profile.save()
                    # print(email)
                form.save()

        return JsonResponse({'success': True})
    else:
        formset = assign_permissions_formset(
            queryset=custom_user.objects.filter(id__in=profile_data.values_list('custom_user_id')))
        if active_requests and active == 'active':
            return render(request, 'pages/assign_permissions_active_requests.html',
                          {'Admin_assignPermissions_all': formset,
                           'profile_data': profile_data})
        else:
            return render(request, 'pages/AssignPermissions.html', {'Admin_assignPermissions_all': formset,
                                                                    'profile_data': profile_data,
                                                                    'active_requests': active_requests})


@login_required(login_url='/Panacea/login')
def accessibility(request):
    return render(request, 'pages/Accessibility.html', {})


@login_required(login_url='/Panacea/login')
def public_disclosure(request):
    return render(request, 'pages/PublicDisclosure.html', {})


@login_required(login_url='/Panacea/login')
def help_page(request):
    return render(request, 'pages/Help.html', {})


@login_required(login_url='/Panacea/login')
def logout_view(request):
    logout(request)


# endregion

# region vanpool

# endregion


# region summary
@login_required(login_url='/Panacea/login')
@group_required('Summary reporter', 'WSDOT staff')
def pick_up_where_you_left_off(request):
    summary_status = summary_report_status.objects.get(year=get_current_summary_report_year(), organization=find_user_organization(request.user.id))
    org_progress, created = summary_organization_progress.objects.get_or_create(organization=find_user_organization(request.user.id))

    if not org_progress.started:
        return redirect('summary_instructions')
    elif not org_progress.address_and_organization:
        return redirect('cover_sheets_organization')
    elif not org_progress.organization_details:
        return redirect('cover_sheets_organization')
    elif not org_progress.service_cover_sheet:
        return redirect('cover_sheets_service')
    elif not summary_status.cover_sheet_submitted_for_review:
        return redirect('submit_cover_sheet')
    elif not org_progress.confirm_service:
        return redirect('summary_report_data')
    elif not org_progress.transit_data:
        return redirect('summary_reporting_type', 'transit_data')
    elif not org_progress.revenue:
        return redirect('summary_reporting_type', 'revenue')
    elif not org_progress.expenses:
        return redirect('summary_reporting_type', 'expense')
    elif not org_progress.ending_balances:
        return redirect('summary_reporting_type', 'fund_balance')
    elif not summary_status.data_report_submitted_for_review:
        return redirect('submit_data')
    else:
        raise Http404("Can't find where you left off.")




@login_required(login_url='/Panacea/login')
@group_required('Summary reporter', 'WSDOT staff')
def ntd_upload(request):
    return render(request, 'pages/summary/ntd_upload.html', {})


@login_required(login_url='/Panacea/login')
@group_required('Summary reporter', 'WSDOT staff')
def summary_report_data(request):
    user_org = find_user_organization(request.user.id)
    if get_data_submitted(user_org.id):
        return redirect('data_submitted')

    ready_to_submit = get_all_data_steps_completed(user_org.id)

    return render(request, 'pages/summary/summary_report_data_instructions.html', {'ready_to_submit': ready_to_submit})




@login_required(login_url='/Panacea/login')
@group_required('Summary reporter', 'WSDOT staff')
def review_data(request):
    user_org = find_user_organization_id(request.user.id)
    org_name = find_user_organization(request.user.id)
    report_year = datetime.date.today().year - 1
    mode_list = transit_data.objects.filter(year=report_year, organization_id=user_org).order_by(
        'transit_mode').values_list('transit_mode', 'transit_mode_id__name', 'administration_of_mode').distinct()
    for mode in mode_list:
        validation_test_for_transit_data(report_year, mode[0], mode[2], user_org, request.user.id)
    ve = validation_errors.objects.filter(organization_id=user_org, year=report_year, error_resolution__isnull=True)
    my_formset_factory = modelformset_factory(model=validation_errors,
                                              form=validation_error_form,
                                              extra=0)
    if request.method == 'POST':
        formset = my_formset_factory(data=request.POST, queryset=ve)
        error_count = formset.total_form_count()
        for form in formset:
            if form.is_valid():
                form.cleaned_data['report_by_id'] = request.user.id
                form.save(commit=True)
    else:
        formset = my_formset_factory(queryset=ve)
        error_count = formset.total_form_count()

        # TODO transit_mode is kind of messed up, and need a little help resolving

    return render(request, 'pages/summary/review_data.html', {'formset': formset,
                                                              'org_name': org_name, 'error_count': error_count})





@login_required(login_url='/Panacea/login')
def your_logged_in(request):
    return render(request, 'you_are_logged_in.html')


def login_denied(request):
    return render(request, 'login_denied.html')


@login_required(login_url='/Panacea/login')
def contact_us(request):
    if request.method == 'POST':
        form = email_contact_form(request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            from_email = form.cleaned_data['from_email']
            message = form.cleaned_data['message']
            try:
                print('something')
                send_mail(subject, message, from_email, [settings.DEFAULT_FROM_EMAIL,], fail_silently=False)
            except BadHeaderError:
                return HttpResponse('Invalid header found')
            return redirect('dashboard')
    else:
        form = email_contact_form()

    return render(request, 'pages/ContactUs.html', {'form':form})



@login_required(login_url='/Panacea/login')
@group_required('WSDOT staff')
def create_new_tracking_year(request, year):
    # TODO add summary reporter flag
    all_orgs = organization.objects.filter(summary_reporter=True).all()

    with transaction.atomic():
        for org in all_orgs:
            t = summary_report_status.objects.get_or_create(organization=org, year=year)

    return summary_tracking(request)


@login_required(login_url='/Panacea/login')
@group_required('WSDOT staff')
def summary_tracking(request, year=None):
    if year is None:
        year = summary_report_status.objects.aggregate(Max('year'))
        year = year['year__max']
        print(year)
    if request.POST:
        pass
    else:
        pass
    tracking_data = summary_report_status.objects.filter(year=year, organization__summary_reporter=True).order_by(
        'organization__name')
    print(tracking_data)

    return render(request, 'pages/summary/admin/summary_tracking.html', {'year': year, 'tracking_data': tracking_data})


@login_required(login_url='/Panacea/login')
@group_required('WSDOT staff')
def summary_yearly_setup(request, action=None):

    if action:
        if action == "reset_summary_reporter_tracking":
            year = get_current_summary_report_year()
            reset_summary_reporter_tracking(year)
        elif action == "reset_all_orgs_summary_progress":
            reset_all_orgs_summary_progress()
        elif action == "create_all_summary_report_statuses":
            year = get_current_summary_report_year()
            summary_orgs = organization.objects.filter(summary_reporter=True)
            print(summary_orgs)
            for org in summary_orgs:
                summary_report_status.objects.get_or_create(year=year, organization=org)
        else:
            raise Http404("Action not found")

    return render(request, 'pages/summary/admin/summary_yearly_setup.html', {})


@login_required(login_url='/Panacea/login')
@group_required('WSDOT staff')
def summary_yearly_setup_instructions(request):
    return render(request, 'pages/summary/admin/summary_yearly_setup_instructions.html', {})



@login_required(login_url='/Panacea/login')
@group_required('WSDOT staff')
def wsdot_review_cover_sheets(request, year=None, organization_id=None):
    if year is None:
        year = summary_report_status.objects.aggregate(Max('year'))
        year = year['year__max']
    if organization_id is None:
        cover_sheet_organization = summary_report_status.objects.filter(year=year,
                                                                        organization__summary_reporter=True).order_by(
            'organization__name').first()
        organization_id = cover_sheet_organization.organization_id

        print(organization_id)

    org_cover_sheet, created = cover_sheet.objects.get_or_create(organization_id=organization_id)

    organization_status = get_object_or_404(summary_report_status, year=year, organization_id=organization_id)
    summary_report_status_id = organization_status.id
    organization_name = organization.objects.get(id=organization_id).name

    cover_sheet_submitted = organization_status.cover_sheet_submitted_for_review
    cover_sheet_status = organization_status.cover_sheet_status

    next_organization = summary_report_status.objects.filter(year=year, organization__summary_reporter=True).order_by(
        'organization__name').filter(organization__name__gt=organization_name).first()
    previous_organization = summary_report_status.objects.filter(year=year,
                                                                 organization__summary_reporter=True).order_by(
        'organization__name').filter(organization__name__lt=organization_name).last()

    try:
        base64_logo = base64.encodebytes(
            org_cover_sheet.organization_logo).decode("utf-8")
    except:
        base64_logo = ""

    if cover_sheet_submitted:
        if request.POST:
            cover_sheet_form = cover_sheet_wsdot_review(data=request.POST, instance=org_cover_sheet, files=request.FILES)
            if cover_sheet_form.is_valid():
                instance = cover_sheet_form.save(commit=False)
                filepath = request.FILES.get('organization_logo_input', False)

                if filepath:
                    instance.organization_logo = filepath.read()
                else:
                    if instance.organization_logo:
                        instance.organization_logo = instance.organization_logo
                    else:
                        instance.organization_logo = None
            instance.save()
        else:
            cover_sheet_form = cover_sheet_wsdot_review(instance=cover_sheet.objects.get(organization_id=organization_id))


        organization_notes = cover_sheet_review_notes.objects.filter(year=year,
                                                                     summary_report_status=summary_report_status.objects.get(organization_id=organization_id),
                                                                     note_area='Organization')
        service_notes = cover_sheet_review_notes.objects.filter(year=year,
                                                                summary_report_status=summary_report_status.objects.get(
                                                                    organization_id=organization_id),
                                                                note_area='Service')
        child_notes = cover_sheet_review_notes.objects.filter(year=year,
                                                              summary_report_status=summary_report_status.objects.get(
                                                                  organization_id=organization_id),
                                                              parent_note__isnull=False)


        new_note_form = add_cover_sheet_review_note()

    else:
        cover_sheet_form = ""
        organization_notes = ""
        new_note_form = ""
        service_notes = ""
        child_notes = ""

    return render(request, 'pages/summary/admin/wsdot_review_cover_sheet.html',
                  {'cover_sheet_id': organization_status.id,
                   'cover_sheet_submitted': cover_sheet_submitted,
                   'cover_sheet_status': cover_sheet_status,
                   'summary_report_status_id': summary_report_status_id,
                   'organization_id': organization_id,
                   'year': year,
                   'next_organization': next_organization,
                   'previous_organization': previous_organization,
                   'cover_sheet_form': cover_sheet_form,
                   'organization_notes': organization_notes,
                   'service_notes': service_notes,
                   'child_notes': child_notes,
                   'new_note_form': new_note_form,
                   'published_version': org_cover_sheet.published_version,
                   'base64_logo': base64_logo})


# TODO Come back through and change this to be object oriented code about a notes object that works for cover sheets and data. Sorry future me... I was running out of time/
@login_required(login_url='/Panacea/login')
def base_note(request):
    # this is used to build the base url to submit a new note it is never actually called.
    raise PermissionError


@login_required(login_url='/Panacea/login')
@group_required('WSDOT staff')
def add_cover_sheet_note_wsdot(request, year, summary_report_status_id, note_area, note_field):

    print(note_area)
    print(cover_sheet_review_notes.NOTE_AREAS)

    if request.POST:
        form = add_cover_sheet_review_note(request.POST)
        instance = form.save(commit=False)
        instance.year = year
        instance.summary_report_status_id = summary_report_status_id
        instance.wsdot_note = True
        instance.note_area = note_area
        instance.note_field = note_field
        instance.custom_user = request.user
        instance.save()
    url = reverse('wsdot_review_cover_sheets_year_org', kwargs={'year': year,
                                                                'organization_id': summary_report_status.objects.get(id=summary_report_status_id).organization_id})
    return HttpResponseRedirect(url)


@login_required(login_url='/Panacea/login')
def add_cover_sheet_child_note_wsdot(request, parent_note):
    parent_note = cover_sheet_review_notes.objects.get(id=parent_note)
    if request.POST:
        form = add_cover_sheet_review_note(request.POST)
        instance = form.save(commit=False)
        instance.year = parent_note.year
        instance.summary_report_status_id = parent_note.summary_report_status_id
        instance.wsdot_note = True
        instance.note_area = parent_note.note_area
        instance.note_field = parent_note.note_field
        instance.custom_user = request.user
        instance.parent_note = parent_note.id
        instance.save()
    url = reverse('wsdot_review_cover_sheets_year_org', kwargs={'year': parent_note.year,
                                                                'organization_id': summary_report_status.objects.get(
                                                                    id=parent_note.summary_report_status_id).organization_id})
    return HttpResponseRedirect(url)


@login_required(login_url='/Panacea/login')
def add_cover_sheet_child_note_customer(request, parent_note):
    parent_note = cover_sheet_review_notes.objects.get(id=parent_note)
    if request.POST:
        form = add_cover_sheet_review_note(request.POST)
        instance = form.save(commit=False)
        instance.year = parent_note.year
        instance.summary_report_status_id = parent_note.summary_report_status_id
        instance.wsdot_note = False
        instance.note_area = parent_note.note_area
        instance.note_field = parent_note.note_field
        instance.custom_user = request.user
        instance.parent_note = parent_note.id
        instance.save()
    url = reverse('customer_review_cover_sheets')
    return HttpResponseRedirect(url)


@login_required(login_url='/Panacea/login')
def add_cover_sheet_note_customer(request, year, note_area, note_field):
    if note_area == "Organization":
        url = reverse('cover_sheets_organization')
    elif note_area == "Service":
        url = reverse('cover_sheets_service')
    else:
        raise PermissionError

    if request.POST:
        form = add_cover_sheet_review_note(request.POST)
        instance = form.save(commit=False)
        instance.year = year
        instance.summary_report_status_id = summary_report_status.objects.get(organization_id=find_user_organization_id(request.user.id), year=year).id
        instance.wsdot_note = False
        instance.note_area = note_area
        instance.note_area = note_field
        instance.custom_user = request.user
        instance.save()

    return HttpResponseRedirect(url)


@login_required(login_url='/Panacea/login')
def delete_cover_sheet_note(request, note_id):
    note = cover_sheet_review_notes.objects.get(id=note_id)
    note_year = note.year
    note_organization_id = summary_report_status.objects.get(id=note.summary_report_status_id).organization_id

    if note.wsdot_note:
        url = reverse('wsdot_review_cover_sheets_year_org', kwargs={'year': note_year,
                                                                    'organization_id': note_organization_id})
    else:
        if note.note_area == "Organization":
            url = reverse('customer_review_cover_sheets')
        elif note.note_area == "Service":
            url = reverse('customer_review_cover_sheets')
        else:
            raise PermissionError

    if not note.custom_user == request.user:
        raise PermissionError
    else:
        note.delete()


    return HttpResponseRedirect(url)


@login_required(login_url='/Panacea/login')
@group_required('WSDOT staff')
def approve_cover_sheet(request, summary_report_status_id):
    cover_sheet_status = summary_report_status.objects.get(id=summary_report_status_id)
    cover_sheet_status.cover_sheet_status = "Complete"
    cover_sheet_status.save()

    url = reverse('wsdot_review_cover_sheets_year_org', kwargs={'year': cover_sheet_status.year,
                                                                'organization_id': cover_sheet_status.organization_id})
    return HttpResponseRedirect(url)


@login_required(login_url='/Panacea/login')
@group_required('WSDOT staff')
def return_cover_sheet_to_user(request, summary_report_status_id):
    cover_sheet_status = summary_report_status.objects.get(id=summary_report_status_id)
    cover_sheet_status.cover_sheet_status = "With user"
    cover_sheet_status.save()

    url = reverse('wsdot_review_cover_sheets_year_org', kwargs={'year': cover_sheet_status.year,
                                                                'organization_id': cover_sheet_status.organization_id})
    return HttpResponseRedirect(url)


@login_required(login_url='/Panacea/login')
@group_required('WSDOT staff')
def wsdot_review_data(request):
    if request.POST:
        pass
    else:
        pass
    return render(request, 'pages/summary/admin/wsdot_review_data.html')


@login_required(login_url='/Panacea/login')
def customer_review_cover_sheets(request):
    year = get_current_summary_report_year()
    organization_id = find_user_organization_id(request.user.id)
    org_summary_report_status = summary_report_status.objects.get(year=year, organization_id=organization_id)

    notes = cover_sheet_review_notes.objects.filter(year=year,
                                                    summary_report_status=summary_report_status.objects.get(organization_id=organization_id),
                                                    parent_note__isnull=True).exclude(note_status="Closed")
    child_notes = cover_sheet_review_notes.objects.filter(year=year,
                                                          summary_report_status=summary_report_status.objects.get(organization_id=organization_id),
                                                          parent_note__isnull=False)
    new_note_form = add_cover_sheet_review_note()


    return render(request, 'pages/summary/customer_review_cover_sheet.html', {'year': year,
                                                                              'organization_id': organization_id,
                                                                              'org_summary_report_status': org_summary_report_status,
                                                                              'notes': notes,
                                                                              'child_notes': child_notes,
                                                                              'new_note_form': new_note_form})


@login_required(login_url='/Panacea/login')
def customer_review_data(request):
    return render(request, 'pages/summary/customer_review_cover_sheet.html')


@login_required(login_url='/Panacea/login')
def customer_review_instructions(request):
    return render(request, 'pages/summary/customer_review_instructions.html')


@login_required(login_url='/Panacea/login')
def accept_wsdot_edit(request, note_id):

    note = cover_sheet_review_notes.objects.get(id=note_id)
    note.note_status = "Closed"
    note.save()
    unresolved_notes_count = cover_sheet_review_notes.objects.filter(summary_report_status=note.summary_report_status, parent_note__isnull=True).exclude(note_status="Closed").count()
    if unresolved_notes_count == 0:
        report_status = summary_report_status.objects.get(id=note.summary_report_status_id)
        report_status.cover_sheet_status = "With WSDOT"
        report_status.cover_sheet_submitted_for_review = True
        report_status.save()


    url = reverse('customer_review_cover_sheets')
    return HttpResponseRedirect(url)


@login_required(login_url='/Panacea/login')
@group_required('WSDOT staff')
def test_tools(request):
    if request.POST:
        custom_user_id = request.POST.get('custom_user')
        my_instance = profile.objects.get(custom_user_id=custom_user_id)
        print(request.POST)
        form = change_user_org(request.POST, instance=my_instance)
        if form.is_valid():
            form.save()
    else:
        form = change_user_org()
    return render(request, 'pages/test_tools.html', {'form': form})






@login_required(login_url='/Panacea/login')
@group_required('WSDOT staff')
def summary_metric_configurations(request, report_type=None):
    if not report_type:
        report_type = 'transit_data'

    metric_configuration_factory = ConfigurationBuilder(report_type)
    if request.POST:
        configuration_form_factory = metric_configuration_factory.create_model_formset_factory()
        form_set = configuration_form_factory(request.POST)
        for form in form_set:
            if form.is_valid():
                if len(form.changed_data) > 0:
                    form.save()
            else:
                print(form.errors)

        return JsonResponse({'success': True})
    else:
        form_set = metric_configuration_factory.get_form_set()

        return render(request, 'pages/summary/admin/summary_configure_metrics.html', {'form_set': form_set,
                                                                                      'report_type': report_type})


@login_required(login_url='/Panacea/login')
def configure_agency_types(request, model=None):

    if not model or model == "organization":
        model = "organization"
        my_model = organization
        field_name = 'summary_organization_classifications'
        other_field_list = []
        one2one = True
    elif model == "revenue_source":
        my_model = revenue_source
        field_name = 'agency_classification'
        other_field_list = ['funding_type', 'government_type']
        one2one = False
    elif model == "transit_metric":
        my_model = transit_metrics
        field_name = 'agency_classification'
        other_field_list = []
        one2one = False
    else:
        raise Http404("Cant find model")

    if one2one:
        my_widget = {'name': forms.TextInput(attrs={'class': 'form-control AJAX_instant_submit',
                                                    'data-form-name': "summary_configure_agency_types"}),
                     field_name: forms.Select(attrs={'class': 'form-control AJAX_instant_submit',
                                                     'data-form-name': "summary_configure_agency_types"})}
    else:
        my_widget = {'name': forms.TextInput(attrs={'class': 'form-control'}),
                     field_name: forms.CheckboxSelectMultiple(
                         attrs={'class': 'form-check-inline no-bullet AJAX_instant_submit',
                                'data-form-name': "summary_configure_agency_types"})}

    if len(other_field_list) > 0:
        for i in other_field_list:
            my_widget[i] = forms.Select(attrs={'class': 'form-control AJAX_instant_submit',
                                               'data-form-name': "summary_configure_agency_types"})

    formset_factory = modelformset_factory(my_model, form=ModelForm, formfield_callback=None,
                                           formset=BaseModelFormSet, extra=0, can_delete=False,
                                           can_order=False, max_num=None,
                                           fields=['name', field_name] + other_field_list,
                                           exclude=None,
                                           widgets=my_widget,
                                           validate_max=False, localized_fields=None,
                                           labels=None, help_texts=None, error_messages=None,
                                           min_num=None, validate_min=False, field_classes=None)

    if request.method == 'POST':
        formset = formset_factory(request.POST)
        for form in formset:
            if form.is_valid():
                form.save()
        return JsonResponse({'success': True})
    else:
        my_queryset = my_model.objects.all()
        formset = formset_factory(queryset=my_queryset.select_related())
        return render(request, 'pages/summary/configure_agency_types.html', {'formset': formset,

                                                                             'model': model})
