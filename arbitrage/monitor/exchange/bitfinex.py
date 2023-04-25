import logging

from django.conf import settings as conf_settings
from arbitrage.monitor.currency import CurrencyPair
from arbitrage.monitor.exchange import Exchange
from arbitrage.monitor.order import Order, OrderState
from crypto_bot.services.bitfinex import BitfinexHandler, hashlib, hmac, time

logger = logging.getLogger(__name__)


class Bitfinex(Exchange):
    """"""

    currency_pair_api_representation = {
        CurrencyPair.BTC_USD: "BTCUSD",
        CurrencyPair.BTC_EUR: "BTCEUR",
        CurrencyPair.ETH_USD: "ETHUSD",
    }
    secret = conf_settings.BITFINEX_SEC
    key = conf_settings.BITFINEX_KEY
    base_url = "https://api.bitfinex.com/v1"
    base_url_v2 = "https://api-pub.bitfinex.com/v2"
    nonce = lambda: str(int(round(time.time() * 1000)))
    handler = BitfinexHandler(config={"api_key": key, "secret": secret})

    def get_head(self, path, body):
        """

        :param path:
        :param body:
        :return:
        """
        nonce = self.nonce()
        signature = f"/api/{path}{nonce}{body}"
        h = hmac.new(self.secret.encode(), signature.encode(), hashlib.sha384)
        signature = h.hexdigest()
        return {
            "bfx-nonce": nonce,
            "bfx-apikey": self.key,
            "bfx-signature": signature,
            "content-type": "application/json",
        }

    @property
    def ticker_url(self):
        """

        :return:
        """
        return (
            f"{self.base_url}/pubticker/"
            f"{self.currency_pair_api_representation[self.currency_pair]}"
        )

    def get_current_platform_status(self):
        """

        :return:
        """
        # url = f"{self.base_url_v2}/platform/status"
        # request = requests.get(url)
        # if request.status_code != 200:
        #     return False
        # status = request.json()[0]
        # if status == 1:
        #     return True
        # return False
        return True if self.handler.api_status == "ACTIVE" else False

    def get_active_orders(self, symbol):
        """
        Get the current active orders.
        :param symbol: a representation of the trade pair
        """
        # body = {}
        # raw_body = json.dumps(body)
        # path = "v2/auth/r/orders"
        # headers = self.get_head(path, raw_body)
        # url = f"https://api.bitfinex.com/{path}"
        # request = requests.post(
        #     url, headers=headers, data=raw_body, verify=True
        # )
        # if request.status_code == 200:
        #     return request.json()
        # return False

        try:
            orders = self.handler.get_orders(trade_pair=symbol)
            return (
                Order(exchange=self, id=order["id"], api_data=order)
                for order in orders
            )
        except Exception as X:
            logger.error(X)
            return f"{X}"

    def get_historical_orders(self, symbol):
        """
        Get the current active orders.
        :param symbol: a representation of the trade pair
        """
        try:
            orders = self.handler.get_orders_history(trade_pair=symbol)
            return (
                Order(exchange=self, id=order["id"], api_data=order)
                for order in orders
            )
        except Exception as X:
            logger.error(X)
            return f"{X}"

    def get_order(self, order_id, symbol, params={}):
        """
        retrieves a given order
        :param order_id: int: id of the order
        :param symbol: trade pair used for it
        :return: Order Object
        """
        try:
            order = self.handler.get_order(
                trade_pair=symbol, order_id=order_id
            )
            return Order(exchange=self, id=order["id"], api_data=order)
        except Exception as X:
            logger.error(X)
            return f"{X}"

    def cancel_order(self, order_id):
        """
        cancels an order
        :param order_id: id of the order to be canceled
        :return: Order obj
        """
        try:
            order = self.handler.cancel_order(order_id=order_id)
            return Order(
                exchange=self,
                id=order["id"],
                api_data=order,
                state=OrderState.CANCELLED,
            )
        except Exception as X:
            logger.error(X)
            return f"{X}"

    def submit_order(self, order_data):
        """
        submits an order to the exchange based on
        the given params
        :param order_data: dict containing all required data.
        :return: json
        """
        try:
            order = self.handler.submit_order(order_data=order_data)
            return Order(
                exchange=self,
                id=order["id"],
                api_data=order,
                state=OrderState.DONE,
            )
        except Exception as X:
            logger.error(X)
            return f"{X}"

    def update_order(self, order_data):
        """
        submits an order to the exchange based on
        the given params
        :param order_data: dict containing all required data.
        :return: json
        """
        try:
            order = self.handler.update_order(order_data=order_data)
            return Order(
                exchange=self,
                id=order["id"],
                api_data=order,
                state=OrderState.DONE,
            )
        except Exception as X:
            logger.error(X)
            return f"{X}"
