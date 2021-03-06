import json
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Min, Sum, Avg
from django.forms import formset_factory, modelformset_factory
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.db.models.functions import datetime
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.db.models import Max
from dateutil.relativedelta import relativedelta
import datetime
from Panacea.decorators import group_required
from .utilities import monthdelta, get_wsdot_color, get_vanpool_summary_charts_and_table, percent_change_calculation, \
    find_vanpool_organizations, get_current_summary_report_year, filter_revenue_sheet_by_classification
from django.http import Http404
from .filters import VanpoolExpansionFilter
from django.conf import settings
import base64

from .forms import CustomUserCreationForm, \
    custom_user_ChangeForm, \
    PhoneOrgSetup, \
    ReportSelection, \
    VanpoolMonthlyReport, \
    user_profile_custom_user, \
    user_profile_profile, \
    organization_profile, \
    change_user_permissions_group, \
    chart_form, \
    submit_a_new_vanpool_expansion, \
    Modify_A_Vanpool_Expansion, \
    request_user_permissions, \
    statewide_summary_settings, \
    Modify_A_Vanpool_Expansion, organisation_summary_settings, organization_information, cover_sheet_service, \
    cover_sheet_organization, \
    summary_revenue_form, BaseRevenueForm, summary_expense_form, service_offered

from .models import profile, vanpool_report, custom_user, vanpool_expansion_analysis, organization, cover_sheet, \
    SummaryRevenues, SummaryTransitData, SummaryExpenses, expenses_source, ServiceOffered, revenue_source
from django.contrib.auth.models import Group
from .utilities import calculate_latest_vanpool, find_maximum_vanpool, calculate_remaining_months, calculate_if_goal_has_been_reached, \
    generate_summary_report_years, find_user_organization


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

    # If the user is registered and has had permissions assigned
    if current_user_profile.profile_complete is True:
        current_user_id = request.user.id
        user_org_id = profile.objects.get(custom_user_id=current_user_id).organization_id
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
                year_over_year_growth = (current_monthly_stat/last_year_stat) - 1

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
        return render(request, 'pages/dashboard.html', {
            'groups_in_operation': get_most_recent_and_change("total_groups_in_operation"),
            'total_passenger_trips': get_most_recent_and_change("total_passenger_trips"),
            'average_riders_per_van': get_most_recent_and_change("average_riders_per_van"),
            'total_miles_traveled': get_most_recent_and_change("total_miles_traveled"),
            'report_status': check_status()
        })

    # If the user has completed their profile but has not had permissions assigned
    elif current_user_profile.profile_submitted is True:
        return render(request, 'pages/ProfileComplete.html')

    # If the user is a new user
    else:
        return redirect('ProfileSetup')


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
                current_user_instance.save()
                emailRecipient = custom_user.objects.filter(id = request.user.id).values('first_name','last_name')
                name = emailRecipient.values_list('first_name', flat=True)
                emailAddress = custom_user.objects.filter(id = request.user.id).values_list('email', flat = True)
                msg_plain = render_to_string('emails/registration_email.txt', {'firstname':name[0]})
                msg_html = render_to_string('emails/registration_email.html', {'firstname': name[0]})
                send_mail('Welcome to WSDOT\'s Public Transit Data Reporting Portal', msg_plain, settings.EMAIL_HOST_USER, [emailAddress[0]], html_message=msg_html,)
                return JsonResponse({'redirect': '../dashboard'})
            else:
                return JsonResponse({'error': form.errors})


