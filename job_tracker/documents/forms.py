"""Forms for the documents app."""
from django import forms

from .models import Document, CoverLetterTemplate


class DocumentForm(forms.ModelForm):
    """Form for uploading a document."""

    class Meta:
        model = Document
        fields = ['doc_type', 'title', 'file', 'version', 'is_active', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'e.g. Senior Developer CV v3'
            }),
        }


class CoverLetterTemplateForm(forms.ModelForm):
    """Form for creating or editing a cover letter template."""

    class Meta:
        model = CoverLetterTemplate
        fields = ['name', 'content', 'job_type', 'is_default']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 15,
                'placeholder': (
                    'Dear Hiring Manager,\n\n'
                    'I am writing to express my interest in the {job_title} '
                    'position at {company_name}...'
                ),
            }),
        }
