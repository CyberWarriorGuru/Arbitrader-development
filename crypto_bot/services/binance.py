import os
import time
import json
import hmac
import requests
import hashlib
from binance.client import Client
from .ccxt_api import GenericExchangeHandler


# need to be complete
class BinanceHandler(GenericExchangeHandler):
    """
    This class is capable of handling
    the requests required in order to process
    the different actions required for the requirements
    established.

    Exchange: binance
    """

    def __init__(self, config):
        super().__init__(config)
        self.api_endpoints = {
            "root": "https://api.binance.com/api/v3/",
            "different_root_options": {
                "v1": "https://api1.binance.com/api/v3/",
                "v2": "https://api2.binance.com/api/v3/",
                "v3": "https://api3.binance.com/api/v3/",
            },
        }
        self.exchange = "Binance"
        self.handler = Client(
            api_key=config["api_key"], api_secret=config["secret"]
        )

    def validate_config(self):
        """
        verifies if the required params exist in the config dictionary
        :return: error if there's one
        """
        required_config = ["api_key", "secret"]
        if "api_key" not in self.config or "secret" not in self.config:
            raise AttributeError(
                f"You must provide the configurations required which are: {required_config}"
            )

    # got a problem with this not being accepted by the
    # API since still saying it's behind the recvwindow.
    @property
    def nonce(self):
        """
        there's an issue with the timestamp, it will throw me
        back no matter how much I try getting it done. need to
        either change the timezone or find a solution for this.
        :return:
        """
        nonce = int(int(self.handler.get_server_time()["serverTime"]) / 1000)
        # nonce = int(self.handler.get_server_time()['serverTime'])
        print(time.localtime(nonce))
        return f"{nonce}"

    def prepare_authentication(self, request_body, signed=True):
        """
        loads the values for the authentication
        in a dict used for the headers of the request

        basically it creates a signature hash that goes
        for the authentication

        :param request_body: dict
        :param api_endpoint str
        :return: dict : request header
        """
        nonce = self.nonce
        request_body.update(timestamp=nonce, recvWindow=5000)
        sig = f"{self.build_querystring(request_body)}".encode()
        signature = hmac.new(
            self.config["secret"].encode(), sig, hashlib.sha256
        ).hexdigest()
        header = {
            "Content-Type": "application/json",
            "X-MBX-APIKEY": f"{self.config['api_key']}",
            "timestamp": nonce,
            "recvWindow": "7000",
        }
        if signed:
            header.update(signature=signature)
            request_body.update(signature=signature)
        # request_body.update(sig_url=sig.decode())
        return header

    def build_querystring(self, request_body):
        """
        builds a query string for the signature
        :param request_body: dict
        :return: str
        """
        sigs = [f"{key}={value}&" for key, value in request_body.items()]
        sigs[-1] = sigs[-1][: sigs[-1].find("&")]
        return "".join(sigs)

    @property
    def api_status(self):
        """
        gets the status of the api
        :return: str
        """
        return (
            "ACTIVE"
            if self.handler.get_system_status()["status"] <= 0
            else "DOWN"
        )

    @property
    def account_status(self):
        """
        verifies the account status
        :return: dict
        """
        return self.handler.get_account_status()

    @property
    def supported_markets(self):
        """
        lists all supported exchanges for binance
        :return:list
        """
        exchanges = [
            symbol["symbol"]
            for symbol in self.handler.get_exchange_info()["symbols"]
        ]
        return exchanges

    def serialize_data(self, **kwargs):
        """
        serializes the data coming from the api
        and turns it into a dictionary.
        :param kwargs:
        :return: dict
        """

    def get_orders(self, trade_pair, since=None, limit=None, params={}):
        """
        loads the open orders for the account provided.
        :param trade_pair: trade_pair to use or market, it must match the existing ones
        :param since: timestamp
        :param limit: int which determines how many records is going to return
        :param params: dict: additional parameters to the request
        :return: list
        Fields:
        """
        assert self.validate_trade_pair(
            trade_pair
        ), f"The trade_pair {trade_pair} is not supported, please try a different one."
        url = f"{self.api_endpoints['root']}openOrders"
        request_body = {
            "symbol": trade_pair,
            "startTime": since,
            "limit": limit,
        }

        if params != {}:
            for k in params.keys():
                request_body[k] = params[k]

        headers = self.prepare_authentication(request_body=request_body)
        orders = self.process_request(
            url=url, headers=headers, request_body=request_body, method="get"
        )
        print(orders)
        return orders

    def get_orders_history(
        self, trade_pair, since=None, limit=None, params={}
    ):
        """
        loads the orders for the account provided.
        :param trade_pair: trade_pair to use or market, it must match the existing ones
        :return: list
        """
        assert self.validate_trade_pair(
            trade_pair
        ), f"The trade_pair {trade_pair} is not supported, please try a different one."
        url = f"{self.api_endpoints['root']}allOrders"
        request_body = {
            "symbol": trade_pair,
            "startTime": since,
            "limit": limit,
        }

        if params != {}:
            for k in params.keys():
                request_body[k] = params[k]
        headers = self.prepare_authentication(request_body=request_body)
        orders = self.process_request(
            url=url, headers=headers, request_body=request_body, method="get"
        )
        print(orders)
        return orders

    def get_order(self, order_id, trade_pair, params={}):
        """
        loads the order provided.
        :param order_id: str
        :return: dict
        the accepted params for this are:
        trade_pair: trade_pair to use or market, it must match the existing ones
        since: timestamp
        limit: int which determines how many records is going to return
        """
        assert self.validate_trade_pair(
            trade_pair
        ), f"The trade_pair {trade_pair} is not supported, please try a different one."
        url = f"{self.api_endpoints['root']}order"
        request_body = {"order_id": order_id, "symbol": trade_pair}
        if params != {}:
            for k in params.keys():
                request_body[k] = params[k]
        headers = self.prepare_authentication(request_body)
        order = self.process_request(url, headers, "get", request_body)
        print(order)
        return order

    def get_order_status(self, trade_pair, order_id):
        """
        :param trade_pair: str: trade_pair
        :param order_id: int
        :return: str
        """
        order = self.get_order(order_id, trade_pair)
        return order["status"]

    def has_required_params(self, required, data):
        """
        verifies if the data has the required fields
        :param required: list
        :param data: dict
        :return: None
        """
        assert all(
            True if field in required else False for field in data.keys()
        ), f"you're missing some fo these fields {required}"

    def submit_order(self, order_data, test=False):
        """
        creates an order
        required parameters:
        type: type of order to make
        trade_pair:str
        price: price of the data
        amount: float: how much you want to offer

        :param order_data:dict containing the data required to submit an order
        :return:dict
        """
        url = f"{self.api_endpoints['root']}order"
        test_url = f"{self.api_endpoints['root']}order/test"
        required_fields = [
            "symbol",
            "side",
            "type",
            "timestamp",
            "price",
            "quantity",
            "timestamp",
        ]
        self.validate_required_fields(
            required_fields=required_fields, request_data=order_data
        )
        request_body = {key: value for key, value in order_data.items()}
        headers = self.prepare_authentication(request_body)
        order = self.process_request(
            url if not test else test_url, headers, "post", request_body
        )
        print(order)
        return order

    def update_order(self, order_data):
        """
        updates an existing order
        :param order_data: dict containing all data
        minimum required fields for the update:
        trade_pair
        order_id
        amount
        price
        :return: dict
        """

    def sell_order(self, order_data, limit=False):
        """
        :param trade_pair: str: trade_pair
        :param order_data: dict: params for the order to buy
        :param limit: bool: if true, it will try to sell the
        order with a limit param and if this param is not provided
        it will return an error
        :return:dict
        """
        required_params = ["symbol", "type", "timestamp", "price", "quantity"]
        self.validate_required_fields(
            required_fields=required_params, request_data=order_data
        )
        if limit:
            assert "limit" in order_data.keys(), (
                f"The option limit is {limit}, therefore you should"
                f"provide the values required for the limit option."
            )
        order_data.update(side="sell")
        sell_order = self.submit_order(order_data)
        return sell_order

    def buy_order(self, order_data, limit=False):
        """
        :param trade_pair: str: trade_pair
        :param order_data: dict: params for the order to buy
        :param limit: bool: if true, it will try to buy the
        order with a limit param and if this param is not provided
        it will return an error
        :return: dict
        """
        required_params = ["symbol", "type", "timestamp", "price", "quantity"]
        self.validate_required_fields(
            required_fields=required_params, request_data=order_data
        )
        if limit:
            assert "limit" in order_data.keys(), (
                f"The option limit is {limit}, therefore you should"
                f"provide the values required for the limit option."
            )
        order_data.update(side="buy")
        buy_order = self.submit_order(order_data)
        return buy_order

    def cancel_order(self, symbol, order_id):
        """
        cancels an existing order
        :param order_id: int
        :return: dict
        """
        url = f"{self.api_endpoints['root']}order"
        request_body = {
            "orderId": order_id,
            "symbol": symbol,
            "timestamp": self.nonce,
        }
        headers = self.prepare_authentication(request_body)
        request_body.update(timestamp=headers["timestamp"])
        cancelled_order = self.process_request(
            url, headers, "delete", request_body
        )
        print(cancelled_order)
        return cancelled_order

    def cancel_all_orders(self, symbol, timestamp):
        """
        cancel all orders under a symbol
        :param symbol: trade_pair
        :return: dict
        """
        url = f"{self.api_endpoints['root']}openOrders"
        request_body = {"symbol": symbol, "timestamp": timestamp}
        headers = self.prepare_authentication(request_body)
        cancelled_orders = self.process_request(
            url, headers, "delete", request_body
        )
        print(cancelled_orders)
        return cancelled_orders
