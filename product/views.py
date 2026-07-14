import requests
import json
import uuid
import hmac
import hashlib
import base64

from django.shortcuts import render, redirect
from django.views import View
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.conf import settings
from django.utils import timezone

from product.models import Product, Category, Cart, Order, OrderItem, PaymentHistory
from product.forms import PaymentForm
from product.tasks import (
    send_order_placement_email_task,
    send_payment_confirmation_email_task,
)


class ProductView(View):
    template_name = "product/products.html"

    def get(self, request):
        products = Product.objects.filter(is_active=True, is_auction_product=False)
        categories = Category.objects.all()

        query = request.GET.get("query", "")
        category_id = request.GET.get("category", 0)

        if category_id:
            products = products.filter(category_id=category_id)

        if query:
            products = products.filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(category__title__icontains=query)
            ).filter(is_active=True, is_auction_product=False)

        return render(
            request,
            self.template_name,
            {
                "products": products,
                "categories": categories,
                "query": query,
                "category_id": int(category_id),
            },
        )


class DetailProductView(View):
    template_name = "product/detail_product.html"

    def get(self, request, *args, **kwargs):
        product_id = kwargs.get("product_id")
        product = get_object_or_404(Product, id=product_id)
        related_products = Product.objects.filter(category=product.category).exclude(
            id=product_id
        )[:3]

        return render(
            request,
            self.template_name,
            {
                "product": product,
                "related_products": related_products,
            },
        )


class CartView(View):
    def post(self, request, *args, **kwargs):
        product_id = kwargs.get("product_id")
        quantity = int(request.POST.get("quantity", 1))

        product = get_object_or_404(Product, id=product_id)

        # Check if the quantity requested is valid
        if quantity > product.quantity:
            return JsonResponse(
                {
                    "success": False,
                    "error": f"Only {product.quantity} more units available.",
                },
                status=400,
            )

        cart_item, created = Cart.objects.get_or_create(
            user=request.user, product=product
        )

        cart_item.quantity = quantity
        cart_item.save()

        return JsonResponse(
            {
                "message": "Product added to cart successfully",
                "product_title": product.title,
                "quantity": cart_item.quantity,
                "total_price": cart_item.total_price(),
            }
        )

    def delete(self, request, *args, **kwargs):
        product_id = kwargs.get("product_id")
        product = get_object_or_404(Product, id=product_id)

        # Try to find the cart item for this product
        cart_item = Cart.objects.filter(user=request.user, product=product).first()

        if cart_item:
            cart_item.delete()
            return JsonResponse(
                {"success": True, "message": "Product removed from cart successfully."},
                status=200,
            )

        return JsonResponse(
            {"error": "Product not found in cart."},
            status=400,
        )


class UserCartView(View):
    template_name = "product/cart.html"

    def get(self, request, *args, **kwargs):
        cart_items = Cart.objects.filter(user=request.user)

        # Calculate the total price of the items in the cart
        total_price = sum(item.total_price() for item in cart_items)

        return render(
            request,
            self.template_name,
            {"cart_items": cart_items, "total_price": total_price},
        )


class CheckoutView(View):
    template_name = "product/checkout.html"

    def get_cart_items(self, user):
        # Fetch the user's cart items (adjust this to your actual data retrieval logic)
        user_cart_items = Cart.objects.filter(user=user)
        return [
            {
                "product": item.product.title,
                "is_auction_product": item.product.is_auction_product,
                "quantity": item.quantity,
                "price": item.product.sale_price,
                "total_price": item.total_price(),
            }
            for item in user_cart_items
        ]

    def get(self, request, *args, **kwargs):
        user_cart_items = self.get_cart_items(request.user)
        total_price = sum(item.get("total_price") for item in user_cart_items)

        return render(
            request,
            self.template_name,
            {
                "cart_items": user_cart_items,
                "total_price": total_price,
            },
        )


class CreateOrderView(View):
    template_name = "product/orders.html"

    def get(self, request, *args, **kwargs):
        cart_items = Cart.objects.filter(user=request.user)

        total_price = sum(item.total_price() for item in cart_items)

        order = Order.objects.create(
            user=request.user,
            total_price=total_price,
            status="Pending",
        )

        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.sale_price,
            )

        cart_items.delete()  # Clear the cart after creating the order
        send_order_placement_email_task.delay(
            user_email=request.user.email,
            username=request.user.username,
            order_id=order.id,
            total_amount=order.total_price,
        )

        return redirect("product:order_detail", order_id=order.id)