@login_required(login_url='/Panacea/login')
def handler404(request, exception):
    return render(request, 'pages/error_404.html', status = 404)

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
    cust = custom_user.objects.filter(id__in=vals).values('first_name', 'last_name', 'email', 'date_joined', 'last_login')
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

            msg_html = render_to_string('emails/request_permissions_email.html',
                                        {'user_name': request.user.get_full_name(), 'groups': groups})
            msg_plain = render_to_string('emails/request_permissions_email.txt',
                                         {'user_name': request.user.get_full_name(), 'groups': groups})
            send_mail(
                subject='Permissions Request - Public Transportation Reporting Portal',
                message=msg_plain,
                from_email='some@sender.com',  # TODO change this to the correct email address
                recipient_list=['wesleyi@wsdot.wa.gov', ],  # TODO change this to the correct email address
                html_message=msg_html,
            )
            msg_html = "There is an active permissions request in the Public Transportation Reporting Portal"  # TODO add link
            msg_plain = "There is an active permissions request in the Public Transportation Reporting Portal"  # TODO add link
            send_mail(
                subject='Active Permissions Request - Public Transportation Reporting Portal',
                message=msg_plain,
                from_email='some@sender.com',  # TODO change this to the correct email address
                recipient_list=['wesleyi@wsdot.wa.gov', ],  # TODO change this to the correct email address
                html_message=msg_html,
            )
            current_user_profile = profile.objects.get(custom_user_id=request.user.id)
            current_user_profile.request_permissions.set(form.cleaned_data['groups'])
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
        formset = assign_permissions_formset(queryset=custom_user.objects.filter(id__in=profile_data.values_list('custom_user_id')))
        if active_requests and active == 'active':
            return render(request, 'pages/assign_permissions_active_requests.html', {'Admin_assignPermissions_all': formset,
                                                                                     'profile_data': profile_data})
        else:
            return render(request, 'pages/AssignPermissions.html', {'Admin_assignPermissions_all': formset,
                                                                    'profile_data': profile_data,
                                                                    'active_requests': active_requests})


@login_required(login_url='/Panacea/login')
def accessibility(request):
    return render(request, 'pages/accessibility.html', {})


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

@login_required(login_url='/Panacea/login')
@group_required('Vanpool reporter')
def Vanpool_report(request, year=None, month=None):
    # Set form parameters
    user_organization_id = profile.objects.get(custom_user_id=request.user.id).organization_id
    user_organization = organization.objects.get(id=user_organization_id)
    organization_data = vanpool_report.objects.filter(organization_id=user_organization_id)

    # logic to select the most recent form or the form requested through the URL
    if not year:
        organization_data_incomplete = organization_data.filter(report_date=None)
        start_year = organization_data_incomplete \
            .aggregate(Min('report_year')) \
            .get('report_year__min')
        start_month = organization_data_incomplete.filter(report_year=start_year) \
            .aggregate(Min('report_month')) \
            .get('report_month__min')
        year = start_year
        month = start_month
    elif not month:
        month = 1

    # Logic to hide year selectors
    min_year = organization_data.all().aggregate(Min('report_year')).get('report_year__min') == year
    max_year = organization_data.all().aggregate(Max('report_year')).get('report_year__max') == year

    # TODO rename to something better (this populates the navigation table)
    past_report_data = vanpool_report.objects.filter(organization_id=user_organization_id, report_year=year)

    # Instance data to link form to data
    form_data = vanpool_report.objects.get(organization_id=user_organization_id, report_year=year, report_month=month)

    # TODO convert to django message framework
    # Logic if form is a new report or is an existing report (Comments are needed before editing an existing reports)
    if form_data.report_date is None:
        new_report = True
    else:
        new_report = False

    # Respond to POST request
    if request.method == 'POST':
        form = VanpoolMonthlyReport(user_organization=user_organization, data=request.POST, instance=form_data, record_id = form_data.id, report_month=month, report_year=year)
        if form.is_valid():
            form.save()
            successful_submit = True  # Triggers a modal that says the form was submitted
            new_report = False

        #TODO Fix this show it shows the form
        else:
            form = VanpoolMonthlyReport(user_organization=user_organization, data=request.POST, instance=form_data,
                                        record_id=form_data.id, report_month=month, report_year=year)
            successful_submit = False

    # If not POST
    else:
        form = VanpoolMonthlyReport(user_organization=user_organization, instance=form_data, record_id = form_data.id, report_month=month, report_year=year)
        successful_submit = False

    if new_report == False:
        form.fields['changeReason'].required = True
    else:
        form.fields['changeReason'].required = False

    return render(request, 'pages/vanpool/Vanpool_report.html', {'form': form,
                                                                 'past_report_data': past_report_data,
                                                                 'year': year,
                                                                 'month': month,
                                                                 'organization': user_organization,
                                                                 'successful_submit': successful_submit,
                                                                 'min_year': min_year,
                                                                 'max_year': max_year,
                                                                 'new_report': new_report}
                  )


