import json
from decimal import Decimal

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from auction.models import Auction, Bid


class AuctionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.auction_id = self.scope["url_route"]["kwargs"]["auction_id"]
        self.auction_group_name = f"auction_{self.auction_id}"

        # Join auction group
        await self.channel_layer.group_add(self.auction_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        # Leave auction group
        await self.channel_layer.group_discard(
            self.auction_group_name, self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        bid_amount = Decimal(data["amount"])  # Convert bid amount to Decimal
        user = self.scope["user"]

        # Validate the bid
        auction = await sync_to_async(Auction.objects.get)(id=self.auction_id)
        if not auction.is_active():
            await self.send(json.dumps({"error": "Auction has ended."}))
            return

        # Check if the bid amount is higher than the current or starting price
        current_price = (
            auction.current_price if auction.current_price else auction.starting_price
        )
        if bid_amount > current_price:
            # Create the bid
            bid = await sync_to_async(Bid.objects.create)(
                auction=auction, user=user, amount=bid_amount
            )

            auction.current_price = bid_amount
            await sync_to_async(auction.save)()

            # Broadcast the new bid
            await self.channel_layer.group_send(
                self.auction_group_name,
                {
                    "type": "broadcast_bid",
                    "bid": {
                        "user": user.username,
                        "amount": str(bid_amount),
                        "timestamp": str(
                            bid.timestamp.strftime("%b. %d, %Y, %-I:%M %p")
                            .replace("AM", "a.m.")
                            .replace("PM", "p.m.")
                        ),
                    },
                },
            )
        else:
            await self.send(
                json.dumps({"error": "Bid must be higher than the current price."})
            )

    async def broadcast_bid(self, event):
        # Send the new bid to WebSocket
        bid = event["bid"]
        await self.send(
            text_data=json.dumps(
                {
                    "user": bid["user"],
                    "amount": bid["amount"],
                    "timestamp": bid["timestamp"],
                }
            )
        )

    async def end_auction(self, event):
        message = event["message"]

        # Send the auction end data to the WebSocket
        await self.send(
            text_data=json.dumps(
                {
                    "type": "auction_end",
                    "winner": message["winner"],
                    "winning_bid": message["winning_bid"],
                }
            )
        )
