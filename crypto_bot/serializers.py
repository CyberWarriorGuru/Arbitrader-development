from rest_framework.serializers import ModelSerializer
from .models import *


class OrderSerializer(ModelSerializer):
    """
    this serializer is used to shape, clean and validate
    the data requried from the data coming
    from the request and going to it
    """

    class Meta:
        model = Order
        fields = [
            "order_id",
            "order_datetime",
            "order_timestamp",
            "status",
            "symbol",
            "side",
            "price",
            "amount",
            "filled",
            "remaining",
            "cost",
            "trades",
            "fee",
            "info",
        ]
