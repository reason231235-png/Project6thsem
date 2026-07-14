from celery import shared_task
from django.core.mail import send_mail
from django.utils.timezone import now
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.conf import settings

from auction.models import Auction
from product.models import Cart


def send_winner_email(user, auction, bid_amount):
    """Send an email notification to the winner of the auction."""
    subject = "🎉 Congratulations! You won the auction!"
    message = (
        f"Dear {user.username},\n\n"
        f"Congratulations! You won the auction for '{auction.product.title}' "
        f"with a winning bid of Rs. {bid_amount}.\n\n"
        f"Please proceed with the payment and check your cart for details.\n\n"
        f"Thank you for participating!\n\n"
        f"Best regards,\nCozy Clothings"
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,  # Set to True if you don't want errors to crash Celery
    )


def add_product_to_cart(user, product):
    """Add the auctioned product to the winner's cart."""
    cart_item, created = Cart.objects.get_or_create(
        user=user,
        product=product,
        defaults={"quantity": 1},  # Default quantity set to 1
    )

    if not created:
        cart_item.quantity += (
            1  # If the product already exists in the cart, increase the quantity
        )
        cart_item.save()


@shared_task
def end_auction():
    auctions = Auction.objects.filter(end_time__lte=now(), winner__isnull=True)

    for auction in auctions:
        highest_bid = auction.bids.order_by("-amount", "timestamp").first()
        if highest_bid:
            auction.winner = highest_bid.user
            auction.current_price = highest_bid.amount
        auction.save()

        # Add auction product to the winner's cart
        add_product_to_cart(highest_bid.user, auction.product)

        # Send email notification to the winner
        send_winner_email(highest_bid.user, auction, highest_bid.amount)

        # Notify users via WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"auction_{auction.id}",
            {
                "type": "end_auction",
                "message": {
                    "winner": highest_bid.user.username if highest_bid else None,
                    "winning_bid": (
                        str(highest_bid.amount) if highest_bid else "No bids"
                    ),
                },
            },
        )
