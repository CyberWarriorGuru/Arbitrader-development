import datetime
import logging
import io
import os
import pprint

import ccxt

from django.core.management import BaseCommand, CommandError


logger = logging.getLogger(__name__)


this_folder = os.path.dirname(os.path.abspath(__file__))
root_folder = os.path.dirname(os.path.dirname(this_folder))


class Command(BaseCommand):
    """
    Provides capabilities to pull data feed from
    the binance exchange, useful for management, backtesting
    and strategy testing.
    """

    help = "Pull coin data from feed"
    symbols = None
    since = None
    timeframe = None
    limit = None
    exchange = ccxt.binance(config={})

    def add_arguments(self, parser):
        """
        add arguments to the given parser to bind the methods required to
        perform binance operations.
        :param parser: ArgumentParser object
        :return: None
        """
        parser.add_argument("symbols", type=str, help="pair symbols XXX/XXX")
        parser.add_argument(
            "--since", type=str, help="Trade Id to search from"
        )
        parser.add_argument(
            "--timeframe",
            type=str,
            help="Timeframe interval for trades ex: 1m, 1d, ...",
        )
        parser.add_argument(
            "--limit",
            type=int,
            help="Max limit of records, max is 500 (default)",
        )

    def handle(self, **options):
        """
        set defaults variable required to make the whole
        class work.
        :param options: dict
        :return: None
        """
        self.limit = options.get("limit", None)
        self.symbols = options.get("symbols")
        self.since = options.get("since", None)
        self.timeframe = options.get("timeframe", None)
        self.last = self.get_history()

    def get_history(self):
        """
        pulls the historical data related to the
        exchange based on the olhcv values
        :return: dict
        """
        self.stdout.write(
            self.style.SUCCESS(f"Feed {self.exchange.name} => {self.symbols}")
        )
        self.stdout.write(
            self.style.NOTICE("Getting a list of OHLCV candles .. ")
        )

        timeframe = (
            self.timeframe
            if (self.timeframe is not None)
            and (self.timeframe in self.exchange.timeframes)
            else "1d"
        )

        limit = (
            self.limit
            if (self.limit is not None) and (0 > self.limit <= 500)
            else None
        )

        try:
            ohlcv = self.exchange.fetch_ohlcv(
                self.symbols,
                timeframe=timeframe,
                since=self.since,
                limit=limit,
            )
        except Exception as error:
            logger.error(f"Error {str(error)} line # 84")
            exit(1)

        data = {"pair": self.symbols, "trades": []}
        for each in ohlcv:
            data["trades"].append(
                {
                    "time": datetime.datetime.fromtimestamp(each[0] / 1000),
                    "open": each[1],
                    "high": each[2],
                    "low": each[3],
                    "vol": each[4],
                }
            )
        pprint.pprint(data)
        return data
