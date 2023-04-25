import os
import time
import json
import hmac
import hashlib
import requests
from .ccxt_api import GenericExchangeHandler
from itertools import zip_longest as zipper
from .bitifnex_key_test import api_auth
from datetime import datetime, date
class BitfinexHandler(GenericExchangeHandler):
    """
    This class is capable of handling
    the requests required in order to process
    the different actions required for the requirements
    established.

    Exchange: bitfinex

    """

    def __init__(self, config):
        super().__init__(config)
        self.api_endpoints = {
            "root_public": "https://api-pub.bitfinex.com/v2/",
            "root_auth": "https://api.bitfinex.com/v2/",
            "available_currencies": "https://api-pub.bitfinex.com/v2/conf/pub:list:currency",
            "available_exchanges": "https://api-pub.bitfinex.com/v2/conf/pub:list:pair:exchange",
            "available_margins_trade_pairs": "https://api-pub.bitfinex.com/v2/conf/pub:list:pair:margin",
            "api_status": "https://api-pub.bitfinex.com/v2/platform/status",
        }
        self.exchange = "Bitfinex"
        self.ORDERS_FIELDS = [
            self.serialize_fields(field)
            for field in """ID,
                       GID,
                       CID,
                       SYMBOL,
                       MTS_CREATE,
                       MTS_UPDATE,
                       AMOUNT,
                       AMOUNT_ORIG,
                       TYPE,
                       TYPE_PREV,
                       FLAGS,
                       ORDER_STATUS,
                       PRICE_AVG,
                       PRICE_TRAILING,
                       PRICE_AUX_LIMIT,
                       HIDDEN,
                       PLACED_ID,
                       ROUTING,
                       META""".lower().split(
                "\n"
            )
        ]
        self.INCOMING_API_ORDER_FIELDS = [
            self.serialize_fields(field)
            for field in """ID
                       GID
                       CID
                       SYMBOL
                       MTS_CREATE
                       MTS_UPDATE
                       AMOUNT
                       AMOUNT_ORIG
                       TYPE
                       TYPE_PREV
                       _PLACEHOLDER
                       _PLACEHOLDER
                       FLAGS
                       ORDER_STATUS
                       _PLACEHOLDER
                       _PLACEHOLDER
                       PRICE
                       PRICE_AVG
                       PRICE_TRAILING
                       PRICE_AUX_LIMIT
                       _PLACEHOLDER
                       _PLACEHOLDER
                       _PLACEHOLDER
                       HIDDEN
                       PLACED_ID
                       _PLACEHOLDER
                       _PLACEHOLDER
                       _PLACEHOLDER
                       ROUTING
                       _PLACEHOLDER
                       _PLACEHOLDER
                       META""".lower().split(
                "\n"
            )
        ]
        self.ADDITIONAL_NEEDED_ORDER_FIELDS = [
            "mts",
            "type",
            "message_id",
            "null",
            "message_status",
            "code",
            "txt",
        ]

    @property
    def nonce(self):
        return str(datetime.timestamp(datetime.now()) * 1000).split(".")[0]

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

    def prepare_authentication(self, request_body, api_endpoint):
        """
        loads the values for the authentication
        in a dict used for the headers of the request

        basically it creates a signature hash that goes
        for the authentication

        :param request_body: dict
        :param api_endpoint str
        :return: dict : request header
        """
        return api_auth(rawBody=json.dumps(request_body),
                        secret=self.config['secret'],
                        api_key=self.config['api_key'],
                        path=f'v2/{api_endpoint}', non= self.nonce
                        )
        # nonce = self.nonce
        # sig = f"/api/v2/{api_endpoint}{nonce}{json.dumps(request_body)}".encode(
        #     encoding="UTF-8"
        # )
        # # sig = f"/api/v2/{api_endpoint}/{nonce}/{json.dumps(request_body)}"
        # signature = hmac.new(
        #     self.config["secret"].encode(encoding="UTF-8"), sig, hashlib.sha384
        # ).hexdigest()
        # header = {
        #     "Content-Type": "application/json",
        #     "bfx-nonce": self.nonce,
        #     "bfx-signature": signature,
        #     "bfx-apikey": self.config["api_key"],
        # }
        # header = self._headers(nonce=nonce,secret=self.config['secret'],key=self.config['api_key'],sig=sig)
        # print(nonce,sig,signature, header)
        # return header

    def _headers(self, nonce, secret, key, sig):
        secbytes = secret.encode(encoding="UTF-8")
        sigbytes = sig.encode(encoding="UTF-8")
        h = hmac.new(secbytes, sigbytes, hashlib.sha384)
        hexstring = h.hexdigest()
        return {
            "bfx-nonce": nonce,
            "bfx-apikey": key,
            "bfx-signature": hexstring,
            "content-type": "application/json",
        }

    @property
    def api_status(self):
        status = 'DOWN'
        try:
            response = requests.get(self.api_endpoints["api_status"]).json()[0]
            if response == 1:
                status = 'ACTIVE'

        except [IndexError, ConnectionError, AssertionError] as EX:
            status = f"INTERNAL ERROR: {EX}"

        finally:
            return status

    @property
    def supported_markets(self):
        """
        lists all supported exchanges for bitfinex
        :return:
        """
        result = None
        try:
            response = requests.get(self.api_endpoints["available_exchanges"], timeout=900)
            assert (
                response.status_code == 200
            ), f"There was a error with the request.{response.json()}"
            result = response.json()[0]

        except [IndexError, ConnectionError, AssertionError] as EX:
            result = f"INTERNAL ERROR: {EX}"

        finally:
            return result

    @property
    def available_currencies(self):
        """
        lists all supported exchanges for bitfinex
        :return:
        """
        response = requests.get(self.api_endpoints["available_currencies"])
        assert (
            response.status_code == 200
        ), f"There was a error with the request.{response.json()}"
        return response.json()[0]

    @property
    def available_margins_trade_pairs(self):
        """
        lists all supported exchanges for bitfinex
        :return:
        """
        response = requests.get(
            self.api_endpoints["available_margins_trade_pairs"]
        )
        assert (
            response.status_code == 200
        ), f"There was a error with the request.{response.json()}"
        return response.json()[0]

    def serialize_fields(self, field):
        """
        removes the blank space out of the string
        :param field: str
        :return: str
        """
        result = ""
        for char in field:
            if char != "" and char != " " and char != "\t" and char != ",":
                result += char
        return result

    def serialize_data(
        self,
        incoming_data_fields,
        fields,
        response_data,
        option="listing_orders",
    ):
        """
        cleans the data and assigns each object its existing
        field in order to make it work better
        :param incoming_data_fields: list
        :param fields: list
        :param response_data: list
        :param option: str: the only valid parms are:
        -submitting_order
        -listing_orders
        -listing_orders_historical
        -getting_order
        -updating_order
        -canceling_order
        :return: it's going to depend but the options are: generator or dict
        """
        valid_options = [
            "submitting_order",
            "listing_orders",
            "listing_orders_historical",
            "getting_order",
            "updating_order",
            "canceling_order",
        ]
        assert (
            option in valid_options
        ), f"The provided option: {option} is not valid, the valid ones are {valid_options}"

        if option == "listing_orders" or option == "listing_orders_historical":
            return (
                {
                    key: data
                    for key, data in zipper(incoming_data_fields, datalist)
                    if key in fields
                }
                for datalist in response_data
            )

        elif (
            option == "submitting_order"
            or option == "getting_order"
            or option == "updating_order"
            or option == "canceling_order"
        ):
            order_data = None
            for ix, value in enumerate(response_data):
                if isinstance(value, list):
                    order_data = response_data.pop(ix)
                    break
            order_data = {
                key: value
                for key, value in zipper(incoming_data_fields, order_data)
                if key in fields
            }
            # print(order_data, self.ADDITIONAL_NEEDED_ORDER_FIELDS, response_data)
            for key, value in zip(
                self.ADDITIONAL_NEEDED_ORDER_FIELDS, response_data
            ):
                order_data[key] = value
            return order_data

    def get_orders(self, trade_pair, since=None, limit=None, params={}):
        """
        loads the open orders for the account provided.
        :param trade_pair: trade_pair to use or market, it must match the existing ones
        :param since: timestamp
        :param limit: int which determines how many records is going to return
        :param params: dict: additional parameters to the request
        :return: generator
        """
        flag = False
        response = None
        try:
            assert self.validate_trade_pair(
                trade_pair
            ), f"The trade_pair {trade_pair} is not supported, please try a different one."
            endpoint = f"auth/r/orders/{trade_pair}"
            request_body = {"since": since, "limit": limit}

            for key, value in params.items():
                request_body[key] = value

            header = self.prepare_authentication(request_body, endpoint)
            url = f"{self.api_endpoints['root_auth']}{endpoint}"
            status, orders = self.process_request(
                url=url, method="post", headers=header, request_body=request_body
            )
            if not status:
                raise AttributeError(f"{orders}")

            response =  self.serialize_data(
                response_data=orders,
                incoming_data_fields=self.INCOMING_API_ORDER_FIELDS,
                fields=self.ORDERS_FIELDS,
                option="listing_orders",
            )
            flag = True

        except AssertionError as AX:
            response = f"{AX}"

        except Exception as X:
            response = f"{X}"

        finally:
            return flag, response

    def get_orders_history(self, trade_pair):
        """
        loads the orders for the account provided.
        :param trade_pair: trade_pair to use or market, it must match the existing ones
        :param since: timestamp
        :param limit: int which determines how many records is going to return
        :param params: dict: additional parameters to the request
        :return: generator
        """
        flag = False
        response = None
        try:
            assert self.validate_trade_pair(
                trade_pair
            ), f"The trade_pair {trade_pair} is not supported, please try a different one."
            endpoint = f"auth/r/orders/{trade_pair}/history"
            request_body = {}
            header = self.prepare_authentication(request_body, endpoint)
            url = f"{self.api_endpoints['root_auth']}{endpoint}"
            orders = self.process_request(
                url=url, method="get", headers=header, request_body=request_body
            )
            response = self.serialize_data(
                response_data=orders,
                incoming_data_fields=self.INCOMING_API_ORDER_FIELDS,
                fields=self.ORDERS_FIELDS,
                option="listing_orders_history")
            flag = True

        except AssertionError as AX:
            response = f"{AX}"

        except Exception as X:
            response = f"{X}"

        finally:
            return flag, response

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
        flag = False
        response = None
        try:
            assert self.validate_trade_pair(
                trade_pair
            ), f"The trade_pair {trade_pair} is not supported, please try a different one."
            endpoint = f"auth/r/orders/{trade_pair}"
            request_body = {"id": [order_id]}
            for key, value in params.items():
                request_body[key] = value
            header = self.prepare_authentication(request_body, endpoint)
            url = f"{self.api_endpoints['root_auth']}{endpoint}"
            order = self.process_request(
                url=url, method="post", headers=header, request_body=request_body
            )
            response = self.serialize_data(
                response_data=order,
                incoming_data_fields=self.INCOMING_API_ORDER_FIELDS,
                fields=self.ORDERS_FIELDS,
                option="getting_order",
            )
            flag = True

        except AssertionError as AX:
            response = f"{AX}"

        except Exception as X:
            response = f"{X}"

        finally:
            return flag, response


    def get_order_status(self, trade_pair, order_id):
        """
        :param trade_pair: str: trade_pair
        :param order_id: int
        :return: str
        """
        order_data = self.get_order(order_id, trade_pair)
        return order_data["order_status"]

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

    def submit_order(self, order_data):
        """
        :param order_data:dict containing the data required to submit an order
        :return:dict
        required parameters:
        type: type of order to make
        trade_pair:str
        price: price of the data
        amount: float: how much you want to offer
        """
        flag = False
        response = None

        required_fields = ["type", "trade_pair", "price", "amount"]
        try:
            self.has_required_params(required_fields, order_data)
            assert self.validate_trade_pair(
                order_data["trade_pair"]
            ), f"The trade_pair {order_data['trade_pair']} is not supported, please try a different one."
            endpoint = f"auth/w/order/submit"
            request_body = {
                "type": order_data.pop("order_type"),
                "symbol": order_data.pop("trade_pair"),
                "price": order_data.pop("price"),
                "amount": order_data.pop("amount"),
            }
            if len(order_data.keys()) > 0:
                for key in order_data.keys():
                    request_body[key] = order_data[key]
            header = self.prepare_authentication(request_body, endpoint)
            url = f"{self.api_endpoints['root_auth']}{endpoint}"
            order = self.process_request(
                url=url, method="post", headers=header, request_body=request_body
            )
            response= self.serialize_data(
                response_data=order,
                incoming_data_fields=self.INCOMING_API_ORDER_FIELDS,
                fields=self.ORDERS_FIELDS,
                option="submitting_order",
            )
            flag = True

        except AssertionError as AX:
            response = f"{AX}"

        except Exception as X:
            response = f"error: {x}"

        finally:
            return flag, response

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
        required_fields = ["order_id", "trade_pair", "price", "amount"]
        self.has_required_params(required_fields, order_data)
        assert self.validate_trade_pair(
            order_data["trade_pair"]
        ), f"The trade_pair {order_data['trade_pair']} is not supported, please try a different one."
        endpoint = f"auth/w/order/update"
        request_body = {
            "type": order_data.pop("order_type"),
            "symbol": order_data.pop("trade_pair"),
            "price": order_data.pop("price"),
            "amount": order_data.pop("amount"),
        }
        if len(order_data.keys()) > 0:
            for key in order_data.keys():
                request_body[key] = order_data[key]
        header = self.prepare_authentication(request_body, endpoint)
        url = f"{self.api_endpoints['root_auth']}{endpoint}"
        order = self.process_request(
            url=url, method="post", headers=header, request_body=request_body
        )
        return self.serialize_data(
            response_data=order,
            incoming_data_fields=self.INCOMING_API_ORDER_FIELDS,
            fields=self.ORDERS_FIELDS,
            option="updating_order",
        )

    def cancel_order(self, order_id):
        """
        cancels an existing order
        :param order_id: int
        :return: dict
        """
        endpoint = f"auth/w/order/cancel"
        request_body = {"id": order_id}
        header = self.prepare_authentication(request_body, endpoint)
        url = f"{self.api_endpoints['root_auth']}{endpoint}"
        order = self.process_request(
            url=url, method="post", headers=header, request_body=request_body
        )
        return self.serialize_data(
            self.INCOMING_API_ORDER_FIELDS,
            self.ORDERS_FIELDS,
            order,
            option="cancelling_order",
        )