@login_required(login_url='/Panacea/login')
@group_required('WSDOT staff')
def Vanpool_expansion_submission(request):
    if request.method == 'POST':
        form = submit_a_new_vanpool_expansion(data = request.POST)
        if form.is_valid():
            instance = form.save(commit = False)
            instance.deadline = instance.latest_vehicle_acceptance + relativedelta(months=+18)
            instance.expansion_goal = int(round(instance.expansion_vans_awarded * .8, 0) + \
                                          instance.vanpools_in_service_at_time_of_award)
            instance.expired = False
            instance.vanpool_goal_met = False
            instance.extension_granted = False
            instance.save()
            # the redirect here is to the expansion page, which triggers the sqlite queries to populate the rest of the data
            return JsonResponse({'redirect': '../Expansion/'})
        else:
            return render(request, 'pages/Vanpool_expansion_submission.html', {'form':form})
    else:
        form = submit_a_new_vanpool_expansion(data=request.POST)
    return render(request, 'pages/vanpool/Vanpool_expansion_submission.html', {'form': form})


@login_required(login_url='/Panacea/login')
def Vanpool_expansion_analysis(request):
    # pulls the latest vanpool data
    calculate_latest_vanpool()
    find_maximum_vanpool()
    calculate_remaining_months()
    calculate_if_goal_has_been_reached()
    f = VanpoolExpansionFilter(request.GET, queryset=vanpool_expansion_analysis.objects.all())
    return render(request, 'pages/vanpool/Vanpool_expansion.html', {'filter': f})


@login_required(login_url='/Panacea/login')
@group_required('WSDOT staff')
def Vanpool_expansion_modify(request, id=None):
    if not id:
        id = 1
    orgs = vanpool_expansion_analysis.objects.filter(expired=False).values('organization_id')
    organization_name = organization.objects.filter(id__in=orgs).values('name')
    vea = vanpool_expansion_analysis.objects.all().filter(expired=False).order_by('organization_id')
    form_data = vanpool_expansion_analysis.objects.get(id=id)

    if request.method == 'POST':
        form = Modify_A_Vanpool_Expansion(data=request.POST, instance=form_data)
        if form.is_valid():
            form.cleaned_data['deadline'] = form.cleaned_data['latest_vehicle_acceptance'] + relativedelta(months=+18)
            form.save()
        else:
            form = Modify_A_Vanpool_Expansion(instance=form_data)

    else:
        form = Modify_A_Vanpool_Expansion(instance=form_data)
    zipped = zip(organization_name, vea)
    return render(request, 'pages/vanpool/Vanpool_expansion_modify.html', {'zipped':zipped, 'id': id, 'form':form})


@login_required(login_url='/Panacea/login')
@group_required('Vanpool reporter', 'WSDOT staff')
def Vanpool_data(request):

    # If it is a request for a chart
    if request.POST:
        form = chart_form(data=request.POST)
        org_list = request.POST.getlist("chart_organizations")
        chart_time_frame = monthdelta(datetime.datetime.now().date(), form.data['chart_time_frame'])
        chart_measure = form.data['chart_measure']

    # Default chart for first load
    else:
        default_time_frame = 36  # months
        chart_time_frame = monthdelta(datetime.datetime.now().date(), default_time_frame)
        org_list = [profile.objects.get(custom_user_id=request.user.id).organization_id]
        chart_measure = 'total_miles_traveled'
        form = chart_form(initial={'chart_organizations': org_list[0],
                                   'chart_measure': chart_measure,
                                   'chart_time_frame': default_time_frame})

    if form.is_valid:
        # Get data for x axis labels
        all_chart_data = [report for report in vanpool_report.objects.filter(organization_id__in=org_list).order_by('organization', 'report_year', 'report_month').all() if
                          chart_time_frame <= report.report_due_date <= datetime.datetime.today().date()]
        x_axis_labels = [report.report_year_month_label for report in all_chart_data]
        x_axis_labels = list(dict.fromkeys(x_axis_labels))

        # Get datasets in the format chart.js needs
        chart_datasets = {}
        color_i = 0
        for org in org_list:
            chart_dataset = [report for report in vanpool_report.objects.filter(organization_id=org).order_by('organization', 'report_year', 'report_month').all() if
                             chart_time_frame <= report.report_due_date <= datetime.datetime.today().date()]
            chart_dataset = [getattr(report, chart_measure) for report in chart_dataset]
            chart_datasets[organization.objects.get(id=org).name] = [json.dumps(list(chart_dataset)), get_wsdot_color(color_i)]
            color_i = color_i + 1

        # Set chart title
        chart_title = form.MEASURE_CHOICES_DICT[chart_measure]

        return render(request, 'pages/vanpool/Vanpool_data.html', {'form': form,
                                                                   'chart_title': chart_title,
                                                                   'chart_measure': chart_measure,
                                                                   'chart_label': x_axis_labels,
                                                                   'chart_datasets_filtered': chart_datasets,
                                                                   'org_list': org_list
                                                                   })
    else:
        raise Http404


