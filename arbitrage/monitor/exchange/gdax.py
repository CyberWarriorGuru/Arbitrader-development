import base64
import datetime
import hmac
import hashlib
import logging

import requests
from requests.auth import AuthBase

from arbitrage.monitor.currency import CurrencyPair
from arbitrage.monitor.exchange import Exchange, BTCAmount
from arbitrage.monitor.order import Order, OrderState, OrderId


logger = logging.getLogger(__name__)


class GdaxAuth(AuthBase):
    """
    Authentication class
    needed for exchange
    gdax.

    its basic functionality is to make requests to
    the API service and return it
    """
    def __init__(self, key: str, secret: str, passphrase: str):
        self.api_key = key
        self.secret_key = secret
        self.passphrase = passphrase

    def __call__(self, request):
        timestamp = str(datetime.time())
        message = (
            timestamp
            + request.method
            + request.path_url
            + (request.body or "")
        )
        hmac_key = base64.b64decode(self.secret_key)
        signature = hmac.new(hmac_key, message, hashlib.sha256)
        signature_b64 = signature.digest().encode("base64").rstrip("\n")

        request.headers.update(
            {
                "CB-ACCESS-SIGN": signature_b64,
                "CB-ACCESS-TIMESTAMP": timestamp,
                "CB-ACCESS-KEY": self.api_key,
                "CB-ACCESS-PASSPHRASE": self.passphrase,
                "Content-Type": "application/json",
            }
        )
        return request


class Gdax(Exchange):
    """
    Exchange object capable of handling
    order requests for the exchange gdax known
    as coinbasepro.
    """
    base_url = "https://api.gdax.com"

    currency_pair_api_representation = {
        CurrencyPair.BTC_USD: "BTC-USD",
        CurrencyPair.BTC_EUR: "BTC-EUR",
        CurrencyPair.ETH_USD: "ETH-USD",
        CurrencyPair.ETH_EUR: "ETH-EUR",
    }

    def __init__(
        self,
        currency_pair: CurrencyPair,
        api_key: str = "settings.GDAX_KEY",
        secret_key: str = "settings.GDAX_SECRET",
        passphrase: str = "settings.GDAX_PASSPHRASE",
    ):
        super().__init__(currency_pair)
        self.auth = GdaxAuth(api_key, secret_key, passphrase)

    @property
    def ticker_url(self) -> str:
        """
        generates a ticket url for the exchange
        :return: str
        """
        return f"{self.base_url}/products/{self.currency_pair_api_representation[self.currency_pair]}/ticker"

    def _place_limit_order(
        self, side: str, amount: BTCAmount, limit: float
    ) -> OrderId:
        """
        This is a helper used in order to get the
        order request depending on which side you're
        trying to get therefore it works for both
        sell or buy
        :param side: str
        :param amount: float
        :param limit: float
        :return: OrderId
        """
        url = f"{self.base_url}/orders/"
        data = {
            "product_id": self.currency_pair_api_representation.get(
                self.currency_pair
            ),
            "side": side,
            "size": amount,
            "price": limit,
        }
        response = requests.post(url, json=data, auth=self.auth)
        json = response.json()
        order_id = json.get("id")
        return order_id

    def limit_sell_order(self, amount: BTCAmount, limit: float) -> Order:
        """
        create a sell order with a limit amount, this means
        it will sell up until the limit
        :param amount: float
        :param limit: float
        :return: Order object
        """
        order_id = self._place_limit_order("sell", amount, limit)
        return Order(exchange=self, order_id=order_id)

    def limit_buy_order(self, amount: BTCAmount, limit: float) -> Order:
        """
        create a buy order with a limit amount, this means
        it will buy up until the limit
        :param amount: float
        :param limit: float
        :return: Order object
        """
        order_id = self._place_limit_order("buy", amount, limit)
        return Order(exchange=self, order_id=order_id)

    def get_order_state(self, order: Order) -> OrderState:
        """
        retrieves the order state from the given order
        :param order: Order object
        :return: OrderState obj
        """
        url = f"{self.base_url}/orders/{order.order_id}"
        response = requests.get(url, auth=self.auth)

        if response.status_code == 404:
            logger.info(
                f"Order {order} doesn't return a status, it might be cancelled"
            )
            return OrderState.CANCELLED

        state_string = response.json().get("state")

        if state_string in ["done", "settled"]:
            return OrderState.DONE
        elif state_string in ["open", "pending"]:
            return OrderState.PENDING
