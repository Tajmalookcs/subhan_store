"""
Root URL Configuration — Subhan Super Store
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django Admin
    path('django-admin/', admin.site.urls),

    # E-Commerce storefront — Phase 5 (must be first to own '/')
    path('', include('apps.store.urls')),

    # All accounts URLs (auth, customer portal, dashboard) — namespace: 'accounts'
    path('', include('apps.accounts.urls')),

    # Product & Catalog management (Phase 3) — namespace: 'products'
    path('dashboard/products/', include('apps.products.urls.admin')),

    # Inventory management (Phase 4) — namespace: 'inventory'
    path('dashboard/inventory/', include('apps.inventory.urls')),

    # Orders & Payments (Phase 6) — namespace: 'orders'
    path('', include('apps.orders.urls')),

    # Point of Sale (Phase 7) — namespace: 'pos'
    path('', include('apps.pos.urls')),

    # REST API — enabled per phase
    # path('api/v1/', include('config.api_urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
