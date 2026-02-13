"""
URL configuration for JobTrack Automate.

Routes all the URL patterns to the correct views across
the different apps in the project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('applications.urls')),
    path('accounts/', include('accounts.urls')),
    path('documents/', include('documents.urls')),
    path('api/', include('applications.api.urls')),
    path('api/auth/', include('rest_framework.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