@login_required(login_url='/Panacea/login')
@group_required('Vanpool reporter', 'WSDOT staff')
def vanpool_organization_summary(request, org_id=None):

    if request.POST:
        settings_form = organisation_summary_settings(data=request.POST)
        include_years = int(settings_form.data['include_years'])
        org_id = settings_form.data['summary_org']

    else:
        include_years = 3
        org_id = profile.objects.get(custom_user_id=request.user.id).organization_id
        settings_form = organisation_summary_settings(initial={
            "include_years": include_years,
            "summary_org": org_id
        })

    if settings_form.is_valid:
        org_name = organization.objects.get(id=org_id).name
        x_axis_labels, all_charts, summary_table_data, summary_table_data_total = get_vanpool_summary_charts_and_table(
            include_years=include_years,
            is_org_summary=True,
            org_id=org_id,
            include_regions=None,
            include_agency_classifications=None)

    return render(request, 'pages/vanpool/vanpool_organization_summary.html', {'settings_form': settings_form,
                                                                               'chart_label': x_axis_labels,
                                                                               'all_charts': all_charts,
                                                                               'summary_table_data': summary_table_data,
                                                                               'summary_table_data_total': summary_table_data_total,
                                                                               'organization_name': org_name
                                                                               }
                  )


@login_required(login_url='/Panacea/login')
@group_required('Vanpool reporter', 'WSDOT staff')
def vanpool_statewide_summary(request):

    if request.POST:
        settings_form = statewide_summary_settings(data=request.POST)
        include_agency_classifications = request.POST.getlist("include_agency_classifications")
        include_years = int(settings_form.data['include_years'])
        include_regions = settings_form.data['include_regions']

    else:
        include_years = 3
        include_regions = "Statewide"
        include_agency_classifications = [classification[0] for classification in organization.AGENCY_CLASSIFICATIONS]

        settings_form = statewide_summary_settings(initial={
            "include_years": include_years,
            "include_regions": include_regions,
            "include_agency_classifications": include_agency_classifications
        })

    if settings_form.is_valid:
        x_axis_labels, all_charts, summary_table_data, summary_table_data_total = get_vanpool_summary_charts_and_table(
            include_years=include_years,
            is_org_summary=False,
            org_id=None,
            include_regions=include_regions,
            include_agency_classifications=include_agency_classifications)

    return render(request, 'pages/vanpool/vanpool_statewide_summary.html', {'settings_form': settings_form,
                                                                            'chart_label': x_axis_labels,
                                                                            'all_charts': all_charts,
                                                                            'summary_table_data': summary_table_data,
                                                                            'summary_table_data_total': summary_table_data_total,
                                                                            'include_regions': include_regions,
                                                                            'include_agency_classifications': include_agency_classifications
                                                                            }
                  )

