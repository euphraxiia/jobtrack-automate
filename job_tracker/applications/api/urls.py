"""API URL configuration for the applications app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView, TokenRefreshView
)

from . import views

router = DefaultRouter()
router.register(r'applications', views.ApplicationViewSet, basename='api-application')
router.register(r'companies', views.CompanyViewSet, basename='api-company')
router.register(r'jobs', views.JobViewSet, basename='api-job')
router.register(r'reminders', views.ReminderViewSet, basename='api-reminder')

urlpatterns = [
    # Router-based URLs (CRUD for applications, companies, jobs, reminders)
    path('', include(router.urls)),

    # Dashboard stats
    path('dashboard/stats/', views.DashboardStatsView.as_view(), name='api-dashboard-stats'),

    # Automation trigger
    path('automation/apply/', views.AutomationApplyView.as_view(), name='api-automation-apply'),

    # Job search
    path('jobs/search/', views.JobSearchView.as_view(), name='api-job-search'),

    # Document upload
    path('documents/upload/', views.DocumentUploadView.as_view(), name='api-document-upload'),

    # JWT authentication
    path('token/', TokenObtainPairView.as_view(), name='token-obtain'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
]
