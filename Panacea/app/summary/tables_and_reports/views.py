from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from Panacea.tables import build_operations_data_table, build_community_provider_revenue_table, build_revenue_table
from Panacea.utilities import get_current_summary_report_year
from Panacea.app.user_and_org.models import *


@login_required(login_url='/Panacea/login')
def view_annual_operating_information(request):
    current_year = get_current_summary_report_year()
    years = [current_year-2, current_year-1, current_year]
    current_user_id = request.user.id
    user_org_id = profile.objects.get(custom_user_id=current_user_id).organization_id
    org_classification = organization.objects.get(id = user_org_id).summary_organization_classifications
    df = build_operations_data_table(years, [user_org_id], org_classification)
    heading_list = ['Annual Operating Information'] + years +['One Year Change (%)']
    data = df.to_dict(orient = 'records')
    return render(request, 'pages/summary/view_agency_report.html', {'data':data, 'years': heading_list})


@login_required(login_url='/Panacea/login')
def view_financial_information(request):
    current_year = get_current_summary_report_year()
    years = [current_year - 2, current_year - 1, current_year]
    current_user_id = request.user.id
    user_org_id = profile.objects.get(custom_user_id=current_user_id).organization_id
    org_classification = organization.objects.get(id=user_org_id).summary_organization_classifications
    if str(org_classification) == 'Community provider':
        revenuedf = build_community_provider_revenue_table(years, [user_org_id])
    else:
        revenuedf = build_revenue_table(years, [user_org_id], org_classification)
    financial_data = revenuedf.to_dict(orient = 'records')
    financial_heading_years = ['Financial Information'] + years + ['One Year Change(%)']
    return render(request, 'pages/summary/view_financial_report.html', {'financial_data':financial_data, 'finance_years': financial_heading_years})


@login_required(login_url='/Panacea/login')
def view_rollup(request):
    current_year = get_current_summary_report_year()
    years = [current_year-2, current_year-1, current_year]
    current_user_id = request.user.id
    user_org_id = profile.objects.get(custom_user_id=current_user_id).organization_id
    rollup_data = build_total_funds_by_source(years, [user_org_id])
    rollup_heading = ['Total Funds by Source'] + years + ['One Year Change (%)']
    rollup_data = rollup_data.to_dict(orient = 'records')
    return render(request, 'pages/summary/view_agency_rollup.html', {'rollup_data': rollup_data, 'rollup_heading': rollup_heading})


@login_required(login_url='/Panacea/login')
def view_statewide_measures(request):
    years = [2013, 2014, 2015, 2016, 2017, 2018]
    statewide_measure_list = []
    list_of_headings = []
    statewide_measure_dictionary = {'Revenue Vehicle Hours by Service Mode': ("Revenue Vehicle Hours"), 'Revenue Vehicle Miles by Service Mode': ('Revenue Vehicle Miles'),
    'Passenger Trips by Service Mode':('Passenger Trips'), 'Farebox Revenues by Service Mode': ('Farebox Revenues'), 'Operating Expenses by Service Mode': ('Operating Expenses')}
    for key, measure in statewide_measure_dictionary.items():
        df = generate_performance_measure_table(measure, years)
        heading_list = [key] + years + ['One Year Change (%)']
        list_of_headings.append(heading_list)
        statewide_measure_list.append(df.to_dict(orient = 'records'))
    return render(request, 'pages/summary/view_statewide_measures.html', {'headings': list_of_headings, 'data': statewide_measure_list, 'titles': statewide_measure_dictionary.keys()})


@login_required(login_url='/Panacea/login')
def view_performance_measures(request):
    years = [2013, 2014, 2015, 2016, 2017, 2018]
    performance_measure_list = []
    list_of_headings = []
    performance_measure_dictionary = {
    'Operating Costs per Passenger Trip': ('Operating Expenses', 'Passenger Trips'), 'Operating Cost per Revenue Vehicle Hour':('Operating Expenses', 'Revenue Vehicle Hours'),
    'Passenger Trips per Revenue Vehicle Hour':('Passenger Trips', 'Revenue Vehicle Hours'), 'Passenger Trips per Revenue Vehicle Mile':('Passenger Trips', 'Revenue Vehicle Miles'),
                                      'Revenue Vehicle Hours per Employee': ('Revenue Vehicle Hours', 'Employees - FTEs'), 'Farebox Recovery Ratio/Vanpool Revenue Recovery': ('Farebox Revenues', 'Operating Expenses')}
    for key, measure in performance_measure_dictionary.items():
        df = generate_performance_measure_table(measure, years)
        heading_list = [key] + years + ['One Year Change (%)']
        list_of_headings.append(heading_list)
        performance_measure_list.append(df.to_dict(orient = 'records'))

    return render(request, 'pages/summary/view_performance_measures.html', {'headings': list_of_headings, 'data': performance_measure_list, 'titles': performance_measure_dictionary.keys()})


@login_required(login_url='/Panacea/login')
def view_statewide_rollup(request):
    year = 2017
    revenue_df = create_statewide_revenue_table(year)
    expense_df = create_statewide_expense_table(year)
    return render(request, 'pages/summary/view_statewide_rollup.html')


@login_required(login_url='/Panacea/login')
def view_statewide_operating(request):
    current_year = get_current_summary_report_year()
    years = [current_year-2, current_year-1, current_year]
    current_user_id = request.user.id
    user_org_id = profile.objects.get(custom_user_id=current_user_id).organization_id
    org_classification = organization.objects.get(id = user_org_id).summary_organization_classifications
    org_list = list(organization.objects.filter(summary_organization_classifications = org_classification).value_list('id', flat = True))
    return render(request)


@login_required(login_url='/Panacea/login')
def view_statewide_revenue(request):
    return render(request)


@login_required(login_url='/Panacea/login')
def view_statewide_investment_tables(request):
    return render(request)


@login_required(login_url='/Panacea/login')
def view_statewide_statistics(request):
    statewide_mode_statistics_list = []
    list_of_headings = []
    year = 2017
    transit_mode_names = ['Fixed Route', 'Commuter Bus', 'Trolley Bus', 'Route Deviated', 'Demand Response', 'Vanpool', 'Commuter Rail', 'Light Rail', 'Streetcar']
    for mode in transit_mode_names:
        df, heading = generate_mode_by_agency_tables(mode, year)
        statewide_mode_statistics_list.append(df.to_dict(orient = 'records'))
        list_of_headings.append(heading)
    return render(request, 'pages/summary/view_statewide_statistics.html', {'headings': list_of_headings, 'data':statewide_mode_statistics_list})
