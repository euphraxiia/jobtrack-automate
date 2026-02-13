"""
CV parser utility.

Extracts information from uploaded CV files (PDF and DOCX).
Pulls out the relevant bits like name, email, phone number,
and skills so we can pre-fill forms.
"""
import logging
import re
from typing import Dict, Any, Optional

logger = logging.getLogger('applications')


class CVParser:
    """
    Parse CV documents and pull out useful information.
    Supports PDF and DOCX formats.
    """

    # Common patterns for finding contact details in a CV
    EMAIL_PATTERN = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+')
    PHONE_PATTERN = re.compile(r'(?:\+27|0)\s*\d{2}\s*\d{3}\s*\d{4}')
    LINKEDIN_PATTERN = re.compile(r'linkedin\.com/in/[\w-]+')

    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a CV file and return the extracted data.
        Works out the file type and uses the right parser.
        """
        if file_path.lower().endswith('.pdf'):
            text = self._extract_pdf_text(file_path)
        elif file_path.lower().endswith('.docx'):
            text = self._extract_docx_text(file_path)
        else:
            logger.warning('Unsupported file format: %s', file_path)
            return {}

        if not text:
            return {}

        return self._extract_info(text)

    @staticmethod
    def _extract_pdf_text(file_path: str) -> str:
        """Pull text out of a PDF file."""
        try:
            from PyPDF2 import PdfReader

            reader = PdfReader(file_path)
            text = ''
            for page in reader.pages:
                text += page.extract_text() or ''
            return text

        except Exception as e:
            logger.error('Failed to read PDF %s: %s', file_path, e)
            return ''

    @staticmethod
    def _extract_docx_text(file_path: str) -> str:
        """Pull text out of a DOCX file."""
        try:
            from docx import Document

            doc = Document(file_path)
            text = '\n'.join(paragraph.text for paragraph in doc.paragraphs)
            return text

        except Exception as e:
            logger.error('Failed to read DOCX %s: %s', file_path, e)
            return ''

    def _extract_info(self, text: str) -> Dict[str, Any]:
        """
        Extract structured information from the CV text.
        Looks for email addresses, phone numbers, and other details.
        """
        info = {
            'email': self._find_email(text),
            'phone': self._find_phone(text),
            'linkedin': self._find_linkedin(text),
            'raw_text': text[:5000],  # Keep the first chunk for reference
        }

        return {k: v for k, v in info.items() if v}

    def _find_email(self, text: str) -> Optional[str]:
        """Find the first email address in the text."""
        match = self.EMAIL_PATTERN.search(text)
        return match.group() if match else None

    def _find_phone(self, text: str) -> Optional[str]:
        """Find a South African phone number in the text."""
        match = self.PHONE_PATTERN.search(text)
        return match.group() if match else None

    def _find_linkedin(self, text: str) -> Optional[str]:
        """Find a LinkedIn profile URL in the text."""
        match = self.LINKEDIN_PATTERN.search(text)
        return match.group() if match else None
