from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task
def send_order_placement_email_task(user_email, username, order_id, total_amount):
    """Celery task to send an order placement email."""
    subject = "🛒 Order Confirmation - Cozy Clothings"
    message = (
        f"Dear {username},\n\n"
        f"Thank you for your order! Your order (Order ID: {order_id}) has been placed successfully.\n\n"
        f"Order Details:\n"
        f"Total Amount: Rs. {total_amount}\n"
        f"You can track your order status in your account.\n\n"
        f"Best regards,\nCozy Clothings"
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user_email],
        fail_silently=True,
    )


@shared_task
def send_payment_confirmation_email_task(
    user_email, username, order_id, total_amount, payment_method, transaction_id
):
    """Celery task to send a payment confirmation email."""
    subject = "✅ Payment Successful - Cozy Clothings"
    message = (
        f"Dear {username},\n\n"
        f"We have received your payment for Order ID: {order_id}.\n\n"
        f"Payment Details:\n"
        f"Amount Paid: Rs. {total_amount}\n"
        f"Payment Method: {payment_method}\n"
        f"Transaction ID: {transaction_id}\n\n"
        f"Your order is now being processed. You will receive another update once it is shipped.\n\n"
        f"Best regards,\nCozy Clothings"
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user_email],
        fail_silently=True,
    )