@login_required(login_url='/Panacea/login')
def Vanpool_Growth(request):

    # class growth_report_table():
    #
    #     def __init__(self, start_vanpool_report_year, end_vanpool_report_year):
    #         self.start_year= start_vanpool_report_year.report_year
    #         self.end_year = end_vanpool_report_year.report_year
    #         self.start_year_vans = start_vanpool_report_year.report_year
    #         self.most_recent_year_vans = end_vanpool_report_year.vanpool_groups_in_operation + end_vanpool_report_year.vanshare_groups_in_operation
    #         self.percent_growth =
    #         self.absolute_van_growth
    #         self.most_recent_year_folds
    #         self.most_recent_year_start



    listOfAgencies = find_vanpool_organizations()
    for i in listOfAgencies:
        organizationId = i.id
        start_vanpool_report_year = vanpool_report.objects.filter(organization_id=organizationId, report_date__isnull=False, report_month=12,).first()
        end_vanpool_report_year = vanpool_report.objects.filter(organization_id=organizationId, report_date__isnull=False, report_month=12,).last()
        print(start_vanpool_report_year.report_year)
        print(end_vanpool_report_year.report_year)
    return render(request, 'pages/vanpool/VanpoolGrowth.html', {})



@login_required(login_url='/Panacea/login')
def Operation_Summary(request):
    total_vp = vanpool_report.objects.values('report_year').annotate(Sum('vanpool_groups_in_operation')).filter(report_month=12, vanpool_groups_in_operation__isnull=False)
    years = [i['report_year'] for i in total_vp]
    print(years)
    total_vp = vanpool_report.objects.values('report_year').annotate(Sum('vanpool_groups_in_operation')).filter(report_month = 12, vanpool_groups_in_operation__isnull=False)
    vp_percent_change = percent_change_calculation(total_vp, 'vanpool_groups_in_operation__sum')
    total_vs =vanpool_report.objects.values('report_year').annotate(Sum('vanshare_groups_in_operation')).filter(report_month = 12, vanshare_groups_in_operation__isnull=False)
    vs_percent_change = percent_change_calculation(total_vs, 'vanshare_groups_in_operation__sum')
    total_starts = vanpool_report.objects.values('report_year').annotate(Sum('vanpool_group_starts')).filter(vanpool_groups_in_operation__isnull=False)
    starts_percent_change = percent_change_calculation(total_starts, 'vanpool_group_starts__sum')
    total_folds = vanpool_report.objects.values('report_year').annotate(Sum('vanpool_group_folds')).filter(vanpool_groups_in_operation__isnull=False)
    folds_percent_change = percent_change_calculation(total_folds, 'vanpool_group_folds__sum')
    zipped = zip(total_starts, total_vp)
    starts_as_a_percent = []
    for i in zipped:
        percent = round((i[0]['vanpool_group_starts__sum']/i[1]['vanpool_groups_in_operation__sum'])*100, 2)
        starts_as_a_percent.append(percent)
    folds_as_a_percent = []
    zipped = zip(total_folds, total_vp)
    for i in zipped:
        percent = round((i[0]['vanpool_group_folds__sum']/i[1]['vanpool_groups_in_operation__sum'])*100, 2)
        folds_as_a_percent.append(percent)
    zipped = zip(total_starts, total_folds)
    net_vanpool = []
    for start, fold in zipped:
        net_vanpool.append(start['vanpool_group_starts__sum'] - fold['vanpool_group_folds__sum'])
    avg_riders = vanpool_report.objects.values('report_year').annotate(Avg('average_riders_per_van')).filter(vanpool_groups_in_operation__isnull=False)
    avg_miles = vanpool_report.objects.values('report_year').annotate(Avg('average_round_trip_miles')).filter(vanpool_groups_in_operation__isnull=False)
    print(avg_riders)
    print(avg_miles)
    vp_totals = zip(total_vp, vp_percent_change)
    vs_totals = zip(total_vs, vs_percent_change)
    starts = zip(total_starts, starts_percent_change)
    folds = zip(total_folds, folds_percent_change)
    empty_list = ['']*len(total_vp)
    starts_as_percent = zip(starts_as_a_percent, empty_list)
    folds_as_percent = zip(folds_as_a_percent, empty_list)
    net_vans = zip(net_vanpool, empty_list)
    average_riders = zip(avg_riders, empty_list)
    average_miles = zip(avg_miles, empty_list)

    return render(request, 'pages/vanpool/OperationSummary.html', {'vp_totals': vp_totals, 'vs_totals': vs_totals, 'starts':starts, 'folds': folds, 'starts_as_a_percent': starts_as_percent,
                                                                   'folds_as_percent': folds_as_percent, 'net_vans': net_vans, 'average_riders': average_riders, 'average_miles': average_miles, 'years':years})

