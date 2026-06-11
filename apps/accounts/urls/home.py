"""
Root URL — redirects to login or dashboard.
"""

from django.urls import path
from apps.accounts.views import HomeRedirectView

urlpatterns = [
    path('', HomeRedirectView.as_view(), name='home'),
]
