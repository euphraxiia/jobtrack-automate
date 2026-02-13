"""URL patterns for the documents app."""
from django.urls import path

from . import views

urlpatterns = [
    path('', views.DocumentListView.as_view(), name='document-list'),
    path('upload/', views.DocumentUploadView.as_view(), name='document-upload'),
    path('<int:pk>/delete/', views.DocumentDeleteView.as_view(), name='document-delete'),
    path('templates/', views.CoverLetterTemplateListView.as_view(), name='template-list'),
    path('templates/new/', views.CoverLetterTemplateCreateView.as_view(), name='template-create'),
]
