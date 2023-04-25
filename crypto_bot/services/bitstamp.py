import os
import time
import json
import hmac
import hashlib
import requests
from .ccxt_api import GenericExchangeHandler
from bitstamp.client import Public, Trading


class BitStampHandler(GenericExchangeHandler):
    """
    This is a bitstamp handler which
    takes the order endpoints required to manage
    the orders and implement them with the
    crypto bot and other services required.

    it's required to pass the key and secret for the
    API, without a profile it won't run.
    """

    def __init__(self, config):
        super().__init__(config)
        self.exchange = "Bitstamp"
        self.endpoints = {"root": "https://www.bitstamp.net/api/v2/"}
        self.public_handler = Public()
        self.auth_handler = Trading(
            self.config["customer_username"],
            key=self.config["api_key"],
            secret=self.config["secret"],
        )

    def validate_config(self):
        """
        validates if the config dict
        has the required fields to run the
        handler
        :return: None
        """
        if (
            "customer_id" not in self.config.keys()
            or "customer_username" not in self.config.keys()
        ):
            raise AttributeError(
                f"You must provide the customer_id/customer_username"
                f" for the bitstamp account to query from."
            )
        return super().validate_config()

    def get_account_balance(self, base, quote):
        """
        gets the balance for the given account
        :return: dict
        """
        return self.auth_handler.account_balance(base, quote)

    def prepare_authentication(self, customer_id):
        """
        generates the signature required for authenticated
        endpoints
        :param customer_id: id of the bitstamp account
        :return:
        """
        nonce = self.nonce
        message = f"{nonce}{customer_id}{self.config['api_key']}"
        signature = (
            hmac.new(
                self.config["secret"], msg=message, digestmod=hashlib.sha256
            )
            .hexdigest()
            .upper()
        )
        header = {
            "Content-Type": "application/json",
            "X-Auth-Signature": signature,
            "X-Auth": f"BITSTAMP {self.config['api_key']}",
            "X-Auth-Nonce": nonce,
            "X-Auth-Timestamp": int(time.time()),
        }
        return header

    @property
    def available_markets(self):
        """
        lists all of the available markets
        :return: list
        """
        return self.public_handler.trading_pairs_info()

    def get_orders(self, base, quote):
        """
        retrieves the list of all order based on the base+quote=trade_pair
        :param base: pair identifier of the currency to convert from
        :param quote: pair identifier of the currency to use against
        :return: list
        """
        return self.auth_handler.open_orders(base=base, quote=quote)

    def get_all_open_orders(self):
        """
        lists all open orders through
        all exchanges
        :return: list
        """
        return self.auth_handler.all_open_orders()

    def get_order(self, order_id, trade_pair, params={}):
        """
        gets the order specified with the order id
        :param order_id: int: repr of the order needed.
        :return:dict
        """
        orders = self.get_all_open_orders()

        for order in orders:
            if order["id"] == str(order_id):
                return order
        raise AttributeError(f"the order {order_id} doesn't exist.")

    def get_order_status(self, order_id):
        """
        returns the order status
        :param order_id: int
        :return: dict
        """
        return self.auth_handler.order_status(order_id)

    def cancel_order(self, order_id):
        """
        cancels the given order id and returns the order cancelled
        :param order_id: int
        :return: dict
        """
        return self.auth_handler.cancel_order(order_id)

    def get_orders_history(self, base, quote):
        """
        gets the history olhcv values for the base and quote values
        :param base: pair identifier of the currency to convert from
        :param quote: pair identifier of the currency to use against
        :return:list
        """
        return self.auth_handler.order_book(base=base, quote=quote)

    def buy_order(self, order_data):
        """
        creates a buy order with the given params
        :param order_data: dict
        :return: dict
        """
        required = ["amount", "base", "quote"]
        evaluation, error = self.validate_required_fields(
            required_fields=required, request_data=order_data
        )
        if not evaluation:
            raise AttributeError(error)
        return self.auth_handler.buy_market_order(
            amount=order_data["amount"],
            base=order_data["base"],
            quote=order_data["quote"],
        )

    def sell_order(self, order_data):
        """
        buys an order required
        :param order_data: dict
        :return:dict
        """
        required = ["amount", "base", "quote"]
        evaluation, error = self.validate_required_fields(
            required_fields=required, request_data=order_data
        )
        if not evaluation:
            raise AttributeError(error)
        return self.auth_handler.sell_market_order(
            amount=order_data["amount"],
            base=order_data["base"],
            quote=order_data["quote"],
        )

    def limit_sell_order(self, order_data):
        """
        creates a sell order based on a limit price
        which means it will sell to a limit price
        :param order_data: dict
        :return: dict
        """
        required = [
            "price",
            "amount",
            "base",
            "quote",
            "limit_price",
            "ioc_order",
        ]
        evaluation, error = self.validate_required_fields(
            required_fields=required, request_data=order_data
        )
        if not evaluation:
            raise AttributeError(error)
        return self.auth_handler.sell_limit_order(
            price=order_data["price"],
            amount=order_data["amount"],
            base=order_data["base"],
            quote=order_data["quote"],
            limit_price=order_data["limit_price"],
            ioc_order=order_data["ioc_order"],
        )

    def limit_buy_order(self, order_data):
        """
        buys the given order based on the given parameters respecting the linmit provided
        if such limit is found, the order should be bought below that limit amount
        :param order_data: dict containing order data
        :return: dict
        """
        required = [
            "price",
            "amount",
            "base",
            "quote",
            "limit_price",
            "ioc_order",
        ]
        evaluation, error = self.validate_required_fields(
            required_fields=required, request_data=order_data
        )
        if not evaluation:
            raise AttributeError(error)

        return self.auth_handler.buy_limit_order(
            price=order_data["price"],
            amount=order_data["amount"],
            base=order_data["base"],
            quote=order_data["quote"],
            limit_price=order_data["limit_price"],
            ioc_order=order_data["ioc_order"],
        )
