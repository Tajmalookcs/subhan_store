"""
Inventory Management models for Subhan Super Store.
Tracks warehouses, stock movements, and product expiry records.
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone

from apps.products.models import Product


class Warehouse(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200, blank=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_default', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Ensure only one default warehouse
        if self.is_default:
            Warehouse.objects.exclude(pk=self.pk).filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_default(cls):
        return cls.objects.filter(is_default=True).first() or cls.objects.first()


class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ('purchase', 'Purchase In'),
        ('sale', 'Sale Out'),
        ('adjustment_in', 'Manual Adjustment — Add'),
        ('adjustment_out', 'Manual Adjustment — Remove'),
    ]

    STOCK_IN_TYPES = {'purchase', 'adjustment_in'}
    STOCK_OUT_TYPES = {'sale', 'adjustment_out'}

    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name='stock_movements',
    )
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.PROTECT, related_name='movements',
    )
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    reference = models.CharField(max_length=100, blank=True, help_text='PO number, invoice, etc.')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='stock_movements',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        direction = '+' if self.movement_type in self.STOCK_IN_TYPES else '-'
        return f'{self.product.name} {direction}{self.quantity} ({self.get_movement_type_display()})'

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self._apply_stock_change()

    def _apply_stock_change(self):
        if self.movement_type in self.STOCK_IN_TYPES:
            Product.objects.filter(pk=self.product_id).update(
                stock_quantity=models.F('stock_quantity') + self.quantity
            )
        else:
            Product.objects.filter(pk=self.product_id).update(
                stock_quantity=models.F('stock_quantity') - self.quantity
            )

    @property
    def is_stock_in(self):
        return self.movement_type in self.STOCK_IN_TYPES


class ExpiryRecord(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name='expiry_records',
    )
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.PROTECT, related_name='expiry_records',
    )
    batch_number = models.CharField(max_length=100, blank=True)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    expiry_date = models.DateField()
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='expiry_records',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['expiry_date']

    def __str__(self):
        return f'{self.product.name} — expires {self.expiry_date}'

    @property
    def is_expired(self):
        return self.expiry_date < timezone.now().date()

    @property
    def days_until_expiry(self):
        return (self.expiry_date - timezone.now().date()).days

    @property
    def status(self):
        days = self.days_until_expiry
        if days < 0:
            return 'expired'
        if days <= 7:
            return 'critical'
        if days <= 30:
            return 'warning'
        return 'ok'
