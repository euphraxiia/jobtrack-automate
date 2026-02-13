#!/usr/bin/env python
"""Django management script for the JobTrack application."""
import os
import sys


def main() -> None:
    """Run admin commands for the project."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Could not import Django. Check that it is installed and "
            "available on your PYTHONPATH. Did you activate your virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
