import os, sys
import datetime
import pdb
import math
import random
import unittest
from django.test import TestCase
from crypto_bot.services.ccxt_api import CCXTApiHandler
from crypto_bot.services.coingecko import CoinGeckoHandler
from crypto_bot.utils import get_timestamp
#from crypto_bot.services.binance import BinanceHandler
#from crypto_bot.services.bitfinex import BitfinexHandler
#from crypto_bot.services.bitstamp import BitstampHandler
from crypto_bot.management.commands.feed_exchange_history import Command as C
from crypto_bot.models import *
#from redis.client import Redis as rd_obj
import json


# --------------------------------------------------------------------------
# Test Services
# --------------------------------------------------------------------------


class TestCcxtApiWrapper(unittest.TestCase):
    def setUp(self):
        self.client = CCXTApiHandler()
        self.supported_exchanges = self.client.supported_exchanges

    @staticmethod
    def get_exchange(client):
        return client.supported_exchanges.get("binance")({})

    def test_a_load_exchange_manager(self):
        exchanges = self.supported_exchanges
        # load all exchange managers
        for exchange in exchanges:
            manager = self.client.load_exchange_manager(exchange, {})
        # Throws assertion error because it does not exist.
        with self.assertRaises(AssertionError):
            self.client.load_exchange_manager("xxxxxxx", {})

    def test_b_get_exchange_field(self):
        """
        What is the first argument of the method?
        """
        fields = [
            "id",
            "name",
            "countries",
            "urls",
            "version",
            "api",
            "has",
            "timeframes",
            "timeout",
            "rateLimit",
            "userAgent",
            "symbols",
            "currencies",
            "markets_by_id",
            "apiKey",
            "secret",
            "password",
            "uid",
        ]
        exchange = self.client.supported_exchanges.get("binance")({})
        self.assertTrue(exchange.name.lower() == "binance")
        exchange_fields = self.client.get_exchange_fields(exchange)
        load = json.loads(exchange_fields)
        self.assertGreater(len(load.keys()), 0)

    @unittest.expectedFailure
    def test_list_orders(self):
        """
        tests the list of orders based on the exchange object
        :return: failure if not not matched

        To make it work, you might need to provide your own keys for the exchange to be used.
        this one is specifically fixed for binance.
        """
        symbol = "BTC/USDT"
        exchange_config = {"api_key": "secret", "secret": "secret"}
        exchange = self.supported_exchanges["binance"](exchange_config)
        self.assertIsInstance(
            self.client.list_orders(exchange_obj=exchange, symbol=symbol),
            list,
            "There was an error loading the orders for the exchange",
        )

    @unittest.expectedFailure
    def test_list_currencies_for_selected_exchange(self):
        exchange_config = {"api_key": "secret", "secret": "secret"}
        exchange = self.supported_exchanges["binance"](exchange_config)
        self.assertIsInstance(
            self.client.list_currencies(exchange_obj=exchange),
            list,
            "There was an error loading the orders for the exchange",
        )

    def test_b_list_markets(self):
        exchang = self.get_exchange(self.client)
        markets = self.client.list_markets(exchang, params={})

    def test_c_get_market(self):
        exchang = self.get_exchange(self.client)
        markets = self.client.list_markets(exchange_obj=exchang, params={})
        market = self.client.get_market(
            exchange_obj=exchang, market_id=markets[0]["id"], params={}
        )
        self.assertIsInstance(market, dict)
        # Test a bad market_id
        with self.assertRaises(AttributeError):
            market = self.client.get_market(
                exchange_obj=exchang, market_id="AUNTJEMIMA", params={}
            )

    def test_d_get_ohlcv(self):
        exchang = self.get_exchange(self.client)
        symbol = "BTC/USDT"
        ohlcv = self.client.get_ohlcv(exchange_obj=exchang, symbol=symbol)
        self.assertGreater(len(ohlcv), 0)

    def test_e_parse_ohlcv(self):
        exchang = self.get_exchange(self.client)
        symbol = "BTC/USDT"
        ohlcv = self.client.get_ohlcv(exchange_obj=exchang, symbol=symbol)
        parsed = self.client.parse_ohlcv(exchang, ohlcv[0])
        self.assertGreater(len(parsed), 0)

    def test_f_parse_ohlcvs(self):
        exchang = self.get_exchange(self.client)
        symbol = "BTC/USDT"
        markets = self.client.list_markets(exchange_obj=exchang, params={})
        market = self.client.get_market(
            exchange_obj=exchang, market_id=markets[0]["id"], params={}
        )
        ohlcv = self.client.get_ohlcv(exchange_obj=exchang, symbol=symbol)
        ohlcvs = self.client.parse_ohlcvs(exchange_obj=exchang, ohlcvs=ohlcv)
        self.assertTrue(ohlcv, ohlcvs)


