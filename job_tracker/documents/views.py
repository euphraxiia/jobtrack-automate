"""
Views for the documents app.

Handles uploading, viewing, and managing documents
like CVs, cover letters, and certificates.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DeleteView, DetailView

from .models import Document, CoverLetterTemplate
from .forms import DocumentForm, CoverLetterTemplateForm


class DocumentListView(LoginRequiredMixin, ListView):
    """Show all documents uploaded by the current user."""
    model = Document
    template_name = 'documents/document_list.html'
    context_object_name = 'documents'

    def get_queryset(self):
        return Document.objects.filter(user=self.request.user)


class DocumentUploadView(LoginRequiredMixin, CreateView):
    """Upload a new document."""
    model = Document
    form_class = DocumentForm
    template_name = 'documents/document_form.html'
    success_url = reverse_lazy('document-list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Document uploaded.')
        return super().form_valid(form)


class DocumentDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a document."""
    model = Document
    success_url = reverse_lazy('document-list')

    def get_queryset(self):
        return Document.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Document deleted.')
        return super().delete(request, *args, **kwargs)


class CoverLetterTemplateListView(LoginRequiredMixin, ListView):
    """Show all cover letter templates."""
    model = CoverLetterTemplate
    template_name = 'documents/template_list.html'
    context_object_name = 'templates'

    def get_queryset(self):
        return CoverLetterTemplate.objects.filter(user=self.request.user)


class CoverLetterTemplateCreateView(LoginRequiredMixin, CreateView):
    """Create a new cover letter template."""
    model = CoverLetterTemplate
    form_class = CoverLetterTemplateForm
    template_name = 'documents/template_form.html'
    success_url = reverse_lazy('template-list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Template created.')
        return super().form_valid(form)
