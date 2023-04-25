import logging

from django.conf import settings

from arbitrage.monitor.currency import CurrencyPair
from arbitrage.monitor.exchange.binance import Binance
from arbitrage.monitor.exchange.bitfinex import Bitfinex
from arbitrage.monitor.exchange.bitstamp import Bitstamp
from arbitrage.monitor.exchange.gdax import Gdax
from arbitrage.monitor.update.db_commit import SpreadHistoryToDB
from arbitrage.monitor.update.csv_writer import AbstractSpreadToCSV


BINANCE_API_KEY = settings.BINANCE_API_KEY
BINANCE_SEC_KEY = settings.BINANCE_SEC_KEY
GDAX_KEY = settings.GDAX_KEY
GDAX_SECRET = settings.GDAX_SECRET
GDAX_PASSPHRASE = settings.GDAX_PASSPHRASE


EXCHANGES = [
    Bitfinex(CurrencyPair.BTC_USD),
    Bitstamp(CurrencyPair.BTC_USD),
    Bitstamp(CurrencyPair.ETH_USD),
    Gdax(CurrencyPair.BTC_USD),
    Gdax(CurrencyPair.ETH_USD),
]

TRI_CURRENCY_LIST = [
    ["BNBBTC", "ADABNB", "ADABTC"],
    ["BNBBTC", "ANTBNB", "ANTBTC"],
    ["BNBBTC", "ATOMBNB", "ATOMBTC"],
    ["BNBBTC", "AVABNB", "AVABTC"],
    ["BNBBTC", "AVAXBNB", "AVAXBTC"],
]

TRI_EXCHANGES = [
    {
        "name": "Binance",
        "exchange": Binance(),
        "currenciesList": TRI_CURRENCY_LIST,
    }
]


UPDATE_ACTIONS = [SpreadHistoryToDB()]


UPDATE_INTERVAL = 5  # seconds

TIME_BETWEEN_NOTIFICATIONS = 5 * 60  # Only send a notification every 5 minutes

MINIMUM_SPREAD_TRADING = 200
TRADING_BTC_AMOUNT = 0.5
TRADING_LIMIT_PUFFER = 10  # Fiat Amount
TRADING_ORDER_STATE_UPDATE_INTERVAL = 1
TRADING_TIME_UNTIL_ORDER_CANCELLATION = 30
