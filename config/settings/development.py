"""
Development settings for Subhan Super Store.
"""

from .base import *  # noqa

DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# Show emails in console during development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Django Debug Toolbar (optional — install separately)
# INSTALLED_APPS += ['debug_toolbar']
