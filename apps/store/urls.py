from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    # Storefront home
    path('', views.home, name='home'),

    # Product listing & detail
    path('shop/', views.product_list, name='product_list'),
    path('shop/<slug:slug>/', views.product_detail, name='product_detail'),

    # Cart
    path('cart/', views.cart_detail, name='cart'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/update/<int:item_id>/', views.cart_update, name='cart_update'),
    path('cart/remove/<int:item_id>/', views.cart_remove, name='cart_remove'),

    # Wishlist
    path('wishlist/', views.wishlist_detail, name='wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.wishlist_toggle, name='wishlist_toggle'),

    # Checkout (order creation handled in Phase 6)
    path('checkout/', views.checkout, name='checkout'),
]
