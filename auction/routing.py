from django.urls import path
from .consumers import AuctionConsumer

auction_websocket_urlpatterns = [
    path("ws/auction/<int:auction_id>/", AuctionConsumer.as_asgi()),
]