# endregion


# region summary
def summary_instructions(request):
    return render(request, 'pages/summary/summary_instructions.html', {})


def organizational_information(request):
    user_profile_data = profile.objects.get(custom_user=request.user.id)
    org = user_profile_data.organization
    org_name = org.name
    form = organization_profile(instance=org)
    if request.POST:
        if form.is_valid():
            form.save()
            return redirect('organizational_information')

    return render(request, 'pages/summary/organizational_information.html', {'org_name': org_name, 'form': form})


def ntd_upload(request):
    return render(request, 'pages/summary/ntd_upload.html', {})


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
        form = cover_sheet_organization(data=request.POST, files=request.FILES)

        if form.is_valid():
            instance = form.save(commit=False)
            instance.organization = org
            instance.id = cover_sheet_instance.id
            filepath = request.FILES.get('organization_logo_input', False)

            if filepath:
                instance.organization_logo = filepath.read()
                base64_logo = base64.encodebytes(instance.organization_logo).decode("utf-8")
            else:
                instance.organization_logo = cover_sheet_instance.organization_logo

            instance.save()

    return render(request, 'pages/summary/cover_sheet_organization.html', {'form': form,
                                                                           'org_name': org_name,
                                                                           'base64_logo': base64_logo})


def cover_sheet_service_view(request):

    user_profile_data = profile.objects.get(custom_user=request.user.id)
    org = user_profile_data.organization
    service_type = org.summary_organization_classifications

    cover_sheet_instance, created = cover_sheet.objects.get_or_create(organization=org)

    form = cover_sheet_service(instance=cover_sheet_instance)

    if request.POST:
        form = cover_sheet_service(data=request.POST, instance=cover_sheet_instance)

        if form.is_valid():
            print("valid")
            form.save()
        else:
            print("Error")
            for error in form.errors:
                print(error)

    return render(request, 'pages/summary/cover_sheet_service.html', {'service_type': service_type, 'form': form})


def summary_report_data(request):
    return render(request, 'pages/summary/report_data.html')


def summary_modes(request):
    org = find_user_organization(request.user.id)
    modes = ServiceOffered.objects.filter(organization_id = org).values('administration_of_mode', 'mode')
    mode_formset = formset_factory(service_offered, min_num=len(modes), extra=2)
    formset = mode_formset(initial=[{'administration_of_mode': x['administration_of_mode'], 'mode': x['mode']} for x in modes])
    modes = ServiceOffered.objects.filter(organization_id = org)
    mode_formset = formset_factory(service_offered, min_num=2)
    formset = mode_formset()
    # TODO add in date time of changes and user id to this dataset date time as native, foreign key for user
    if request.method == 'POST':
        formset = mode_formset(data=request.POST)
        print(formset.errors)
        print(formset.is_valid())
        for form in formset:
            if 'mode' in form.changed_data:
                if form.is_valid():
                    print(form.is_valid())
                    instance = form.save(commit=False)
                    instance.organization = org
                    form.save()
        return redirect('report_transit_data')
    return render(request, 'pages/summary/summary_modes.html', {'formset': formset, 'modes': modes, 'org': org})

def report_transit_data(request):
    return render(request, 'pages/summary/report_transit_data.html')


