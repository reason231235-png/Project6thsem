from django.urls import path

from product.views import (
    ProductView,
    DetailProductView,
    CartView,
    UserCartView,
    CheckoutView,
    CreateOrderView,
    OrderView,
    DetailOrderView,
    PaymentView,
    PurchaseView,
)

app_name = "product"

urlpatterns = [
    path("", ProductView.as_view(), name="products"),
    path("<int:product_id>/", DetailProductView.as_view(), name="detail_product"),
    path(
        "add-remove-from-cart/<int:product_id>/",
        CartView.as_view(),
        name="add_remove_from_cart",
    ),
    path(
        "user-cart/",
        UserCartView.as_view(),
        name="user_cart",
    ),
    path(
        "checkout/",
        CheckoutView.as_view(),
        name="checkout",
    ),
    path("create-order/", CreateOrderView.as_view(), name="create_order"),
    path("orders/", OrderView.as_view(), name="orders"),
    path("order/<int:order_id>/", DetailOrderView.as_view(), name="order_detail"),
    path(
        "payment/<int:order_id>/",
        PaymentView.as_view(),
        name="payment",
    ),
    path("purchase/", PurchaseView.as_view(), name="purchase"),
]
