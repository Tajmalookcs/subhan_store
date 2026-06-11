from django.contrib import admin
from .models import Warehouse, StockMovement, ExpiryRecord


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'is_default', 'is_active', 'created_at')
    list_filter = ('is_default', 'is_active')
    search_fields = ('name', 'location')


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('product', 'movement_type', 'quantity', 'warehouse', 'reference', 'created_by', 'created_at')
    list_filter = ('movement_type', 'warehouse', 'created_at')
    search_fields = ('product__name', 'product__sku', 'reference')
    readonly_fields = ('created_at',)
    raw_id_fields = ('product',)
    date_hierarchy = 'created_at'

    def has_change_permission(self, request, obj=None):
        # Movements are immutable after creation — stock is already adjusted
        return False


@admin.register(ExpiryRecord)
class ExpiryRecordAdmin(admin.ModelAdmin):
    list_display = ('product', 'batch_number', 'quantity', 'expiry_date', 'warehouse', 'created_at')
    list_filter = ('warehouse', 'expiry_date')
    search_fields = ('product__name', 'batch_number')
    date_hierarchy = 'expiry_date'
    raw_id_fields = ('product',)
