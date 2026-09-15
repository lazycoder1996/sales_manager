from django.urls import path

from apps.inventory.views import (
    ProductActivateView,
    ProductDeactivateView,
    ProductDetailView,
    ProductListCreateView,
    ProductVariantActivateView,
    ProductVariantDeactivateView,
    ProductVariantDetailView,
    ProductVariantListCreateView,
    StockReceiptDetailView,
    StockReceiptListCreateView,
    StockBalanceView,
    PaymentListCreateView,
    PaymentDetailView,
    SaleListCreateView,
    SaleDetailView,
    SaleLineCreateView,
    SaleLineDetailView,
    SaleDeliveryView,
    StudentHistoryView,
    StockDetailView,
    SellerListCreateView,
    SellerDetailView,
    SellerPaymentListCreateView,
    SellerPaymentDetailView,
    DashboardView,
    CompleteSaleView,
    AdditionalPurchaseCreateView,
    TodaysSalesView,
)


urlpatterns = [
    # Dashboard
    path(
        "dashboard/",
        DashboardView.as_view(),
        name="dashboard",
    ),
    path(
        "dashboard/todays-sales/",
        TodaysSalesView.as_view(),
        name="dashboard-todays-sales",
    ),

    # Sellers
    path(
        "sellers/",
        SellerListCreateView.as_view(),
        name="seller-list-create",
    ),
    path(
        "sellers/<uuid:seller_id>/",
        SellerDetailView.as_view(),
        name="seller-detail",
    ),
    path(
        "seller-payments/",
        SellerPaymentListCreateView.as_view(),
        name="seller-payment-list-create",
    ),

    path(
        "seller-payments/<uuid:payment_id>/",
        SellerPaymentDetailView.as_view(),
        name="seller-payment-detail",
    ),
    # Products
    path(
        "products/",
        ProductListCreateView.as_view(),
        name="product-list-create",
    ),
    path(
        "products/<uuid:product_id>/",
        ProductDetailView.as_view(),
        name="product-detail",
    ),
    path(
        "products/<uuid:product_id>/activate/",
        ProductActivateView.as_view(),
        name="product-activate",
    ),
    path(
        "products/<uuid:product_id>/deactivate/",
        ProductDeactivateView.as_view(),
        name="product-deactivate",
    ),
    path(
        "products/<uuid:product_id>/variants/",
        ProductVariantListCreateView.as_view(),
        name="product-variant-list-create",
    ),
    path(
        "products/<uuid:product_id>/variants/<uuid:variant_id>/",
        ProductVariantDetailView.as_view(),
        name="product-variant-detail",
    ),
    path(
        "products/<uuid:product_id>/variants/<uuid:variant_id>/activate/",
        ProductVariantActivateView.as_view(),
        name="product-variant-activate",
    ),
    path(
        "products/<uuid:product_id>/variants/<uuid:variant_id>/deactivate/",
        ProductVariantDeactivateView.as_view(),
        name="product-variant-deactivate",
    ),

    # Stock
    path(
        "stock-receipts/",
        StockReceiptListCreateView.as_view(),
        name="stock-receipt-list-create",
    ),
    path(
        "stock-receipts/<uuid:receipt_id>/",
        StockReceiptDetailView.as_view(),
        name="stock-receipt-detail",
    ),
    path(
        "stock-balance/",
        StockBalanceView.as_view(),
        name="stock-balance",
    ),
    path(
        "stock-detail/",
        StockDetailView.as_view(),
        name="stock-detail",
    ),

    # Sales
    path(
        "sales/",
        SaleListCreateView.as_view(),
        name="sale-list-create",
    ),
    path(
        "sales/<uuid:sale_id>/",
        SaleDetailView.as_view(),
        name="sale-detail",
    ),
    path(
        "sales/complete/",
        CompleteSaleView.as_view(),
    ),
    path(
        "sales/<uuid:sale_id>/purchases/",
        AdditionalPurchaseCreateView.as_view(),
    ),

    # Sale lines
    path(
        "sales/<uuid:sale_id>/lines/",
        SaleLineCreateView.as_view(),
        name="sale-line-create",
    ),
    path(
        "sales/<uuid:sale_id>/lines/<uuid:line_id>/",
        SaleLineDetailView.as_view(),
        name="sale-line-detail",
    ),

    # Payments
    path(
        "payments/",
        PaymentListCreateView.as_view(),
        name="payment-list-create",
    ),
    path(
        "payments/<uuid:payment_id>/",
        PaymentDetailView.as_view(),
        name="payment-detail",
    ),

    # Delivery
    path(
        "sales/<uuid:sale_id>/deliver/",
        SaleDeliveryView.as_view(),
        name="sale-delivery",
    ),

    # History
    path(
    "student-history/",
        StudentHistoryView.as_view(),
        name="student-history",
    ),

]