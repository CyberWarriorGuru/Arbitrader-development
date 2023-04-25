import logging


from arbitrage.monitor import settings
from arbitrage.monitor.exchange import Exchange
from arbitrage.monitor.spread_detection import SpreadABC


logger = logging.getLogger(__name__)


class TriSpreadDifferentCurrenciesError(Exception):
    pass


class TriSpreadMissingPriceError(Exception):
    pass


class TriSpreadDetector(SpreadABC):
    def __init__(self, exchange: Exchange, currenciesList: list):
        self.exchange = exchange
        self.currenciesList = currenciesList
        self.spread = self._calculate_spread()

    @property
    def summary(self):
        return f"Tri_Spread: {self.spread_with_currency}"

    @property
    def spread_with_currency(self):
        return f"{self.spread}"

    @property
    def spread_percentage(self):
        return self.spread

    def _calculate_spread(self):

        exch_rate_list = []
        client = self.exchange.client
        sym = self.currenciesList[0]

        # record of buy and sell orders for given symbol
        depth = client.get_order_book(symbol=sym)

        # price one
        price1 = float(depth["bids"][0][0])
        exch_rate_list.append(price1)

        # price two
        try:
            sym = self.currenciesList[1]
            depth = client.get_order_book(symbol=sym)
            price2 = float(depth["asks"][0][0])
            price2 = 1 / price2
            exch_rate_list.append(price2)
        except Exception as error:
            logger.exception(str(error))
            price2 = 0.000000001
            exch_rate_list.append(price2)

        # price three
        sym = self.currenciesList[2]
        depth = client.get_order_book(symbol=sym)
        price3 = float(depth["bids"][0][0])
        exch_rate_list.append(price3)

        rate1 = exch_rate_list[0]
        rate2 = price3 * price2

        if float(rate1) < float(rate2):
            logger.info("[Triangular] Bingo {}".format(self.currenciesList))
        return float(rate2) - float(rate1)
