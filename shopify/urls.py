from django.urls import path
from . import views

urlpatterns = [
    path('store/', views.store, name='store'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('get_products/', views.get_products, name='get_products'),
    path('get_orders/', views.get_orders, name='get_orders'),
]
