from django.urls import path
from Panacea.vanpool import views

urlpatterns = [
    path('report/', views.Vanpool_report, name="Vanpool_report"),
    path('report/<int:year>/<int:month>/', views.Vanpool_report, name="Vanpool_report"),
    path('data/', views.Vanpool_data, name="Vanpool_data"),
    path('download_vanpool_data', views.download_vanpool_data, name='download_vanpool_data'),
    path('statewide_summary/', views.vanpool_statewide_summary, name="vanpool_statewide_summary"),
    path('organization_summary/', views.vanpool_organization_summary, name="vanpool_organization_summary"),
    path('organization_summary/<int:org_id>/', views.vanpool_organization_summary,
         name="vanpool_organization_summary"),
    path('admin/expansion/', views.Vanpool_expansion_analysis, name="Vanpool_expansion_analysis"),
    path('admin/operation_summary', views.Operation_Summary, name='Operation_Summary'),
    path('admin/vanpool_growth', views.Vanpool_Growth, name='Vanpool_Growth'),
    path('admin/vanpool_expansion_modify', views.Vanpool_expansion_modify, name="Vanpool_expansion_modify"),
    path('admin/vanpool_expansion_modify/<int:id>', views.Vanpool_expansion_modify,
         name="Vanpool_expansion_modify"),
    path('admin/vanpool_expansion_submission/', views.Vanpool_expansion_submission,
         name="Vanpool_expansion_submission"),
]
