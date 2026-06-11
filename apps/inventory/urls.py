from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Dashboard
    path('', views.InventoryDashboardView.as_view(), name='dashboard'),

    # Stock movements
    path('movements/', views.StockMovementListView.as_view(), name='movement_list'),
    path('movements/receive/', views.PurchaseInCreateView.as_view(), name='stock_in'),
    path('movements/adjust/', views.ManualAdjustmentCreateView.as_view(), name='adjustment'),

    # Low stock
    path('low-stock/', views.LowStockListView.as_view(), name='low_stock'),

    # Expiry records
    path('expiry/', views.ExpiryRecordListView.as_view(), name='expiry_list'),
    path('expiry/add/', views.ExpiryRecordCreateView.as_view(), name='expiry_create'),
    path('expiry/<int:pk>/edit/', views.ExpiryRecordUpdateView.as_view(), name='expiry_update'),
    path('expiry/<int:pk>/delete/', views.ExpiryRecordDeleteView.as_view(), name='expiry_delete'),
]