class OrderView(View):
    template_name = "product/orders.html"

    def get(self, request, *args, **kwargs):
        orders = Order.objects.filter(user=request.user)

        return render(request, self.template_name, {"orders": orders})


class DetailOrderView(View):
    template_name = "product/detail_order.html"

    def get(self, request, *args, **kwargs):
        order_id = kwargs.get("order_id")
        order = get_object_or_404(Order, id=order_id, user=request.user)
        order_items = order.items.all()

        # Fetch the latest ended auction for auctioned products
        for item in order_items:
            if item.product.is_auction_product:
                auction = (
                    item.product.auction.filter(end_time__lte=timezone.now())
                    .order_by("-end_time")
                    .first()
                )
                item.auction_price = (
                    auction.current_price if auction else 0
                )  # Attach dynamic price

        return render(
            request, self.template_name, {"order": order, "order_items": order_items}
        )


class PaymentView(View):
    template_name = "product/payment.html"
    form_class = PaymentForm

    def get(self, request, *args, **kwargs):
        order_id = kwargs.get("order_id")

        order = get_object_or_404(Order, id=order_id, user=request.user)
        total_price = order.total_price

        form = self.form_class()

        return render(
            request,
            self.template_name,
            {
                "order": order,
                "total_price": total_price,
                "form": form,
            },
        )

    def post(self, request, *args, **kwargs):
        user = request.user
        order_id = kwargs.get("order_id")
        form = self.form_class(request.POST)

        order = get_object_or_404(Order, id=order_id, user=request.user)

        if form.is_valid():
            address = form.cleaned_data.get("shipping_address")
            payment_method = form.cleaned_data.get("payment_method").lower()

            total_price, product_details = self._process_order_details(
                order, user, payment_method, address
            )
            if payment_method == "esewa":
                return self._handle_esewa_payment(request, order, total_price)
            elif payment_method == "khalti":
                payment_url = self._handle_khalti_payment(
                    order, total_price, product_details
                )
                return redirect(payment_url)
        else:
            return render(
                request,
                self.template_name,
                {
                    "order": order,
                    "total_price": order.total_price,
                    "form": form,
                },
            )

    # custom methods to handle payments
    def _process_order_details(self, order, user, payment, shipping_address):
        total_amount = 0
        product_details = []

        order.shipping_address = shipping_address
        order.save()

        order_items = OrderItem.objects.filter(order=order)

        for order_item in order_items:
            product = order_item.product
            quantity = order_item.quantity

            if quantity > product.quantity:
                raise ValueError(f"Insufficient stock for {product.title}")

            # Determine the correct price
            if product.is_auction_product:
                # Fetch the latest auction price
                auction = (
                    product.auction.filter(end_time__lte=timezone.now())
                    .order_by("-end_time")
                    .first()
                )
                unit_price = float(auction.current_price) if auction else 0
            else:
                # Use the sale price for regular products
                unit_price = float(product.sale_price)

            item_total = unit_price * quantity
            total_amount += item_total

            product_details.append(
                {
                    "identity": str(product.id),
                    "name": product.title,
                    "total_price": item_total,
                    "quantity": quantity,
                    "unit_price": float(product.price) * 100,
                }
            )

        PaymentHistory.objects.create(
            buyer=user,
            amount=item_total,
            order=order,
            transaction_status="INITIATE",
            transaction_type=payment.upper(),
        )

        return total_amount, product_details

    def _handle_khalti_payment(self, order, total_price, product_details):
        total_price = float(total_price) * 100  # convert to paisa

        payment_data = {
            "return_url": settings.TRANSACTION_REDIRECT_URL,
            "website_url": settings.WEBSITE_URL,
            "amount": total_price,
            "purchase_order_id": order.id,
            "purchase_order_name": f"Order #{order.id}",
            "customer_info": {
                "name": settings.KHALTI_CUSTOMER_NAME,
                "email": settings.KHALTI_CUSTOMER_EMAIL,
                "phone": settings.KHALTI_CUSTOMER_PHONE,
            },
            "amount_breakdown": [
                {"label": "Mark Price", "amount": total_price},
                {"label": "VAT", "amount": 0},
            ],
            "product_details": product_details,
            "merchant_username": settings.KHALTI_MERCHANT_USERNAME,
            "merchant_extra": "merchant_extra",
        }

        headers = {
            "Authorization": settings.KHALTI_AUTH,
            "Content-Type": "application/json",
        }

        response = requests.post(
            settings.KHALTI_URL, headers=headers, data=json.dumps(payment_data)
        )

        data = response.json()

        if response.status_code != 200:
            return "product:orders"

        PaymentHistory.objects.filter(order=order).update(
            transaction_response=data, transaction_id=data["pidx"]
        )

        return data.get("payment_url")

    def _generate_esewa_signature(self, fields_dict, signed_field_names, secret_key):
        fields_to_sign = signed_field_names.split(",")
        values = []
        for field in fields_to_sign:
            value = fields_dict[field]
            values.append(f"{field}={value}")

        input_string = ",".join(values)
        signature = hmac.new(
            secret_key.encode("utf-8"), input_string.encode("utf-8"), hashlib.sha256
        )
        return base64.b64encode(signature.digest()).decode("utf-8")

    def _handle_esewa_payment(self, request, order, total_price):
        transaction_uuid = str(uuid.uuid4())

        esewa_fields = {
            "amount": str(total_price),
            "tax_amount": "0",
            "total_amount": str(total_price),
            "transaction_uuid": transaction_uuid,
            "product_code": "EPAYTEST",
            "product_service_charge": "0",
            "product_delivery_charge": "0",
            "success_url": f"{settings.TRANSACTION_REDIRECT_URL}",
            "failure_url": f"{settings.WEBSITE_URL}",
            "signed_field_names": "total_amount,transaction_uuid,product_code",
        }

        signature = self._generate_esewa_signature(
            esewa_fields, esewa_fields["signed_field_names"], settings.ESEWA_SECRET_KEY
        )

        esewa_fields["signature"] = signature

        PaymentHistory.objects.filter(order=order).update(
            transaction_id=transaction_uuid
        )

        return render(
            request, "product/esewa_checkout.html", {"esewa_fields": esewa_fields}
        )


