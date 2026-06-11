from django.contrib import admin
from .models import POSSession, POSSale, POSSaleItem


class POSSaleItemInline(admin.TabularInline):
    model = POSSaleItem
    extra = 0
    readonly_fields = ('line_total',)


@admin.register(POSSession)
class POSSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'cashier', 'status', 'opening_cash', 'total_sales', 'total_revenue', 'opened_at')
    list_filter = ('status', 'opened_at')
    readonly_fields = ('opened_at',)


@admin.register(POSSale)
class POSSaleAdmin(admin.ModelAdmin):
    list_display = ('sale_number', 'cashier', 'total_amount', 'payment_method', 'is_void', 'created_at')
    list_filter = ('payment_method', 'is_void', 'created_at')
    search_fields = ('sale_number', 'customer_name', 'cashier__username')
    readonly_fields = ('sale_number', 'created_at')
    inlines = [POSSaleItemInline]
