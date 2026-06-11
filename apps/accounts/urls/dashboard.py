"""
Admin dashboard URLs — /dashboard/
"""

from django.urls import path
from apps.accounts import views

urlpatterns = [
    path('', views.AdminDashboardView.as_view(), name='dashboard'),
    path('profile/', views.ProfileView.as_view(), name='staff_profile'),
    path('staff/', views.StaffListView.as_view(), name='staff_list'),
    path('staff/add/', views.StaffCreateView.as_view(), name='staff_create'),
]