class TestBitfinexService(TestCase):
    def setUp(self):
        self.api_config = {}
        self.client = BitfinexHandler(config=self.api_config)
        self.api_endpoints = {
            "root_public": "https://api-pub.bitfinex.com/v2/",
            "root_auth": "https://api.bitfinex.com/v2/",
            "available_currencies": "https://api-pub.bitfinex.com/v2/conf/pub:list:currency",
            "available_exchanges": "https://api-pub.bitfinex.com/v2/conf/pub:list:pair:exchange",
            "available_margins_trade_pairs": "https://api-pub.bitfinex.com/v2/conf/pub:list:pair:margin",
            "api_status": "https://api-pub.bitfinex.com/v2/platform/status",
        }
        self.redis = rd_obj()

    @unittest.expectedFailure
    def test_retrieve_orders_fail(self):
        """
        retrieves all existing orders for the given currency
        this is supposed to provide an assertion error.
        :return: error if any
        """
        # trade_pair = random.choice(self.client.supported_exchanges)
        trade_pair = "BTCDPOQ"
        endpoint = f"auth/r/orders/{trade_pair}"
        url = f"{self.api_endpoints['root_auth']}auth/r/orders/{trade_pair}"
        limit = 500
        since = datetime.datetime.timestamp()
        request_body = {"symbol": endpoint, "limit": limit, "since": since}
        headers = self.client.prepare_authentication(
            endpoint=endpoint, request_body=request_body
        )
        self.assertRaises(
            AssertionError,
            self.client.process_request(
                url=url,
                request_body=request_body,
                method="post",
                headers=headers,
            ),
        )

    def test_retrieve_orders(self):
        """
        retrieves all existing orders for the given currency
        :return: error if any
        """
        trade_pair = random.choice(self.client.supported_exchanges)
        endpoint = f"auth/r/orders/{trade_pair}"
        url = f"{self.api_endpoints['root_auth']}auth/r/orders/{trade_pair}"
        limit = 500
        since = datetime.datetime.timestamp()
        request_body = {"symbol": endpoint, "limit": limit, "since": since}
        headers = self.client.prepare_authentication(
            endpoint=endpoint, request_body=request_body
        )
        response = self.client.process_request(
            url=url, request_body=request_body, method="post", headers=headers
        )
        self.assertIsInstance(
            response, list, f"There was an error: {response}"
        )

    def test_submit_order(self):
        """
        submits a test order for the given account
        this should return a dictionary, if not
        this will cause an error.
        :return: error if any
        """

    def test_get_orders_history(self):
        """
        submits a test order for the given account
        this should return a dictionary, if not
        this will cause an error.
        :return: error if any
        """

    def test_cancel_order(self):
        """
        submits a test order for the given account
        this should return a dictionary, if not
        this will cause an error.
        :return: error if any
        """

    def test_update_order(self):
        """
        updates an existing order
        if not this will cause an error
        :return:
        """


