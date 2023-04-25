import os
import json
import requests
import ccxt as ct
import datetime, time
from binance.client import Client as binance_client
from ccxt.base.errors import NotSupported, BadSymbol, BadRequest, BaseError
from abc import abstractmethod


class CCXTApiHandler(object):
    """
    implementation of ccxt sdk
    for consuming data for the crypto bot
    """

    def __init__(self):
        self.supported_exchanges = {
            key: getattr(ct, key) for key in ct.exchanges
        }

    def load_exchange_manager(self, exchange, exchange_config={}):
        """
        loads the data_manager for
        the given exchange as long
        as it's supported by the app
        :param: str: exchange name
        :param exchange_config: dict: containing all needed
        configurations for the exchange to work.
        :return: object
        """
        assert (
            exchange in self.supported_exchanges.keys()
        ), f"The exchange provided: {exchange} is not supported."

        return self.supported_exchanges[exchange](config=exchange_config)

    def get_supported_markets(self, exchange_obj):
        """
        lists all of the symbols or trade_pair markets available
        based on the existing object.
        :param exchange_obj: obj
        :return: list
        """
        return exchange_obj.markets.keys()

    def get_exchange_fields(self, exchange_obj):
        """
        loads all of the usable fields for the given exchange
        and returns it in a json format
        :param exchange_obj: exchange object
        :return: JSON
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
        return json.dumps(
            {
                key: value
                for key, value in exchange_obj.__dict__.items()
                if key in fields
            }
        )

    def list_markets(self, exchange_obj, params):
        """
        lists all of the markets available
        to the given exchange object
        :param exchange_obj:exchange object
        :param params: dict, params to get the market
        :return: list
        """
        return exchange_obj.fetch_markets(params=params)

    def get_market(self, exchange_obj, market_id, params):
        """
        gets an specific market from all supported
        markets in the exchange
        :param exchange_obj: exchange object
        :param market_id: str identifier of the market
        :param params: dict, params to get the market
        :return: dict
        """
        markets = self.list_markets(exchange_obj, params)
        for market in markets:
            if market["id"] == market_id:
                return market
        raise AttributeError(
            f"the specified market {market_id} doesn't exist"
        ) from None

    def list_orders(self, exchange_obj, symbol):
        """
        provides a list of orders from
        the giben exhange object
        :param exchange_obj: exchange object
        :param: symbol: str a symbol for it: trade_pair.
        :return: list
        """
        return exchange_obj.fetch_orders(symbol=symbol)

    def get_order(self, exchange_obj, order_id, params):
        """
        gets an specific oject on the orders book
        :param exchange_obj: exchange object
        :param order_id: str
        :param params: dict of parameters to pass to the object
        :return: dict
        """
        return exchange_obj.fetch_order(id=order_id, params=params)

    def list_currencies(self, exchange_obj):
        """
        provides a list of currencies available
        for the exchange given
        :param exchange_obj: exchange object
        :return: list
        """
        currencies = exchange_obj.fetch_currencies()
        return [currency for currency in currencies.values()]

    def list_ohlcvs(
        self,
        exchange_obj,
        symbol,
        timeframe="1m",
        since=None,
        limit=None,
        params={},
    ):
        """
        gets all  ohlcv values for the
        given exchange with the given filters
        :param exchange_obj: exchange object
        :param symbol: identifier of the exhange or coin
        :param timeframe: time elapsed between entrance and value generated
        :param since: date to get from
        :param limit: date to get to
        :param params: dict, additional params for the fetching
        :return: dict
        """
        assert isinstance(since, int)
        assert isinstance(limit, int)
        return exchange_obj.fetch_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            since=since,
            limit=limit,
            params=params,
        )

    def get_ohlcv(
        self,
        exchange_obj,
        symbol,
        timeframe="1m",
        since=None,
        limit=None,
        params={},
    ):
        """
        gets the ohlcv values for the
        given exchange
        :param exchange_obj: exchange object
        :param symbol: identifier of the exhange or coin
        :param timeframe: time elapsed between entrance and value generated
        :param since: date to get from
        :param limit: date to get to
        :param params: dict, additional params for the fetching
        :return: dict
        """
        return exchange_obj.fetch_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            since=since,
            limit=limit,
            params=params,
        )

    def parse_ohlcv(self, exchange_obj, ohlcv):
        """
        parces the ohlcv values for the
         given exchange
        :param exchange_obj: exchange object
        :param ohlcv: ohlcv indication
        :return: dict
        """
        return exchange_obj.parse_ohlcv(ohlcv=ohlcv)

    def parse_ohlcvs(
        self,
        exchange_obj,
        ohlcvs,
        market=None,
        timeframe="1m",
        since=None,
        limit=None,
    ):
        """
        parses all of the ohlcvs that matches the given filters
        based on the given exchange
        :param exchange_obj: exchange objects
        :param ohlcvs: list of ohlcvs
        :param market: marked selected
        :param timeframe: frequency of how hold it will get to load the intervals
        :param since: date to get from
        :param limit:date to get to
        :return: list
        """
        return exchange_obj.parse_ohlcvs(
            ohlcvs=ohlcvs,
            market=market,
            timeframe=timeframe,
            since=since,
            limit=limit,
        )


class GenericExchangeHandler(object):
    """
    this is a generic exchange handler which contains all
    methods to cover based on what we need to accomplish
    between exchanges.

    keys required for the configuration are:
    api_key
    secret

    methods which have a different behavior between
    objects can be modified and overridden.

    This object must not be instanced since this is a base class
    for the methods to cover with the different exchanges.

    symbol == trade pair in other exchanges

    """

    def __init__(self, config):
        self.config = config
        self.validate_config()
        self.api_endpoints = {}
        self.exchange = None

    def validate_config(self):
        """
        verifies if the required params exist in the config dictionary
        :return: error if there's one
        """
        required_config = ["api_key", "secret"]
        config_values = self.config.keys()
        if "api_key" not in config_values or "secret" not in config_values:
            raise AttributeError(
                f"You must provide the configurations required which are: {required_config}"
            )

    def _post(self, url, headers, request_body={}):
        """
        sends a post request with the given params
        :param url: str
        :param headers: dict
        :param params: dict
        :return: dict
        """
        return requests.post(url, headers=headers, data=request_body)

    def _get(self, url, headers, params={}):
        """
        sends a get request with the given params
        :param url: str
        :param headers: dict
        :param params: dict
        :return: dict
        """
        return requests.get(url, headers=headers, params=params)

    def _delete(self, url, headers, request_body={}):
        """
        sends a delete request
        :param url:
        :param headers:
        :param request_body:
        :return: dict
        """
        return requests.delete(url=url, headers=headers, data=request_body)

    def process_request(self, url, headers, method, request_body={}):
        """
        applies the method from requests so that it's easier and removes
        reduncancy on the code.
        :param request_body: dict request body
        :param headers: dict: headers for the request
        :param url: url to make the request to
        :param method: str: get, post, delete for now
        :return: json
        """
        flag = False
        # options = ["get", "post", "delete"]
        try:
            response = None
            if method == 'post':
                response = self._post(url=url,
                                      headers=headers,
                                      request_body=request_body
                                      )

            elif method == 'get':
                response = self._get(url=url,
                                     headers=headers,
                                     params=request_body
                                     )

            elif method == 'delete':
                response = self._delete(url=url,
                                        headers=headers,
                                        request_body=request_body
                                        )

            if response.status_code == 200:
                print(response, response.headers, response.text)
                flag = True
                return flag, response.json()

            else:
                result = f"There was an error while trying to process the request " \
                    f"{response.json() if response.status_code!=404 else response.text}," \
                    f" with status {response.status_code}"

                return flag, result

        except Exception as X:
            return flag, f"{X}"


    def validate_required_fields(self, required_fields, request_data):
        """
        evaluates that the given request data has the required fields
        :param required_fields:
        :param request_data:
        :return: tuple
        """
        evaluation, message = (
            False,
            f"the required fields are {required_fields}",
        )
        values_evaluation = all(x for x in request_data.values())
        for field in request_data.keys():
            if field not in required_fields:
                break
        else:
            if values_evaluation:
                evaluation = True
                message = None
        return evaluation, message

    @property
    def nonce(self):
        """
        generates the timestamp needed for the request on the APIs
        :return: str
        """
        return f"{int(round(time.time() * 1000))}"

    @abstractmethod
    def prepare_authentication(self, **kwargs):
        """
        loads the values for the authentication
        in a dict used for the headers of the request

        basically it creates a signature hash that goes
        for the authentication
        :return: dict
        """
        raise NotImplementedError(
            "You must implement this in order to use authenticated endpoints"
        )

    @abstractmethod
    def serialize_data(self, **kwargs):
        """
        formats the data to better management datatype.
        :param kwargs: dict
        :return: dict
        """
        raise NotImplementedError("The method hasn't been implemented")

    @property
    def supported_markets(self):
        """
        lists all supported exchanges for bitfinex
        :return:
        """
        raise NotImplementedError("The method hasn't been implemented")

    @property
    def available_currencies(self):
        """
        lists all supported exchanges for bitfinex
        :return:
        """
        raise NotImplementedError

    def validate_trade_pair(self, trade_pair):
        """
        verifies if the trade_pair provided is actually supported by the
        exchange.
        :param trade_pair: str: trade_pair
        :return: bool
        """
        return trade_pair in self.supported_markets

    @abstractmethod
    def get_orders(self, **kwargs):
        """
        loads the open orders  for the account provided.
        :param trade_pair: trade_pair to use or market, it must match the existing ones
        :param since: timestamp
        :param limit: int which determines how many records is going to return
        :param params: dict: additional parameters to the request
        :return: list
        """
        raise NotImplementedError("The method hasn't been implemented")

    @abstractmethod
    def get_order(self, **kwargs):
        """
        loads the order provided.
        :param order_id: str
        :return: dict
        the accepted params for this are:
        trade_pair: trade_pair to use or market, it must match the existing ones
        since: timestamp
        limit: int which determines how many records is going to return
        """
        raise NotImplementedError("The method hasn't been implemented")

    @abstractmethod
    def get_order_status(self, **kwargs):
        """
        :param trade_pair: str: trade_pair

        :param order_id:
        :return:
        """
        raise NotImplementedError("The method hasn't been implemented")

    @abstractmethod
    def submit_order(self, order_data):
        """
        :param trade_pair: str: trade_pair

        :param order_data:
        :return:
        """
        raise NotImplementedError("The method hasn't been implemented")

    @abstractmethod
    def sell_order(self, order_data):
        """
        :param trade_pair: str: trade_pair

        :param order_data:
        :return:
        """
        raise NotImplementedError("The method hasn't been implemented")

    @abstractmethod
    def buy_order(self, order_data):
        """
        :param trade_pair: str: trade_pair
        :param order_data:
        :return:
        """
        raise NotImplementedError("The method hasn't been implemented")

    @abstractmethod
    def cancel_order(self, **kwargs):
        """
        :param trade_pair: str: trade_pair
        :param order_id:
        :return:
        """
        raise NotImplementedError("The method hasn't been implemented")

    def __str__(self):
        return f"<GenericExchangeObject>: {self.exchange}"
