# PriceTracker/catalog/urls.py
from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('items/', views.item_list, name='item_list'),
    path('item/<int:item_id>/', views.item_detail, name='item_detail'),
    path('ajax/search-items/', views.ajax_search_items, name='ajax_search_items'),
    path('item/<int:item_id>/add_price/', views.add_price_entry, name='add_price_entry'),
    path('ajax/item/<int:item_id>/last-purchase-details/', views.ajax_get_last_purchase_details, name='ajax_get_last_purchase_details'),
]