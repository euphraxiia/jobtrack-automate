"""
Root conftest for pytest.
Sets environment variables before Django settings are loaded.
"""
import os

os.environ.setdefault('USE_SQLITE', '1')
os.environ.setdefault('RUNNING_TESTS', 'pytest')
