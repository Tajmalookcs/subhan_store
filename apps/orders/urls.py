from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Customer
    path('checkout/', views.checkout, name='checkout'),
    path('my-orders/', views.order_list, name='order_list'),
    path('my-orders/<str:order_number>/', views.order_detail, name='order_detail'),
    path('my-orders/<str:order_number>/cancel/', views.order_cancel, name='order_cancel'),
    path('my-orders/<str:order_number>/invoice/', views.invoice, name='invoice'),

    # Admin / Staff
    path('dashboard/orders/', views.admin_order_list, name='admin_order_list'),
    path('dashboard/orders/<str:order_number>/', views.admin_order_detail, name='admin_order_detail'),
]
