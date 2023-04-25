import logging

from binance.client import Client

from django.conf import settings

from arbitrage.monitor.currency import CurrencyPair
from arbitrage.monitor.exchange import Exchange, BTCAmount
from arbitrage.monitor.order import Order

from crypto_bot.services.binance import BinanceHandler

logger = logging.getLogger(__name__)


class Binance:
    """
    This is the base adapter for the exchange
    where we implement the services from crypto_bot.service
    """

    name = "Binance"

    def __init__(
        self, key=settings.BINANCE_API_KEY, secret=settings.BINANCE_SEC_KEY
    ):
        self.client = Client(key, secret)
        self.allowed_actions = ["canTrade", "canWhitdraw"]
        self.exchange_feed = None
        self.handler = BinanceHandler(
            config={"api-key": key, "secret": secret}
        )

    def update_prices(self):
        """
        refreshes the prices for the order tickets from the exchange API
        :return: bool
        it returns false in case of an error.
        """
        try:
            self.tickers = self.client.get_orderbook_tickers()
        except Exception as error:
            logger.exception(str(error))
            return False
        return True

    def can_do(self, action: str):
        """
        verifies if the given action can be implemented
        :param action: str
        :return: bool
        """
        flag: bool = False
        try:
            if action not in self.allowed_actions:
                raise Exception("Invalid action {}".format(action))
            flag = self.client.get_account()[action]
        except Exception as error:
            logger.exception(str(error))
            flag = False
        return flag

    def __str__(self):
        return f"{self.name}"

    def create_test_order(self, symbol, side, type, price, quantity):
        """
        creates a test order, this won't be created since it will
        use the test endpoint from the api.
        :param symbol: str
        :param side: str
        :param type: str
        :param price: float
        :param quantity: float
        :return: dict
        """
        order_data = {
            "symbol": symbol,
            "side": side,
            "type": type,
            "price": price,
            "quantity": quantity,
        }

        order = self.handler.submit_order(order_data=order_data, test=True)
        return order


