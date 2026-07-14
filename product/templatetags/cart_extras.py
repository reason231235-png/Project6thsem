from django import template
from product.models import Product

register = template.Library()


@register.filter(name="cart_of")
def liked_by(product, user):
    return product.in_cart_of(user)
