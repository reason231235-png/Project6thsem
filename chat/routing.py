from django.urls import path
from chat import consumers

chat_websocket_urlpatterns = [
    path("ws/auction/<int:auction_id>/chat/", consumers.ChatConsumer.as_asgi()),
]
