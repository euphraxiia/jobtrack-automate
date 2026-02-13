import pytest
from django.test import Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from documents.models import CoverLetterTemplate, Document
from applications.tests.factories import UserFactory


@pytest.mark.django_db
class TestDocumentModel:
    """Tests for the Document model."""

    def test_create_document(self):
        user = UserFactory()
        fake_file = SimpleUploadedFile(
            'test_cv.pdf',
            b'%PDF-1.4 fake content',
            content_type='application/pdf'
        )
        doc = Document.objects.create(
            user=user,
            title='My CV',
            doc_type='cv',
            file=fake_file,
            version=1,
            is_active=True
        )
        assert doc.pk is not None
        assert doc.title == 'My CV'

    def test_document_str(self):
        user = UserFactory()
        fake_file = SimpleUploadedFile('cv.pdf', b'content', content_type='application/pdf')
        doc = Document.objects.create(
            user=user,
            title='Professional CV',
            doc_type='cv',
            file=fake_file
        )
        assert 'Professional CV' in str(doc)


@pytest.mark.django_db
class TestCoverLetterTemplate:
    """Tests for the CoverLetterTemplate model."""

    def test_create_template(self):
        user = UserFactory()
        template = CoverLetterTemplate.objects.create(
            user=user,
            name='Standard Cover Letter',
            content='Dear Hiring Manager at {company_name}, I am applying for {job_title}.',
            is_default=True
        )
        assert template.pk is not None
        assert template.is_default is True

    def test_template_render(self):
        user = UserFactory()
        template = CoverLetterTemplate.objects.create(
            user=user,
            name='Test Template',
            content='Dear {company_name}, I want to be your {job_title}. Regards, {your_name}.'
        )
        rendered = template.render({
            'company_name': 'Takealot',
            'job_title': 'Python Developer',
            'your_name': 'Nomsa Dlamini',
        })
        assert 'Takealot' in rendered
        assert 'Python Developer' in rendered
        assert 'Nomsa Dlamini' in rendered

    def test_template_str(self):
        user = UserFactory()
        template = CoverLetterTemplate.objects.create(
            user=user,
            name='My Template',
            content='Some content here'
        )
        assert str(template) == 'My Template'


@pytest.mark.django_db
class TestDocumentViews:
    """Tests for document related views."""

    def test_document_list_requires_login(self):
        client = Client()
        response = client.get(reverse('document-list'))
        assert response.status_code == 302

    def test_document_list_loads(self):
        user = UserFactory()
        client = Client()
        client.login(username=user.username, password='testpass123')
        response = client.get(reverse('document-list'))
        assert response.status_code == 200

    def test_document_upload_page_loads(self):
        user = UserFactory()
        client = Client()
        client.login(username=user.username, password='testpass123')
        response = client.get(reverse('document-upload'))
        assert response.status_code == 200

    def test_template_list_loads(self):
        user = UserFactory()
        client = Client()
        client.login(username=user.username, password='testpass123')
        response = client.get(reverse('template-list'))
        assert response.status_code == 200

    def test_template_create_loads(self):
        user = UserFactory()
        client = Client()
        client.login(username=user.username, password='testpass123')
        response = client.get(reverse('template-create'))
        assert response.status_code == 200
