"""
Combined accounts URL namespace.
All four sub-modules share the 'accounts' app_name via this entry point.
"""

app_name = 'accounts'

from django.urls import path, include

urlpatterns = [
    path('auth/',      include('apps.accounts.urls.auth')),
    path('account/',   include('apps.accounts.urls.customer')),
    path('dashboard/', include('apps.accounts.urls.dashboard')),
]
