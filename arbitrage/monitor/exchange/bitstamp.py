import logging


from arbitrage.monitor.currency import CurrencyPair, FiatAmount
from arbitrage.monitor.exchange import Exchange, BTCAmount
from arbitrage.monitor.order import Order, OrderState, OrderId
from crypto_bot.services.bitstamp import BitStampHandler
from django.conf import settings as conf_settings

logger = logging.getLogger(__name__)


class Bitstamp(Exchange):
    base_url = "https://www.bitstamp.net/api/v2"

    currency_pair_api_representation = {
        CurrencyPair.BTC_USD: "btcusd",
        CurrencyPair.BTC_EUR: "btceur",
        CurrencyPair.ETH_USD: "ethusd",
        CurrencyPair.ETH_EUR: "etheur",
    }
    secret = conf_settings.BITSTAMP_SECRET
    key = conf_settings.BITSTAMP_KEY
    user = conf_settings.BITSTAMP_USERNAME
    user_id = conf_settings.BITSTAMP_USER_ID
    handler = BitStampHandler(
        config={
            "apit_key": key,
            "secret": secret,
            "customer_username": user,
            "customer_id": user_id,
        }
    )

    @property
    def ticker_url(self):
        return (
            f"{self.base_url}/ticker/"
            f"{self.currency_pair_api_representation[self.currency_pair]}"
        )

    def get_account_balance(self, base: str, quote: str) -> FiatAmount:
        return self.handler.get_account_balance(base=base, quote=quote)

    def _place_limit_order(
        self,
        side: str,
        amount: BTCAmount,
        limit: float,
        quote: str,
        base: str,
        price: float,
        immediate_or_cancel: bool = False,
    ) -> OrderId:
        """
        creates an order based on the limits provided
        :param side: type of order either sell or buy
        :param amount: how much to use for the order
        :param limit: limit price to sell at
        :param quote: exchange to sell to or buy from
        :param base: exchange to sell from or buy to
        :param price: price of the amount you're selling or buying
        :param immediate_or_cancel: flag to determine that it should
                        be immediately performed or cancelled the order.
        :return: Order object
        """
        order_data = {
            "quote": quote,
            "base": base,
            "ioc_order": immediate_or_cancel,
            "amount": amount,
            "price": price,
            "limit_price": limit,
        }
        try:
            order = (
                self.handler.limit_buy_order(order_data)
                if side == "buy"
                else self.handler.limit_sell_order(order_data)
            )
            return order

        except Exception as X:
            logger.error(f"X")
            return f"There was an error with your request: {X}"

    def _place_market_order(
        self, order_type: str, amount: float, base: str, quote: str
    ) -> OrderId:
        """
        creates a basic order based on the given params
        :param order_type: type of operation to perform: sell or buy
        :param amount: float:how much to use for the order
        :param base: str: exchange to sell to or buy from
        :param quote: str:exchange to sell to or buy from
        :return: dict
        """
        order_data = {"quote": quote, "base": base, "amount": amount}
        try:
            order = (
                self.handler.buy_order(order_data)
                if order_type == "buy"
                else self.handler.sell_order(order_data)
            )
            return order

        except Exception as X:
            logger.error(f"X")
            return f"There was an error with your request: {X}"

    def limit_sell_order(
        self,
        amount: BTCAmount,
        limit: float,
        quote: str,
        base: str,
        price: float,
        immediate_or_cancel: bool = False,
    ) -> Order:
        order = self._place_limit_order(
            "sell",
            amount,
            limit,
            base=base,
            quote=quote,
            price=price,
            immediate_or_cancel=immediate_or_cancel,
        )
        return (
            Order(exchange=self, order_id=order["id"], api_data=order)
            if isinstance(order, dict)
            else order
        )

    def limit_buy_order(
        self,
        amount: BTCAmount,
        limit: float,
        quote: str,
        base: str,
        price: float,
        immediate_or_cancel: bool = False,
    ) -> Order:
        order = self._place_limit_order(
            "buy",
            amount,
            limit,
            base=base,
            quote=quote,
            price=price,
            immediate_or_cancel=immediate_or_cancel,
        )
        return (
            Order(exchange=self, order_id=order["id"], api_data=order)
            if isinstance(order, dict)
            else order
        )

    def market_sell_order(self, amount, base, quote):
        """
         creates a simple sell order for the trade pair
         provided trade_pair = base-quote
        :param amount: float
        :param base: str
        :param quote: str
        :return: Order object
        """
        order = self._place_market_order(
            "sell", amount, base=base, quote=quote
        )
        return (
            Order(exchange=self, order_id=order["id"], api_data=order)
            if isinstance(order, dict)
            else order
        )

    def market_buy_order(self, amount, base, quote):
        """
        creates a simple market buy order for the trade pair
        provided trade_pair = base-quote
        :param amount: float
        :param base: str
        :param quote: str
        :return: Order object
        """
        order = self._place_market_order("buy", amount, base=base, quote=quote)
        return (
            Order(exchange=self, order_id=order["id"], api_data=order)
            if isinstance(order, dict)
            else order
        )

    def get_order_state(self, order: Order) -> OrderState:
        """
        gets an order state based on the existing data
        :param order: Order Object
        :return: dict
        """
        return self.handler.get_order_status(order.id)
