"""
Customer account portal URLs — /account/
"""

from django.urls import path
from apps.accounts import views

urlpatterns = [
    path('', views.CustomerDashboardView.as_view(), name='customer_dashboard'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/password/', views.PasswordChangeView.as_view(), name='password_change'),
]
