from django import forms


class PaymentForm(forms.Form):
    order_id = forms.IntegerField(widget=forms.HiddenInput())
    shipping_address = forms.CharField(
        widget=forms.TextInput(attrs={"class": "w-full py-4 px-6 rounded-xl border"}),
        label="Shipping Address",
    )
    payment_method = forms.ChoiceField(
        choices=[
            ("esewa", "Esewa"),
            ("khalti", "Khalti"),
        ],
        widget=forms.RadioSelect(attrs={"class": "w-full py-4 px-6 rounded-xl border"}),
        label="Payment Method",
    )