def report_revenues(request, year = None):
    user_org = find_user_organization(request.user.id)

    if year is None:
        year = get_current_summary_report_year()
    previous_year = year - 1
    two_years_ago = year - 2

    my_formset_factory = modelformset_factory(model=SummaryRevenues,
                                              form=summary_revenue_form,
                                              extra=0)

    # Function start TODO move this
    def get_or_create_summary_revenue_queryset(year, organization, user):
        classification = organization.summary_organization_classifications
        classification = filter_revenue_sheet_by_classification(classification)
        print(classification)
        source_ids = list(SummaryRevenues.objects.filter(organization_id=user_org.id, year=year).values_list(
            'specific_revenue_source_id', flat=True))
        all_revenue_sources = list(revenue_source.objects.filter(agency_funding_classification=classification).values_list("id", flat=True))
        print(all_revenue_sources)
        print(source_ids)

        if len(source_ids) != len(all_revenue_sources):
            missing_ids = list(set(all_revenue_sources) - set(source_ids))
            print(missing_ids)

            with transaction.atomic():
                for my_id in missing_ids:
                   SummaryRevenues.objects.create(year=year,
                                                   specific_revenue_source_id=my_id,
                                                   organization=organization,
                                                   specific_revenue_source=None,
                                                   report_by=user)
        return SummaryRevenues.objects.filter(organization_id=user_org.id,
                                              year=year).order_by('specific_revenue_source').all()

    # Function end

    query_sets = {'this_year': get_or_create_summary_revenue_queryset(year, user_org, request.user),
                  'previous_year': get_or_create_summary_revenue_queryset(previous_year, user_org, request.user),
                  'two_years_ago': get_or_create_summary_revenue_queryset(two_years_ago, user_org, request.user)}


    formsets = {}
    for key, value in query_sets.items():
        formsets[key] = my_formset_factory(queryset=value, prefix=key)

    # print(formset.total_form_count())

    if request.method == 'POST':
        print("post")
        for key, value in formsets.items():
            print(key)
            formsets[key] = my_formset_factory(request.POST, queryset=query_sets[key], prefix=key)
            if formsets[key].is_valid():
                for form in formsets[key]:
                    form.save()
            else:
                print(formsets[key].errors)

    return render(request, 'pages/summary/report_revenues.html', {'formsets': formsets,
                                                                  'form_range': range(len(formsets['this_year']))})


def report_expenses(request, year=None):
    user_org = find_user_organization(request.user.id)

    if year is None:
        year = get_current_summary_report_year()
    previous_year = year - 1
    two_years_ago = year - 2

    my_formset_factory = modelformset_factory(model=SummaryExpenses,
                                              form=summary_expense_form,
                                              extra=0)

    #Function start TODO move this
    def get_or_create_summary_expenses_queryset(year, organization, user):
        source_ids = list(SummaryExpenses.objects.filter(organization_id=user_org.id, year=year).values_list(
            'specific_expense_source_id', flat=True))
        all_expense_sources = list(expenses_source.objects.values_list("id", flat=True))

        if len(source_ids) != len(all_expense_sources):
            missing_ids = list(set(all_expense_sources) - set(source_ids))
            print(missing_ids)

            with transaction.atomic():
                for my_id in missing_ids:
                    SummaryExpenses.objects.create(year=year,
                                                   specific_expense_source_id=my_id,
                                                   organization=organization,
                                                   specific_expense_source=None,
                                                   report_by=user
                                                   )
        return SummaryExpenses.objects.filter(organization_id=user_org.id,
                                              year=year).order_by('specific_expense_source').all()
    #Function end

    query_sets = {'this_year': get_or_create_summary_expenses_queryset(year, user_org, request.user),
                  'previous_year': get_or_create_summary_expenses_queryset(previous_year, user_org, request.user),
                  'two_years_ago': get_or_create_summary_expenses_queryset(two_years_ago, user_org, request.user)}

    formsets = {}
    for key, value in query_sets.items():
        formsets[key] = my_formset_factory(queryset=value, prefix=key)

    # print(formset.total_form_count())

    if request.method == 'POST':
        print("post")
        for key, value in formsets.items():
            formsets[key] = my_formset_factory(request.POST, queryset=query_sets[key], prefix=key)
            if formsets[key].is_valid():
                for form in formsets[key]:
                    form.save()
            else:
                print(formsets[key].errors)

    return render(request, 'pages/summary/report_expenses.html', {'formsets': formsets,
                                                                  'form_range': range(len(formsets['this_year']))})


def review_data(request):
    return render(request, 'pages/summary/review_data.html')


#def test(request):
    #
    #     form = test_field(custom_field_name="test value")
    #     # import pdb
    #     # pdb.set_trace()
    #     if request.method == 'POST':
    #         form = test_field(data=request.POST, custom_field_name=form.custom_field_name)
    #         print("post")
    #         if form.is_valid():
    #             print("form valid")
    #             form.save()
    #
  #  return render(request, 'pages/Blank.html', {'form': form})

# endregion





