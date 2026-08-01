from django.urls import path
from . import views

urlpatterns = [
    # Settings
    path('settings/', views.get_shop_settings, name='shop-settings'),
    path('settings/update/', views.update_shop_settings, name='shop-settings-update'),

    # Dashboard & Reports
    path('dashboard/', views.dashboard_stats, name='shop-dashboard'),
    path('reports/sales/', views.sales_report, name='shop-sales-report'),

    # Products
    path('products/', views.list_products, name='product-list'),
    path('products/create/', views.create_product, name='product-create'),
    path('products/<uuid:product_id>/', views.product_detail, name='product-detail'),
    path('products/<uuid:product_id>/update/', views.update_product, name='product-update'),
    path('products/<uuid:product_id>/adjust-stock/', views.adjust_stock, name='product-adjust-stock'),

    # POS Sales
    path('sales/', views.list_sales, name='sale-list'),
    path('sales/new/', views.process_sale, name='sale-create'),
    path('sales/<uuid:sale_id>/', views.sale_detail, name='sale-detail'),
    path('sales/<uuid:sale_id>/void/', views.void_sale_view, name='sale-void'),

    # Stock Movements
    path('stock-movements/', views.list_stock_movements, name='stock-movements'),

    # Customers
    path('customers/', views.list_customers, name='customer-list'),
    path('customers/create/', views.create_customer, name='customer-create'),
    path('customers/<uuid:customer_id>/update/', views.update_customer, name='customer-update'),

    # Suppliers
    path('suppliers/', views.list_suppliers, name='supplier-list'),
    path('suppliers/create/', views.create_supplier, name='supplier-create'),

    # Purchase Orders
    path('purchase-orders/', views.list_purchase_orders, name='po-list'),
    path('purchase-orders/create/', views.create_purchase_order, name='po-create'),
    path('purchase-orders/<uuid:po_id>/receive/', views.receive_purchase_order, name='po-receive'),

    # Wholesale Orders
    path('orders/', views.list_orders, name='order-list'),
    path('orders/create/', views.create_order, name='order-create'),
    path('orders/<uuid:order_id>/status/', views.update_order_status, name='order-status'),
]
