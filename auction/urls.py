from django.urls import path
from .views import AuctionDetailView, AuctionView

app_name = "auction"

urlpatterns = [
    path("", AuctionView.as_view(), name="auctions"),
    path("<int:auction_id>/", AuctionDetailView.as_view(), name="auction_detail"),
]
