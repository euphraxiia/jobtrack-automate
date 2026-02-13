"""
Views for the applications app.

Handles all the page rendering for the job application tracking
features - the dashboard, list views, detail pages, and forms.
"""
import csv
from typing import Any, Dict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q, QuerySet
from django.http import HttpResponse, HttpRequest
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
)

from .models import Application, Company, Job, Reminder, ApplicationActivity
from .forms import (
    ApplicationForm, CompanyForm, JobForm,
    ApplicationFilterForm, ReminderForm
)
from .services.analytics_engine import AnalyticsEngine


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    The main dashboard page with all the stats and charts.
    Shows a summary of where things stand with applications.
    """
    template_name = 'applications/dashboard.html'

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        user = self.request.user
        engine = AnalyticsEngine()

        context['total_applications'] = Application.objects.filter(user=user).count()
        context['this_month'] = engine.get_monthly_count(user)
        context['response_rate'] = engine.calculate_response_rate(user)
        context['interview_rate'] = engine.calculate_interview_rate(user)
        context['avg_response_days'] = engine.calculate_avg_response_time(user)
        context['status_breakdown'] = engine.get_applications_by_status(user)
        context['recent_applications'] = (
            Application.objects.filter(user=user)
            .select_related('job', 'company')[:5]
        )
        context['upcoming_reminders'] = (
            Reminder.objects.filter(
                application__user=user,
                is_sent=False,
                reminder_date__gte=timezone.now().date()
            )[:5]
        )
        context['top_companies'] = engine.get_top_companies(user)
        context['board_stats'] = engine.get_success_by_board(user)

        return context


class ApplicationListView(LoginRequiredMixin, ListView):
    """
    Show all applications for the logged-in user.
    Supports filtering by status, priority, and search terms.
    """
    model = Application
    template_name = 'applications/application_list.html'
    context_object_name = 'applications'
    paginate_by = 20

    def get_queryset(self) -> QuerySet:
        queryset = (
            Application.objects.filter(user=self.request.user)
            .select_related('job', 'company')
        )

        # Apply filters from the query string
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)

        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(job__title__icontains=search) |
                Q(company__name__icontains=search) |
                Q(notes__icontains=search)
            )

        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)

        date_to = self.request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        return queryset

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['filter_form'] = ApplicationFilterForm(self.request.GET)
        return context


class ApplicationDetailView(LoginRequiredMixin, DetailView):
    """Show the full details of a single application."""
    model = Application
    template_name = 'applications/application_detail.html'
    context_object_name = 'application'

    def get_queryset(self) -> QuerySet:
        return Application.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['activities'] = (
            ApplicationActivity.objects.filter(application=self.object)[:20]
        )
        context['reminder_form'] = ReminderForm()
        return context


class ApplicationCreateView(LoginRequiredMixin, CreateView):
    """Create a new job application."""
    model = Application
    form_class = ApplicationForm
    template_name = 'applications/application_form.html'
    success_url = reverse_lazy('application-list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Application added successfully.')
        return super().form_valid(form)


class ApplicationUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing application."""
    model = Application
    form_class = ApplicationForm
    template_name = 'applications/application_form.html'

    def get_queryset(self) -> QuerySet:
        return Application.objects.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Application updated.')
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse_lazy('application-detail', kwargs={'pk': self.object.pk})


class ApplicationDeleteView(LoginRequiredMixin, DeleteView):
    """Delete an application."""
    model = Application
    success_url = reverse_lazy('application-list')

    def get_queryset(self) -> QuerySet:
        return Application.objects.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Application deleted.')
        return super().form_valid(form)


class CompanyListView(LoginRequiredMixin, ListView):
    """Show all companies in the database."""
    model = Company
    template_name = 'applications/company_list.html'
    context_object_name = 'companies'
    paginate_by = 20

    def get_queryset(self) -> QuerySet:
        queryset = Company.objects.all()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(industry__icontains=search)
            )
        return queryset


class CompanyCreateView(LoginRequiredMixin, CreateView):
    """Add a new company."""
    model = Company
    form_class = CompanyForm
    template_name = 'applications/company_form.html'
    success_url = reverse_lazy('company-list')

    def form_valid(self, form):
        messages.success(self.request, 'Company added.')
        return super().form_valid(form)


class AnalyticsView(LoginRequiredMixin, TemplateView):
    """
    Detailed analytics page with charts and graphs.
    Shows trends over time and breakdowns by category.
    """
    template_name = 'applications/analytics.html'

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        user = self.request.user
        engine = AnalyticsEngine()

        context['response_rate'] = engine.calculate_response_rate(user)
        context['interview_rate'] = engine.calculate_interview_rate(user)
        context['status_breakdown'] = engine.get_applications_by_status(user)
        context['monthly_trend'] = engine.get_monthly_trend(user)
        context['board_stats'] = engine.get_success_by_board(user)
        context['top_companies'] = engine.get_top_companies(user)

        return context


def export_applications_csv(request: HttpRequest) -> HttpResponse:
    """Export all applications as a CSV file for the current user."""
    if not request.user.is_authenticated:
        return redirect('login')

    applications = (
        Application.objects.filter(user=request.user)
        .select_related('job', 'company')
    )

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="applications.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Job Title', 'Company', 'Status', 'Priority',
        'Applied Date', 'Source', 'Notes'
    ])

    for app in applications:
        writer.writerow([
            app.job.title,
            app.company.name,
            app.get_status_display(),
            app.get_priority_display(),
            app.applied_date,
            app.job.get_source_platform_display(),
            app.notes,
        ])

    return response


def add_reminder(request: HttpRequest, application_pk: int) -> HttpResponse:
    """Add a reminder to an application."""
    if request.method != 'POST':
        return redirect('application-list')

    application = get_object_or_404(
        Application, pk=application_pk, user=request.user
    )
    form = ReminderForm(request.POST)

    if form.is_valid():
        reminder = form.save(commit=False)
        reminder.application = application
        reminder.save()
        messages.success(request, 'Reminder set.')
    else:
        messages.error(request, 'Could not set reminder. Check the form.')

    return redirect('application-detail', pk=application_pk)
