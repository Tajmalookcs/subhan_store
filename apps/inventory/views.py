"""
Inventory Management views for Subhan Super Store.
"""

from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from apps.accounts.permissions import StaffRequiredMixin, ManagerRequiredMixin, AdminRequiredMixin
from apps.products.models import Product
from .models import StockMovement, ExpiryRecord, Warehouse
from .forms import StockMovementForm, ExpiryRecordForm


# ── Inventory Dashboard ───────────────────────────────────────────────────────

class InventoryDashboardView(StaffRequiredMixin, TemplateView):
    template_name = 'inventory/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.now().date()
        soon = today + timedelta(days=30)

        ctx['total_products'] = Product.objects.filter(is_active=True).count()
        ctx['low_stock_products'] = Product.objects.filter(
            is_active=True, stock_quantity__lte=10
        ).order_by('stock_quantity')[:10]
        ctx['low_stock_count'] = Product.objects.filter(
            is_active=True, stock_quantity__lte=10
        ).count()
        ctx['out_of_stock_count'] = Product.objects.filter(
            is_active=True, stock_quantity=0
        ).count()
        ctx['recent_movements'] = StockMovement.objects.select_related(
            'product', 'created_by'
        ).order_by('-created_at')[:10]
        ctx['expiring_soon'] = ExpiryRecord.objects.filter(
            expiry_date__gte=today, expiry_date__lte=soon
        ).select_related('product').order_by('expiry_date')[:10]
        ctx['expiring_soon_count'] = ExpiryRecord.objects.filter(
            expiry_date__gte=today, expiry_date__lte=soon
        ).count()
        ctx['expired_count'] = ExpiryRecord.objects.filter(expiry_date__lt=today).count()
        return ctx


# ── Stock Movements ───────────────────────────────────────────────────────────

class StockMovementListView(StaffRequiredMixin, ListView):
    model = StockMovement
    template_name = 'inventory/movement_list.html'
    context_object_name = 'movements'
    paginate_by = 25

    def get_queryset(self):
        qs = StockMovement.objects.select_related('product', 'warehouse', 'created_by')
        q = self.request.GET.get('q', '').strip()
        movement_type = self.request.GET.get('type', '')
        if q:
            qs = qs.filter(
                Q(product__name__icontains=q) |
                Q(reference__icontains=q) |
                Q(product__sku__icontains=q)
            )
        if movement_type:
            qs = qs.filter(movement_type=movement_type)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        ctx['selected_type'] = self.request.GET.get('type', '')
        ctx['movement_types'] = StockMovement.MOVEMENT_TYPES
        return ctx


class PurchaseInCreateView(ManagerRequiredMixin, SuccessMessageMixin, CreateView):
    """Add stock received from a supplier (Purchase In)."""
    model = StockMovement
    form_class = StockMovementForm
    template_name = 'inventory/movement_form.html'
    success_url = reverse_lazy('inventory:movement_list')
    success_message = 'Stock received successfully for "%(product)s".'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['movement_type_choices'] = [('purchase', 'Purchase In')]
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.movement_type = 'purchase'
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form_title'] = 'Receive Stock (Purchase In)'
        ctx['submit_label'] = 'Confirm Stock In'
        return ctx


class ManualAdjustmentCreateView(ManagerRequiredMixin, CreateView):
    """Manual stock adjustment — add or remove stock freely."""
    model = StockMovement
    form_class = StockMovementForm
    template_name = 'inventory/movement_form.html'
    success_url = reverse_lazy('inventory:movement_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['movement_type_choices'] = [
            ('adjustment_in', 'Manual Adjustment — Add'),
            ('adjustment_out', 'Manual Adjustment — Remove'),
        ]
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(
            self.request,
            f'Stock adjusted for "{form.instance.product.name}".'
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form_title'] = 'Manual Stock Adjustment'
        ctx['submit_label'] = 'Apply Adjustment'
        return ctx


class LowStockListView(StaffRequiredMixin, ListView):
    model = Product
    template_name = 'inventory/low_stock.html'
    context_object_name = 'products'
    paginate_by = 25

    def get_queryset(self):
        return Product.objects.filter(
            is_active=True, stock_quantity__lte=10
        ).select_related('category', 'brand').order_by('stock_quantity')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['out_of_stock_count'] = Product.objects.filter(
            is_active=True, stock_quantity=0
        ).count()
        return ctx


# ── Expiry Records ────────────────────────────────────────────────────────────

class ExpiryRecordListView(ManagerRequiredMixin, ListView):
    model = ExpiryRecord
    template_name = 'inventory/expiry_list.html'
    context_object_name = 'records'
    paginate_by = 25

    def get_queryset(self):
        qs = ExpiryRecord.objects.select_related('product', 'warehouse', 'created_by')
        status = self.request.GET.get('status', '')
        today = timezone.now().date()
        if status == 'expired':
            qs = qs.filter(expiry_date__lt=today)
        elif status == 'critical':
            qs = qs.filter(expiry_date__gte=today, expiry_date__lte=today + timedelta(days=7))
        elif status == 'warning':
            qs = qs.filter(expiry_date__gte=today, expiry_date__lte=today + timedelta(days=30))
        elif status == 'ok':
            qs = qs.filter(expiry_date__gt=today + timedelta(days=30))
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(product__name__icontains=q) |
                Q(batch_number__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['selected_status'] = self.request.GET.get('status', '')
        ctx['q'] = self.request.GET.get('q', '')
        return ctx


class ExpiryRecordCreateView(ManagerRequiredMixin, SuccessMessageMixin, CreateView):
    model = ExpiryRecord
    form_class = ExpiryRecordForm
    template_name = 'inventory/expiry_form.html'
    success_url = reverse_lazy('inventory:expiry_list')
    success_message = 'Expiry record added for "%(product)s".'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form_title'] = 'Add Expiry Record'
        return ctx


class ExpiryRecordUpdateView(ManagerRequiredMixin, SuccessMessageMixin, UpdateView):
    model = ExpiryRecord
    form_class = ExpiryRecordForm
    template_name = 'inventory/expiry_form.html'
    success_url = reverse_lazy('inventory:expiry_list')
    success_message = 'Expiry record updated.'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form_title'] = 'Edit Expiry Record'
        return ctx


class ExpiryRecordDeleteView(AdminRequiredMixin, DeleteView):
    model = ExpiryRecord
    template_name = 'inventory/confirm_delete.html'
    success_url = reverse_lazy('inventory:expiry_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['object_type'] = 'Expiry Record'
        ctx['cancel_url'] = reverse_lazy('inventory:expiry_list')
        return ctx

    def post(self, request, *args, **kwargs):
        messages.success(request, 'Expiry record deleted.')
        return super().post(request, *args, **kwargs)
