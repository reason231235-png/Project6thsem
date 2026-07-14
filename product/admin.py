from django.contrib import admin

from product.models import Category, Product, Cart, Order, OrderItem, PaymentHistory


admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Cart)
admin.site.register(PaymentHistory)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0  # This prevents showing extra empty forms (set to 1 if you want 1 extra empty form)
    fields = (
        "product",
        "quantity",
        "price",
    )
    readonly_fields = (
        "product",
        "quantity",
        "price",
    )
    can_delete = False


class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "status",
        "total_price",
        "shipping_address",
        "created_at",
    )
    inlines = [OrderItemInline]


admin.site.register(Order, OrderAdmin)
