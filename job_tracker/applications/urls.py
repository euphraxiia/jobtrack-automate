"""URL patterns for the applications app."""
from django.urls import path

from . import views

urlpatterns = [
    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard-home'),

    # Applications CRUD
    path(
        'applications/',
        views.ApplicationListView.as_view(),
        name='application-list'
    ),
    path(
        'applications/new/',
        views.ApplicationCreateView.as_view(),
        name='application-create'
    ),
    path(
        'applications/<int:pk>/',
        views.ApplicationDetailView.as_view(),
        name='application-detail'
    ),
    path(
        'applications/<int:pk>/edit/',
        views.ApplicationUpdateView.as_view(),
        name='application-update'
    ),
    path(
        'applications/<int:pk>/delete/',
        views.ApplicationDeleteView.as_view(),
        name='application-delete'
    ),
    path(
        'applications/<int:application_pk>/reminder/',
        views.add_reminder,
        name='add-reminder'
    ),

    # Companies
    path(
        'companies/',
        views.CompanyListView.as_view(),
        name='company-list'
    ),
    path(
        'companies/new/',
        views.CompanyCreateView.as_view(),
        name='company-create'
    ),

    # Analytics and export
    path('analytics/', views.AnalyticsView.as_view(), name='analytics'),
    path('export/csv/', views.export_applications_csv, name='export-csv'),
]
