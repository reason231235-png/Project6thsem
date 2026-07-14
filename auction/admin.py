from django import forms
from django.contrib import admin
from django_celery_beat.models import (
    PeriodicTask,
    IntervalSchedule,
    CrontabSchedule,
    SolarSchedule,
    ClockedSchedule,
)

from product.models import Product
from auction.models import Auction, Bid


class AuctionForm(forms.ModelForm):
    class Meta:
        model = Auction
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter the product dropdown to show only products with is_auction=True
        self.fields["product"].queryset = Product.objects.filter(
            is_auction_product=True
        )


class AuctionAdmin(admin.ModelAdmin):
    form = AuctionForm  # Use the custom form
    list_display = (
        "product",
        "starting_price",
        "current_price",
        "start_time",
        "end_time",
        "winner",
    )
    list_filter = ("start_time", "end_time")
    search_fields = ("product__title",)


admin.site.register(Auction, AuctionAdmin)
admin.site.register(Bid)

# Unregister the models
admin.site.unregister(PeriodicTask)
admin.site.unregister(IntervalSchedule)
admin.site.unregister(CrontabSchedule)
admin.site.unregister(SolarSchedule)
admin.site.unregister(ClockedSchedule)
