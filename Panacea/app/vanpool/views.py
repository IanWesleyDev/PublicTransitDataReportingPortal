import csv
import datetime
import json

from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
from django.db.models import Min, Max, Avg, Sum
from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import render

from Panacea.decorators import group_required
from Panacea.filters import VanpoolExpansionFilter
from Panacea.vanpool.forms import *
from Panacea.utilities import calculate_latest_vanpool, find_maximum_vanpool, calculate_remaining_months, \
    calculate_if_goal_has_been_reached, monthdelta, get_wsdot_color, complete_data, percent_change_calculation, \
    get_vanpool_summary_charts_and_table


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
        form = VanpoolMonthlyReport(user_organization=user_organization, data=request.POST, instance=form_data,
                                    record_id=form_data.id, report_month=month, report_year=year)
        if form.is_valid():
            form.save()
            successful_submit = True  # Triggers a modal that says the form was submitted
            new_report = False

        # TODO Fix this show it shows the form
        else:
            form = VanpoolMonthlyReport(user_organization=user_organization, data=request.POST, instance=form_data,
                                        record_id=form_data.id, report_month=month, report_year=year)
            successful_submit = False

    # If not POST
    else:
        form = VanpoolMonthlyReport(user_organization=user_organization, instance=form_data, record_id=form_data.id,
                                    report_month=month, report_year=year)
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
        form = submit_a_new_vanpool_expansion(data=request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
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
            return render(request, 'pages/Vanpool_expansion_submission.html', {'form': form})
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
        form = vanpool_metric_chart_form(data=request.POST)
        org_list = request.POST.getlist("chart_organizations")
        chart_time_frame = monthdelta(datetime.datetime.now().date(), form.data['chart_time_frame'])
        chart_measure = form.data['chart_measure']

    # Default chart for first load
    else:
        default_time_frame = 36  # months
        chart_time_frame = monthdelta(datetime.datetime.now().date(), default_time_frame)
        org_list = [profile.objects.get(custom_user_id=request.user.id).organization_id]
        chart_measure = 'total_miles_traveled'
        form = vanpool_metric_chart_form(initial={'chart_organizations': org_list[0],
                                                  'chart_measure': chart_measure,
                                                  'chart_time_frame': default_time_frame})

    if form.is_valid:
        # Get data for x axis labels
        all_chart_data = [report for report in
                          vanpool_report.objects.filter(organization_id__in=org_list).order_by('organization',
                                                                                               'report_year',
                                                                                               'report_month').all() if
                          chart_time_frame <= report.report_due_date <= datetime.datetime.today().date()]
        x_axis_labels = [report.report_year_month_label for report in all_chart_data]
        x_axis_labels = list(dict.fromkeys(x_axis_labels))

        # Get datasets in the format chart.js needs
        chart_datasets = {}
        color_i = 0
        for org in org_list:
            chart_dataset = [report for report in
                             vanpool_report.objects.filter(organization_id=org).order_by('organization', 'report_year',
                                                                                         'report_month').all() if
                             chart_time_frame <= report.report_due_date <= datetime.datetime.today().date()]
            chart_dataset = [getattr(report, chart_measure) for report in chart_dataset]
            chart_datasets[organization.objects.get(id=org).name] = [json.dumps(list(chart_dataset)),
                                                                     get_wsdot_color(color_i)]
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
def download_vanpool_data(request, org_id = None):
    org_id = profile.objects.get(custom_user_id=request.user.id).organization_id
    org_name = organization.objects.get(id=org_id).name
    vanshare_existence = organization.objects.get(id = org_id).vanshare_program
    vanpool_data = vanpool_report.objects.filter(organization_id = org_id, vanpool_groups_in_operation__isnull=False)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="{}.csv"'.format(org_name)
    writer = csv.writer(response)
    count = 0

    for k in vanpool_data:
        if count == 0:
            writer.writerow(list(k.__dict__.keys())[1:])
            count +=1
        else:
            writer.writerow(list(k.__dict__.values())[1:])
    return response


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

    latest_complete_data = complete_data()

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
                                                                            'include_agency_classifications': include_agency_classifications,
                                                                            'latest_complete_data': latest_complete_data
                                                                            }
                  )