class BinanceAdapter(Exchange):
    """
    native adapter for the binance exchange, basically
    this exchange object provides methods for easier interaction
    with the api and the site.
    """

    currency_pair_api_representation = {
        CurrencyPair.BTC_USD: "BTCUSD",
        CurrencyPair.BTC_EUR: "BTCEUR",
        CurrencyPair.ETH_USD: "ETHUSD",
    }

    def __init__(self, currency_pair: CurrencyPair, binance: Binance):
        super().__init__(currency_pair)
        self.binance = Binance()
        self._depth = self.binance.client.get_order_book(symbol=currency_pair)
        self.last_ask_price = float(self.depth["asks"][0][0])
        self.last_bid_price = float(self.depth["bids"][0][0])

    @property
    def depth(self):
        """
        returns the depth
        :return: int
        """
        return self._depth

    @depth.setter
    def depth(self, value):
        """
        sets the depth for the exchange object
        :param value: int
        :return: None
        """
        self._depth = value

    @property
    def ticker_url(self):
        """
        build an url for the tickets managed by the exchange
        :return: str
        """
        return (
            f"{self.base_url}/pubticker/"
            f"{self.currency_pair_api_representation[self.currency_pair]}"
        )

    def place_test_order(
        self, quantity: BTCAmount, trade_pair, side, type, price
    ):
        """
        creates a test order to verify the parameters
        this doesn't create an order in the exchange
        :param quantity:  int the amount of coins to use.
        :param trade_pair: str: trading pair used in order to make the offer
        :param side: str: sell or buy
        :param type: str: type of order: limit, market, limit_buy, limit_sell
        :param price: float: price for the order
        :return: bool

        returns false if there's any type of error
        """
        try:
            self.binance.create_test_order(
                symbol=trade_pair,
                side=side,
                type=type,
                quantity=quantity,
                price=price,
            )
        except Exception as error:
            logger.exception(str(error))
            return False
        return True

    def get_active_orders(self, trade_pair, since=None, limit=None, params={}):
        """
        gets all active orders for the given symbol
        :param trade_pair: str: trade_pair to use
        :return: generator
        """
        orders = self.binance.handler.get_orders(
            symbol=trade_pair, since=since, limit=limit, params=params
        )
        return (self.process_order(order) for order in orders)

    def get_history_orders(self, trade_pair, since, limit=None, params={}):
        """
        gets all orders despite the status based on the given params
        :param trade_pair:  symbol
        :param since: datetime
        :param limit: int
        :param params: dict: additional parameters
        :return: generator
        """
        orders = self.binance.handler.get_orders_history(
            symbol=trade_pair, since=since, limit=limit, params=params
        )
        return (self.process_order(order) for order in orders)

    def get_order(self, trade_pair, order_id):
        """
        retrieves the order with the matching params
        :param trade_pair: str
        :param order_id: int
        :return: Order Object
        """
        order = self.binance.handler.get_order(
            symbol=trade_pair, order_id=order_id
        )
        return self.process_order(order)

    def process_order(self, order_data):
        """
        serializes the given dict
        and turns it in an Order object
        :param order_data: dict
        :return: Order Object
        """
        return Order(
            exchange=self, order_id=order_data["id"], api_data=order_data
        )

    def _submit_order(self, order_data, option, limit):
        """
        processes the order operation based on the given params.
        :param order_data:
        :param option: str: options available are: buy, sell, sell_limit,
                            buy_limit.
        :param limit: bool: determines if it's a limit option or not
        :return: order object
        """
        # ops = {
        #     "sell": self.binance.handler.sell_order,
        #     "buy": self.binance.handler.buy_order,
        # }
        # error = "Invalid option"
        # assert option in ops.keys(), error
        # return self.process_order(
        #     ops[option](order_data=order_data, limit=limit)
        # )

        ops = {
            "sell": self.binance.handler.sell_order,
            "buy": self.binance.handler.buy_order,
        }
        error = "Invalid option"
        flag = False
        result = None
        try:
            result =  self.process_order(
                ops[option](order_data=order_data, limit=limit)
            )

        except KeyError as K:
            error += f": {K}: the option {option} is not valid, the only valid ones are {opts.keys()}"
            result = error

        except ConnectionError as CT:
            error = f"Connection Error: {CT}"
            result = error

        except Exception as NotIdentifedError:
            error = f"{NotIdentifedError}"
            result = error

        finally:
            return flag, result

    def buy_order(self, order_data):
        """
        makes a buy order with the given data
        :param order_data: dict
        :return: Order object
        """
        return self._submit_order(
            order_data=order_data, option="buy", limit=False
        )

    def sell_order(self, order_data):
        """
        creates a sell order with the given params.
        :param order_data: dict
        :return: Order object
        """
        return self._submit_order(
            order_data=order_data, option="sell", limit=False
        )

    def buy_order_limit(self, order_data):
        """
        creates a buy order with limit params.
        if the limit params aren't provided, it will raise an Exception
        :param order_data: dict
        :return: Order object
        """
        return self._submit_order(
            order_data=order_data, option="buy", limit=True
        )

    def sell_order_limit(self, order_data):
        """
        creates a sell order with limit params.
        if the limit params aren't provided, it will raise an Exception
        :param order_data: dict
        :return: Order object
        """
        return self._submit_order(
            order_data=order_data, option="sell", limit=True
        )

    def cancel_order(self, trade_pair, order_id=None, all=False):
        """
        cancel the provided order
        :param trade_pair: symbol: str
        :param order_id: int
        :param all: bool: flag that determines if it cancels all
                    orders for the given currency
        :return: list
        """
        timestamp = self.binance.handler.nonce
        result = None
        error = "Invalid order"
        flag = False
        try:
            if not all:
                result = [
                    self.process_order(
                        self.binance.handler.cancel_order(
                            symbol=trade_pair, order_id=order_id
                        )
                    )
                ]
            else:
                result = [
                    self.process_order(order)
                    for order in self.binance.handler.cancel_all_orders(
                        symbol=trade_pair, timestamp=timestamp
                    )
                ]
            flag = True
            return flag, result

        except Exception as X:
            return flag, f"{error}: {X}"


    def get_order_status(self, order_id, trade_pair):
        """
        gets the status of the given order ID
        :param order_id: int
        :param trade_pair: str
        :return: str
        """
        return self.binance.handler.get_order_status(
            trade_pair=trade_pair, order_id=order_id
        )