class TestBinanceService(TestCase):
    def setUp(self):
        self.api_config = {"secret": "", "api_key": ""}
        self.client = BinanceHandler(config=self.api_config)
        self.api_endpoints = {}

    @unittest.expectedFailure
    def test_retrieve_orders_fail(self):
        """
        retrieves all existing orders for the given currency
        this is supposed to provide an assertion error.
        :return: error if any
        """
        # trade_pair = random.choice(self.client.supported_exchanges)
        trade_pair = "BTCDPOQ"
        endpoint = f"auth/r/orders/{trade_pair}"
        url = f"{self.api_endpoints['root_auth']}auth/r/orders/{trade_pair}"
        limit = 500
        since = datetime.datetime.timestamp()
        request_body = {"symbol": endpoint, "limit": limit, "since": since}
        headers = self.client.prepare_authentication(
            endpoint=endpoint, request_body=request_body
        )
        self.assertRaises(
            AssertionError,
            self.client.process_request(
                url=url,
                request_body=request_body,
                method="post",
                headers=headers,
            ),
        )

    def test_retrieve_orders(self):
        """
        retrieves all existing orders for the given currency
        :return: error if any
        """
        trade_pair = random.choice(self.client.supported_exchanges)
        endpoint = f"auth/r/orders/{trade_pair}"
        url = f"{self.api_endpoints['root_auth']}auth/r/orders/{trade_pair}"
        limit = 500
        since = datetime.datetime.timestamp()
        request_body = {"symbol": endpoint, "limit": limit, "since": since}
        headers = self.client.prepare_authentication(
            endpoint=endpoint, request_body=request_body
        )
        response = self.client.process_request(
            url=url, request_body=request_body, method="post", headers=headers
        )
        self.assertIsInstance(
            response, list, f"There was an error: {response}"
        )

    def test_submit_order(self):
        """
        submits a test order for the given account
        this should return a dictionary, if not
        this will cause an error.
        :return: error if any
        """

    def test_get_orders_history(self):
        """
        submits a test order for the given account
        this should return a dictionary, if not
        this will cause an error.
        :return: error if any
        """

    def test_cancel_order(self):
        """
        submits a test order for the given account
        this should return a dictionary, if not
        this will cause an error.
        :return: error if any
        """

    def test_update_order(self):
        """
        updates an existing order
        if not this will cause an error
        :return:
        """


class TestBitstampService(TestCase):
    def setUp(self):
        self.api_config = {
            "customer_username": "",
            "secret": "",
            "api_key": "",
        }
        self.client = BitstampHandler(config=self.api_config)
        self.api_endpoints = {}

    @unittest.expectedFailure
    def test_retrieve_orders_fail(self):
        """
        retrieves all existing orders for the given currency
        this is supposed to provide an assertion error.
        :return: error if any
        """
        # trade_pair = random.choice(self.client.supported_exchanges)
        trade_pair = "BTCDPOQ"
        endpoint = f"auth/r/orders/{trade_pair}"
        url = f"{self.api_endpoints['root_auth']}auth/r/orders/{trade_pair}"
        limit = 500
        since = datetime.datetime.timestamp()
        request_body = {"symbol": endpoint, "limit": limit, "since": since}
        headers = self.client.prepare_authentication(
            endpoint=endpoint, request_body=request_body
        )
        self.assertRaises(
            AssertionError,
            self.client.process_request(
                url=url,
                request_body=request_body,
                method="post",
                headers=headers,
            ),
        )

    def test_retrieve_orders(self):
        """
        retrieves all existing orders for the given currency
        :return: error if any
        """
        trade_pair = random.choice(self.client.supported_exchanges)
        endpoint = f"auth/r/orders/{trade_pair}"
        url = f"{self.api_endpoints['root_auth']}auth/r/orders/{trade_pair}"
        limit = 500
        since = datetime.datetime.timestamp()
        request_body = {"symbol": endpoint, "limit": limit, "since": since}
        headers = self.client.prepare_authentication(
            endpoint=endpoint, request_body=request_body
        )
        response = self.client.process_request(
            url=url, request_body=request_body, method="post", headers=headers
        )
        self.assertIsInstance(
            response, list, f"There was an error: {response}"
        )

    def test_submit_order(self):
        """
        submits a test order for the given account
        this should return a dictionary, if not
        this will cause an error.
        :return: error if any
        """

    def test_get_orders_history(self):
        """
        submits a test order for the given account
        this should return a dictionary, if not
        this will cause an error.
        :return: error if any
        """

    def test_cancel_order(self):
        """
        submits a test order for the given account
        this should return a dictionary, if not
        this will cause an error.
        :return: error if any
        """

    def test_update_order(self):
        """
        updates an existing order
        if not this will cause an error
        :return:
        """


# --------------------------------------------------------------------------
# Test Commands and Strategies
# --------------------------------------------------------------------------


