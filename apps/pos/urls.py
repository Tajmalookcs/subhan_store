from django.urls import path
from . import views

app_name = 'pos'

urlpatterns = [
    path('pos/', views.pos_redirect, name='redirect'),
    path('pos/screen/', views.pos_screen, name='screen'),
    path('pos/session/open/', views.session_open, name='session_open'),
    path('pos/session/close/', views.session_close, name='session_close'),
    path('pos/session/', views.session_list, name='session_list'),
    path('pos/session/<int:pk>/', views.session_detail, name='session_detail'),
    path('pos/receipt/<str:sale_number>/', views.receipt, name='receipt'),
    path('pos/void/<str:sale_number>/', views.sale_void, name='sale_void'),

    # AJAX
    path('pos/api/search/', views.product_search, name='product_search'),
    path('pos/api/process/', views.process_sale, name='process_sale'),
]
