from django.db import models
from django.utils.text import slugify
from django.utils.timezone import now
from django.contrib.auth.models import User

from cozy_clothings.enums import TransactionStatus, TransactionType


class Category(models.Model):
    title = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    created_at = models.DateTimeField(default=now, editable=False)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["title"]


class Product(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField()
    quantity = models.PositiveIntegerField()
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="products"
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = models.PositiveIntegerField(
        blank=True, null=True, default=0, help_text="Enter discount percentage (0-100)."
    )
    sale_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        editable=False,
        blank=True,
        null=True,
        help_text="Automatically calculated based on discount.",
    )
    image = models.ImageField(
        upload_to="product_images/",
        blank=True,
        null=True,
        default="product_images/default.jpg",
    )
    created_at = models.DateTimeField(default=now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_auction_product = models.BooleanField(
        default=False, help_text="Check if this product is for auction."
    )

    def __str__(self):
        return self.title

    def in_cart_of(self, user):
        return self.cart_items.filter(user=user).exists()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        # Calculate sale price if there's a discount
        if self.discount_percentage and 0 < self.discount_percentage <= 100:
            self.sale_price = self.price - (self.price * self.discount_percentage / 100)
        else:
            self.sale_price = self.price  # No discount

        super().save(*args, **kwargs)

    class Meta:
        ordering = ["-created_at"]


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="carts")
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="cart_items"
    )
    quantity = models.PositiveIntegerField(default=1)
    is_auctioned = models.BooleanField(
        default=False
    )  # Field to mark auctioned products

    def total_price(self):
        if self.is_auctioned:
            auction = (
                self.product.auction.filter(end_time__lte=now())
                .order_by("-end_time")
                .first()
            )
            return (
                auction.current_price if auction else 0
            )  # Get dynamic price from auction
        return self.product.sale_price * self.quantity

    class Meta:
        unique_together = (
            "user",
            "product",
        )
        ordering = ["-id"]

    def __str__(self):
        status = "Auctioned" if self.is_auctioned else "Regular"
        return f"{self.quantity} {self.product.title} ({self.product.id}) - {self.user.username} [{status}]"


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=[
            ("Pending", "Pending"),
            ("Paid", "Paid"),
            ("Shipped", "Shipped"),
            ("Delivered", "Delivered"),
        ],
        default="Pending",
    )
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_address = models.TextField(blank=True, null=True)
    payment_method = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def total_price(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.title}"


class PaymentHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payment")
    buyer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="buyer_payment_histories"
    )
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    transaction_id = models.TextField()
    transaction_response = models.JSONField(null=True)
    transaction_status = models.CharField(
        choices=TransactionStatus.choices, max_length=20
    )
    transaction_type = models.CharField(choices=TransactionType.choices, max_length=20)
    created_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"#{self.order.id} {self.transaction_type} ({self.transaction_status}) {self.buyer.id}"
