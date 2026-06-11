"""
Custom User Model for Subhan Super Store.
Extends AbstractUser with role-based access control.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Extended user model with role support.
    Replaces Django's default User model via AUTH_USER_MODEL setting.
    """

    ROLE_CHOICES = [
        ('superadmin', 'Super Admin'),
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('cashier', 'Cashier'),
        ('inventory_staff', 'Inventory Staff'),
        ('delivery_staff', 'Delivery Staff'),
        ('customer', 'Customer'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='customer',
        db_index=True,
    )
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True,
    )
    date_of_birth = models.DateField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.role})'

    # ── Role helper properties ──────────────────────────────────────────────

    @property
    def is_superadmin(self):
        return self.role == 'superadmin' or self.is_superuser

    @property
    def is_admin(self):
        return self.role in ('superadmin', 'admin') or self.is_superuser

    @property
    def is_manager(self):
        return self.role in ('superadmin', 'admin', 'manager') or self.is_superuser

    @property
    def is_cashier(self):
        return self.role in ('superadmin', 'admin', 'manager', 'cashier') or self.is_superuser

    @property
    def is_inventory_staff(self):
        return self.role in ('superadmin', 'admin', 'manager', 'inventory_staff') or self.is_superuser

    @property
    def is_delivery_staff(self):
        return self.role in ('superadmin', 'admin', 'manager', 'delivery_staff') or self.is_superuser

    @property
    def is_customer(self):
        return self.role == 'customer' and not self.is_superuser

    @property
    def is_staff_member(self):
        """True for any non-customer role, or Django superuser."""
        return self.role != 'customer' or self.is_superuser

    def get_dashboard_url(self):
        """Return the appropriate dashboard URL based on role."""
        if self.role == 'customer' and not self.is_superuser:
            return '/account/'
        return '/dashboard/'
