from django.views import View
from django.shortcuts import render, get_object_or_404
from django.utils import timezone

from auction.models import Auction


class AuctionView(View):
    template_name = "auction/auctions.html"

    def get(self, request, *args, **kwargs):
        auctions = Auction.objects.filter(end_time__gt=timezone.now())

        return render(request, self.template_name, {"auctions": auctions})


class AuctionDetailView(View):
    template_name = "auction/auction_detail.html"

    def get(self, request, *args, **kwargs):
        auction_id = kwargs.get("auction_id")

        auction = get_object_or_404(Auction, id=auction_id)
        bids = auction.bids.all()
        auction_status = "ongoing" if auction.end_time > timezone.now() else "ended"

        return render(
            request,
            self.template_name,
            {
                "auction": auction,
                "bids": bids,
                "auction_status": auction_status,
            },
        )