class TestHistoricalData(TestCase):
    """
    These test will work
    directly on the historical feed exchange data
    """

    def setUp(self):
        self.client = CoinGeckoHandler()
        self.cctx_client = CCXTApiHandler()
        self.command_obj = C()
        self.command_options = {
            "list_exchanges": self.command_obj.list_exchanges,
            "list_trade_pair_by_exchange": self.command_obj.list_trade_pairs_by_exchange,
            "list_general_trade_pair_ohlcv": self.command_obj.list_general_trade_pair_ohlcv,
            "list_exchange_trade_pair_ohlcv": self.command_obj.list_exchange_trade_pair_ohlcv,
        }
        self.exchanges_accepted = [
            "Binance",
            "Kraken",
            "Bisq",
            "coinbase",
            "bitfinex",
            "kucoin",
            "ftx",
            "liquid",
            "bithumb",
            "poloniex",
        ]

    def test_list_exchanges(self):
        """
        verifies all available exchanges suited by the command
        :return: error if not matched
        """
        option = "list_exchanges"
        passed, response_data = self.command_options[option]()
        # print(passed, response_data)
        self.assertIsInstance(
            response_data,
            list,
            f"The value provided,"
            f" is not a list, there must be an error{response_data}",
        )

    def test_trade_pairs_by_exchange(self):
        """
        verifies all available exchanges suited by the command
        :return: error if not matched
        """
        option = "list_trade_pair_by_exchange"

        params = {"exchange": "coinbase", "cache": True}
        passed, response_data = self.command_options[option](params=params)
        self.assertTrue(passed, f"{response_data}")

    def test_list_general_trade_pair_ohlcv_not_supported_coin_cache(self):
        """
        test the plain information related to the given
        exchange.
        this one is basically related to a coin itself for coingecko
        :return: error if not match assertion
        """
        since = datetime.datetime(
            day=7, month=1, year=2021, hour=0, minute=0, second=0
        )

        since = since - datetime.timedelta(days=90)
        limit = since + datetime.timedelta(days=30)

        since = since.timestamp()
        limit = limit.timestamp()

        # coins = self.client.supported_coins
        # coin_id = random.choice(coins)
        coin_id = "ether"

        param = dict(
            coin_id=coin_id,
            currency="usd",
            since=since,
            limit=limit,
            cache=True,
            commit=False,
        )

        option = "list_general_trade_pair_ohlcv"
        passed, response_data = self.command_options[option](param)
        # print(passed, response_data)
        self.assertTrue(passed, f"{response_data}")

    def test_list_general_trade_pair_ohlcv_not_supported_coin_commit(self):
        """
        test the plain information related to the given
        exchange.
        this one is basically related to a coin itself for coingecko
        :return: error if not match assertion
        """
        since = datetime.datetime(
            day=7, month=1, year=2021, hour=0, minute=0, second=0
        )

        since = since - datetime.timedelta(days=90)
        limit = since + datetime.timedelta(days=30)

        since = since.timestamp()
        limit = limit.timestamp()

        # coins = self.client.supported_coins
        # coin_id = random.choice(coins)
        coin_id = "ether"

        param = dict(
            coin_id=coin_id,
            currency="usd",
            since=since,
            limit=limit,
            cache=False,
            commit=True,
        )

        option = "list_general_trade_pair_ohlcv"
        passed, response_data = self.command_options[option](param)
        # print(passed, response_data)
        self.assertTrue(passed, f"{response_data}")

    def test_list_general_trade_pair_ohlcv_cache(self):
        """
        test the plain information related to the given
        exchange.
        this one is basically related to a coin itself for coingecko
        :return: error if not match assertion
        """
        since = datetime.datetime(
            day=7, month=1, year=2021, hour=0, minute=0, second=0
        )

        since = since - datetime.timedelta(days=90)
        limit = since + datetime.timedelta(days=30)

        since = since.timestamp()
        limit = limit.timestamp()

        coins = self.client.supported_coins
        coin_id = random.choice(coins)

        param = dict(
            coin_id=coin_id,
            currency="usd",
            since=since,
            limit=limit,
            cache=True,
            commit=False,
        )

        option = "list_general_trade_pair_ohlcv"
        passed, response_data = self.command_options[option](param)
        # print(passed, response_data)
        self.assertTrue(passed, f"{response_data}")

    def test_list_general_trade_pair_ohlcv_commit(self):
        """
        test the pain information related to the given
        exchange.
        this one is basically related to a coin itself for coingecko
        :return: error if not match assertion
        """
        since = datetime.datetime(
            day=7, month=1, year=2021, hour=0, minute=0, second=0
        )

        since = since - datetime.timedelta(days=90)
        limit = since + datetime.timedelta(days=30)

        since = since.timestamp()
        limit = limit.timestamp()

        coins = self.client.supported_coins
        coin_id = random.choice(coins)

        param = dict(
            coin_id=coin_id,
            currency="usd",
            since=since,
            limit=limit,
            cache=False,
            commit=True,
        )

        option = "list_general_trade_pair_ohlcv"
        passed, response_data = self.command_options[option](param)
        self.assertTrue(
            passed, f"There was an error during this process {response_data}"
        )

    @unittest.expectedFailure
    def list_exchange_trade_pair_ohlcv_not_supported_cache(self):
        """
        test the pain information related to the given
        exchange.
        this works with cctx
        :return: error if not match assertion
        """
        since = datetime.datetime(
            day=7, month=1, year=2021, hour=0, minute=0, second=0
        )

        since = since - datetime.timedelta(days=90)
        limit = since + datetime.timedelta(days=30)

        since = since.timestamp()
        limit = limit.timestamp()
        exchange = ""

        param = dict(
            exchange=exchange,
            currency="usd",
            since=since,
            limit=limit,
            cache=True,
            commit=False,
        )

        option = "list_exchange_trade_pair_ohlcv"
        passed, response_data = self.command_options[option](param)
        # print(option, passed, response_data)
        self.assertTrue(passed, f"{response_data}")

    @unittest.expectedFailure
    def list_exchange_trade_pair_ohlcv_not_supported_commit(self):
        """
        test the pain information related to the given
        exchange.
        this works with cctx
        :return: error if not match assertion
        """
        since = datetime.datetime(
            day=7, month=1, year=2021, hour=0, minute=0, second=0
        )

        since = since - datetime.timedelta(days=90)
        limit = since + datetime.timedelta(days=30)

        since = since.timestamp()
        limit = limit.timestamp()
        exchange = ""

        param = dict(
            exchange=exchange,
            currency="usd",
            since=since,
            limit=limit,
            cache=False,
            commit=True,
        )

        option = "list_exchange_trade_pair_ohlcv"
        passed, response_data = self.command_options[option](param)
        # print(option, passed, response_data)
        self.assertTrue(passed, f"{response_data}")

    def list_exchange_trade_pair_ohlcv_cache(self):
        """
        test the pain information related to the given
        exchange.
        this works with cctx
        :return: error if not match assertion
        """
        """
                test the pain information related to the given
                exchange.
                this works with cctx
                :return: error if not match assertion
                """
        since = datetime.datetime(
            day=7, month=1, year=2021, hour=0, minute=0, second=0
        )

        since = since - datetime.timedelta(days=90)
        limit = since + datetime.timedelta(days=30)

        since = since.timestamp()
        limit = limit.timestamp()
        exchange = random.choice(self.exchanges_accepted)

        param = dict(
            exchange=exchange,
            currency="usd",
            since=since,
            limit=limit,
            cache=True,
            commit=False,
        )

        option = "list_exchange_trade_pair_ohlcv"
        passed, response_data = self.command_options[option](param)
        # print(option, passed, response_data)
        self.assertTrue(passed, f"{response_data}")

    def list_exchange_trade_pair_ohlcv_commit(self):
        """
        test the pain information related to the given
        exchange.
        this works with CCXT
        :return: error if not match assertion
        """
        since = datetime.datetime(
            day=7, month=1, year=2021, hour=0, minute=0, second=0
        )

        since = since - datetime.timedelta(days=90)
        limit = since + datetime.timedelta(days=30)

        since = since.timestamp()
        limit = limit.timestamp()
        exchange = random.choice(self.exchanges_accepted)

        param = dict(
            exchange=exchange,
            currency="usd",
            since=since,
            limit=limit,
            cache=False,
            commit=True,
        )

        option = "list_exchange_trade_pair_ohlcv"
        passed, response_data = self.command_options[option](param)
        # print(option, passed, response_data)
        self.assertTrue(passed, f"{response_data}")