class PurchaseView(View):
    template_name = "product/products.html"

    def get(self, request, *args, **kwargs):
        pidx = request.GET.get("pidx", "")
        data = request.GET.get("data", "")
        if pidx:
            status = request.GET.get("status", "")
            if status != "Completed":
                return render(request, self.template_name)

            response = self._handle_khalti_lookup(pidx)
            if not response.status_code == 200:
                return render(request, self.template_name)
            lookup_data = response.json()

            if lookup_data["status"] != "Completed":
                return render(request, self.template_name)

            self._handle_completed_payment(lookup_data["pidx"], request.user, response)
            return render(request, self.template_name)

        elif data:
            decoded_data = base64.b64decode(data).decode("utf-8")
            data = json.loads(decoded_data)

            if data["status"] != "COMPLETE":
                return render(request, self.template_name)

            response = self._handle_esewa_lookup(
                data["product_code"], data["total_amount"], data["transaction_uuid"]
            )
            if not response.status_code == 200:
                return render(request, self.template_name)
            lookup_data = response.json()

            if lookup_data["status"] != "COMPLETE":
                return render(request, self.template_name)

            self._handle_completed_payment(
                lookup_data["transaction_uuid"], request.user, response
            )
            return render(request, self.template_name)

    def _handle_completed_payment(self, transaction_id, user, response):
        payment = PaymentHistory.objects.filter(transaction_id=transaction_id).first()
        order = payment.order

        order_items = OrderItem.objects.filter(order=order)
        for order_item in order_items.all():
            product = order_item.product
            quantity = order_item.quantity

            product.quantity -= quantity
            product.save()

        order.status = "Paid"
        order.payment_method = payment.transaction_type
        order.save()

        payments = PaymentHistory.objects.filter(transaction_id=transaction_id)
        for payment in payments:
            payment.transaction_status = "COMPLETE"
            payment.transaction_response = response.json()
            payment.save()

        send_payment_confirmation_email_task.delay(
            user_email=user.email,
            username=user.username,
            order_id=order.id,
            total_amount=order.total_price,
            payment_method=payments[0].transaction_type,
            transaction_id=transaction_id,
        )

    def _handle_khalti_lookup(self, pidx):
        url = settings.KHALTI_LOOKUP_URL
        payload = json.dumps({"pidx": pidx})
        headers = {
            "Authorization": settings.KHALTI_AUTH,
            "Content-Type": "application/json",
        }
        return requests.post(url, headers=headers, data=payload)

    def _handle_esewa_lookup(self, product_code, total_amount, transaction_uuid):
        url = f"{settings.ESEWA_LOOKUP_URL}?product_code={product_code}&total_amount={total_amount.replace(',', '')}&transaction_uuid={transaction_uuid}"
        return requests.get(url)
