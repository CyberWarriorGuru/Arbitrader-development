import datetime

from rest_framework import serializers
from arbitrage.models import Exchange


class ActionSerialier(serializers.Serializer):
    action = serializers.CharField(required=True)

    def clean_action(self, value):
        if value not in ["start", "stop"]:
            raise serializers.ValidationError()
        return value


class HistoricalDataSerializer(serializers.Serializer):
    trade_pair = serializers.CharField(required=True)
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)
    option = serializers.CharField(required=True)

    def clean_option(self, value):
        available_options = {
            "list_exchanges",
            "list_trade_pair_by_exchange",
            "list_general_trade_pair_ohlcv",
            "list_exchange_trade_pair_ohlcv",
        }
        if value not in available_options:
            raise serializers.ValidationError("Invalid option")
        return value

    def clean_end_date(self, value):
        if value > datetime.datetime.today():
            raise serializers.ValidationError("Date can not be in the future")
        return value

    def clean_start_date(self, value):
        if value > datetime.datetime.today():
            raise serializers.ValidationError("Date can not be in the future")
        return value

    def validate(self, data):
        if data["start_date"] > data["end_date"]:
            raise serializers.ValidationError(
                "Start date cannot be greater than end_date"
            )
        return data


def serialize_change(exchange):
    return {
        "name": exchange.name,
        "currency_pair": exchange.currency_pair,
        "last_ask_price": exchange.last_ask_price,
        "last_bid_price": exchange.last_bid_price,
    }
