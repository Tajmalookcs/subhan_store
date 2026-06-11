import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.products.models import Product


def generate_sale_number():
    return 'POS-' + uuid.uuid4().hex[:8].upper()


class POSSession(models.Model):
    STATUS_CHOICES = [('open', 'Open'), ('closed', 'Closed')]

    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='pos_sessions',
    )
    opening_cash = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    closing_cash = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open', db_index=True)
    notes = models.TextField(blank=True)
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-opened_at']

    def __str__(self):
        return f'Session #{self.pk} — {self.cashier.username} ({self.status})'

    @property
    def total_sales(self):
        return self.sales.filter(is_void=False).count()

    @property
    def total_revenue(self):
        from django.db.models import Sum
        return self.sales.filter(is_void=False).aggregate(
            t=Sum('total_amount')
        )['t'] or 0

    @property
    def duration(self):
        end = self.closed_at or timezone.now()
        delta = end - self.opened_at
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes = remainder // 60
        return f'{hours}h {minutes}m'


class POSSale(models.Model):
    PAYMENT_CHOICES = [
        ('cash', 'Cash'),
        ('jazzcash', 'JazzCash'),
        ('easypaisa', 'EasyPaisa'),
        ('card', 'Card'),
    ]

    sale_number = models.CharField(max_length=20, unique=True, default=generate_sale_number, db_index=True)
    session = models.ForeignKey(POSSession, on_delete=models.PROTECT, related_name='sales')
    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='pos_sales',
    )
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cash')
    amount_tendered = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    change_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    customer_name = models.CharField(max_length=200, blank=True)
    notes = models.CharField(max_length=300, blank=True)
    is_void = models.BooleanField(default=False, db_index=True)
    voided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='voided_sales',
    )
    voided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.sale_number} — Rs.{self.total_amount}'


class POSSaleItem(models.Model):
    sale = models.ForeignKey(POSSale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    product_name = models.CharField(max_length=200)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.quantity}x {self.product_name}'