@login_required(login_url='/Panacea/login')
@group_required('WSDOT staff')
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
        start_vanpool_report_year = vanpool_report.objects.filter(organization_id=organizationId,
                                                                  report_date__isnull=False, report_month=12, ).first()
        end_vanpool_report_year = vanpool_report.objects.filter(organization_id=organizationId,
                                                                report_date__isnull=False, report_month=12, ).last()
    return render(request, 'pages/vanpool/VanpoolGrowth.html', {})



@login_required(login_url='/Panacea/login')
@group_required('WSDOT staff')
def Operation_Summary(request):
    total_vp = vanpool_report.objects.values('report_year').annotate(Sum('vanpool_groups_in_operation')).filter(
        report_month=12, vanpool_groups_in_operation__isnull=False)
    years = [i['report_year'] for i in total_vp]
    print(years)
    total_vp = vanpool_report.objects.values('report_year').annotate(Sum('vanpool_groups_in_operation')).filter(
        report_month=12, vanpool_groups_in_operation__isnull=False)
    vp_percent_change = percent_change_calculation(total_vp, 'vanpool_groups_in_operation__sum')
    total_vs = vanpool_report.objects.values('report_year').annotate(Sum('vanshare_groups_in_operation')).filter(
        report_month=12, vanshare_groups_in_operation__isnull=False)
    vs_percent_change = percent_change_calculation(total_vs, 'vanshare_groups_in_operation__sum')
    total_starts = vanpool_report.objects.values('report_year').annotate(Sum('vanpool_group_starts')).filter(
        vanpool_groups_in_operation__isnull=False)
    starts_percent_change = percent_change_calculation(total_starts, 'vanpool_group_starts__sum')
    total_folds = vanpool_report.objects.values('report_year').annotate(Sum('vanpool_group_folds')).filter(
        vanpool_groups_in_operation__isnull=False)
    folds_percent_change = percent_change_calculation(total_folds, 'vanpool_group_folds__sum')
    zipped = zip(total_starts, total_vp)
    starts_as_a_percent = []
    for i in zipped:
        percent = round((i[0]['vanpool_group_starts__sum'] / i[1]['vanpool_groups_in_operation__sum']) * 100, 2)
        starts_as_a_percent.append(percent)
    folds_as_a_percent = []
    zipped = zip(total_folds, total_vp)
    for i in zipped:
        percent = round((i[0]['vanpool_group_folds__sum'] / i[1]['vanpool_groups_in_operation__sum']) * 100, 2)
        folds_as_a_percent.append(percent)
    zipped = zip(total_starts, total_folds)
    net_vanpool = []
    for start, fold in zipped:
        net_vanpool.append(start['vanpool_group_starts__sum'] - fold['vanpool_group_folds__sum'])
    avg_riders = vanpool_report.objects.values('report_year').annotate(Avg('average_riders_per_van')).filter(
        vanpool_groups_in_operation__isnull=False)
    avg_miles = vanpool_report.objects.values('report_year').annotate(Avg('average_round_trip_miles')).filter(
        vanpool_groups_in_operation__isnull=False)
    print(avg_riders)
    print(avg_miles)
    vp_totals = zip(total_vp, vp_percent_change)
    vs_totals = zip(total_vs, vs_percent_change)
    starts = zip(total_starts, starts_percent_change)
    folds = zip(total_folds, folds_percent_change)
    empty_list = [''] * len(total_vp)
    starts_as_percent = zip(starts_as_a_percent, empty_list)
    folds_as_percent = zip(folds_as_a_percent, empty_list)
    net_vans = zip(net_vanpool, empty_list)
    average_riders = zip(avg_riders, empty_list)
    average_miles = zip(avg_miles, empty_list)

    return render(request, 'pages/vanpool/OperationSummary.html',
                  {'vp_totals': vp_totals, 'vs_totals': vs_totals, 'starts': starts, 'folds': folds,
                   'starts_as_a_percent': starts_as_percent,
                   'folds_as_percent': folds_as_percent, 'net_vans': net_vans, 'average_riders': average_riders,
                   'average_miles': average_miles, 'years': years})

