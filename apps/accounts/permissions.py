"""
Custom permission mixins for Subhan Super Store.
Used as mixins on class-based views to enforce role-based access.
"""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Allows access only to staff members (non-customer roles)."""

    def test_func(self):
        return self.request.user.is_staff_member

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have permission to access this page.')
        return redirect('accounts:customer_dashboard')


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Allows access only to admin and superadmin roles."""

    def test_func(self):
        return self.request.user.is_admin

    def handle_no_permission(self):
        messages.error(self.request, 'Admin access required.')
        return redirect('accounts:dashboard')


class ManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Allows access to manager, admin, and superadmin roles."""

    def test_func(self):
        return self.request.user.is_manager

    def handle_no_permission(self):
        messages.error(self.request, 'Manager access required.')
        return redirect('accounts:dashboard')


class CashierRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Allows access to cashier and above roles."""

    def test_func(self):
        return self.request.user.is_cashier

    def handle_no_permission(self):
        messages.error(self.request, 'Cashier access required.')
        return redirect('accounts:dashboard')


class SuperAdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Allows access only to superadmin."""

    def test_func(self):
        return self.request.user.is_superadmin

    def handle_no_permission(self):
        messages.error(self.request, 'Super Admin access required.')
        return redirect('accounts:dashboard')
