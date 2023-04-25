import json
import os
import sys
import warnings
import pprint
import datetime

import ccxt
from django.conf import settings
from django.core.management import BaseCommand, CommandError
from django.utils.timezone import make_aware
from django.conf import settings
import arbitrage.models

from crypto_bot.models import *
from crypto_bot.services.ccxt_api import CCXTApiHandler as handler
from crypto_bot.services.coingecko import CoinGeckoHandler as gecko_handler


LIST_GENERAL_TRADE_PAIR_PARAMS = [
    "coin_id",
    "currency",
    "since",
    "limit",
    "commit",
    "cache",
]


class Command(BaseCommand):
    """
    this class provides capabilities for
    accessing the listed exchanges below and collecting
    the historical data required for backtesting strategies.
    """

    exchanges = [
        "bittrex",
        "binance",
        "bitvavo",
        "kraken",
        #"bytetrade",
        "currencycom",

        "bitfinex",
        "bithumb",
        #"coinbase",
        "ftx",
        "kucoin",
        #"liquid",
        "poloniex",
    ]

    obj_handler = handler()
    obj_handler_gecko = gecko_handler()

    def add_arguments(self, parser):
        """
        adds arguments for the console parser, so that different options required
        with the command are capable of being processed
        :param parser: ArgumentParser object
        :return: None
        """
        parser.add_argument(
            "--list_exchanges",
            help="List exchanges available.",
            action="store_true",
            default=False
        )
        parser.add_argument(
            "--list_trade_pairs",
            help="List trade pairs for a given exchange.",
            action="store_true",
            default=False
        )
        parser.add_argument(
            "--exchange",
            type=str,
            help="Exchange ID (run command with --list_exchanges  "
            "and list_exchange_trade_pair_ohlcv options).",
        )

        parser.add_argument(
            "--list_exchange_trade_pair_ohlcv",
            help="List the ohlcv values for the given trade and exchange.",
            action="store_true",
            default=False
        )

        parser.add_argument(
            "--list_general_trade_pair_ohlcv",
            help="List the general for ohlcv values for the given coin,"
            " trade, exchange and time filters to use from X to X.",
            action="store_true",
            default=False
        )
        parser.add_argument(
            "--populate",
            help="populate",
            action="store_true",
            default=False
        )

        parser.add_argument(
            "--currency",
            help=" currency to gather values from for the provided coin_id, (run only with command "
            "--list_general_trade_pair_ohlcv option)",
        )

        parser.add_argument(
            "--coin_id",
            type=str,
            help="Coin ID (run command with --list_general_trade_pair_ohlcv option).",
        )

        parser.add_argument(
            "--trade_pair",
            type=str,
            help="Trade pair identifier of the exchange (run command with --list_exchange_trade_pair_ohlcv option).",
        )
        parser.add_argument(
            "--time_frame",
            type=str,
            help="<from/since, DDMMYYYY/DDMMYYYY>",
        )
        parser.add_argument(
            "--limit",
            type=int,
            help="timestamp to stop looking to (run command with --list_exchange_trade_pair_ohlcv "
            "and --list_general_trade_pair_ohlcv options).",
        )
        parser.add_argument(
            "--granularity",
            type=str,
            help="specification between records (run command with --list_exchange_trade_pair_ohlcv option).",
        )
        parser.add_argument(
            "--commit",
            help="save the data in the db (run command with --list_exchange_trade_pair_ohlcv and"
            " --list_general_trade_pair_ohlcv options).",
            action="store_true",
            default=False
        )

        parser.add_argument(
            "--cache",
            help="print the data in the terminal (run command with --list_exchange_trade_pair_ohlcv and"
            " --list_general_trade_pair_ohlcv options).",
            action="store_true",
            default=False
        )

    def handle(self, **options):
        """
        handles the commands prompted through the terminal or any type of call
        :param options: dict: dictionary containing the keyword
         arguments needed for the operations
        :return: str or object: it's going to depen which option is passed:
        if --cache: then it prints the string returning none
        if --commit then it saves the record in the model
        """
        if options.get("list_exchanges"):
            t19 = self.list_exchanges()
            print(json.dumps(t19[1]))
        elif (
           options.get("list_trade_pairs")
           and options.get("exchange") is not None
        ):
            exchange = options.get("exchange")
            t1 = self.list_trade_pairs_by_exchange(
                dict(
                    exchange=exchange
                )
            )
            print(json.dumps(t1[1]))
        elif options.get("list_exchange_trade_pair_ohlcv"):
            params = dict(
                trade_pair=options['trade_pair'].split('/')[0:2],
                time_frame=options['time_frame'],
                granularity=options['granularity'],
                exchange=options['exchange'],
                cache=options['cache'],
                commit=options['commit'],
            )

            t3 = self.list_exchange_trade_pair_ohlcv(params=params)
            if not params['commit']:
                print(
                    json.dumps(
                        dict(
                            ticker=[
                                dict(
                                    raw=o,
                                    timestamp=str(datetime.datetime.fromtimestamp(o['timestamp']))
                                )
                                for o in t3[1]
                            ],
                            exchange=params['exchange'],
                            trade_pair=params['trade_pair'],
                        ),
                        indent=4
                    )
                )
        elif options.get("populate"):
            params = dict(
                time_frame=options['time_frame'],
            )
            self.populate(params)
        elif options.get("list_general_trade_pair_ohlcv"):
            for each in LIST_GENERAL_TRADE_PAIR_PARAMS:
                if options.get(each) is None:
                    raise RuntimeError(
                        f"missing {each} param"
                    )

            params = {}
            for p in LIST_GENERAL_TRADE_PAIR_PARAMS:
                params[p] = options.get(p)

            t2 = self.list_general_trade_pair_ohlcv(params=params)
            print(json.dumps(t2[1]))
        else:
            raise NotImplementedError()
        exit(0)

    def list_exchanges(self):
        """
        Lists all exchanges supported by the feed exchange history.
        :return: tuple
        """
        #self.stdout.write(self.style.SUCCESS("Listing available exchanges"))
        #self.stdout.write(self.style.WARNING("---------------------------"))
        #for exchange in self.exchanges:
        #    self.stdout.write(exchange)
        return True, self.exchanges

    def list_trade_pairs_by_exchange(self, params) -> list:
        """
        offers the list of markets based on the given
        exchange provided
        :param params: dict
        :return: list

        Update: fixed so that the error message displays the
        available list of exchanges supported at the moment.
        """
        exchange = params["exchange"]
        exchange = getattr(ccxt, exchange.lower())()
        exchange.load_markets()
        t1 = exchange.markets

        markets = [
            v['symbol']
            for k, v in t1.items()
            if \
                k == v['symbol'] and \
                v['symbol'] == '%s/%s' % (v['base'], v['quote']) and \
                len(v['symbol'].split('/')) == 2 and \
                v['symbol'].split('/')[0] == v['base'] and \
                v['symbol'].split('/')[1] == v['quote']
        ]

        assert len(markets) > 0

        return True, markets

    def list_general_trade_pair_ohlcv(self, params):
        """
        gets the coin data coming from the
        given data which comes with the
        ohlcv values for the given coin

        this one works with coingecko
        :param coin_id: id of the coin to manage in order to pull the data from
        :param currency: the type of currency to pull the data about prices and exchanges values related to the coin
        and exchange provided.
        :param since: timestamp: starting time to pull the data : basically the from in the from ...to: this is a timestamp of a date obj
        :param limit: timestamp: stopping time to pull the data: basically the to in the from ...to: this is a timestamp of a date obj
        :return: list of values or small code.

        before adding more tests, I need to verify if the coin is supported by coingecko so that we don't
        have a problem just adding information that's not really required.

        """
        # Param check
        for key in params.keys():
            if key not in LIST_GENERAL_TRADE_PAIR_PARAMS:
                error = f"Missing {key} param"
                warning.warn(error, UserWarning, stacklevel=2)
                return False, error

        coin_id = params["coin_id"]
        currency = params["currency"]
        t1 = params['time_frame'].split('/')
        date_from = params["since"]
        date_to = params["limit"]
        cache = params["cache"]
        commit = params["commit"]
        df = datetime.datetime.fromtimestamp(date_from)
        dt = datetime.datetime.fromtimestamp(date_to)
        df = make_aware(df)
        dt = make_aware(dt)

        try:
            if coin_id not in self.obj_handler_gecko.supported_coins:
                return (
                    False,
                    f"{coin_id} is not supported, try a different one.",
                )

            coin = (
                Coin.objects.get(coin_id=coin_id)
                if Coin.coin_exists(coin_id)
                else None
            )

            meta = {}
            if not coin:
                coin_values = self.obj_handler_gecko.get_coin(coin_id)
                coin = Coin.objects.create(
                    name=coin_values["name"], coin_id=coin_values["id"]
                )

            exists, return_data = CoinHistoricalData.does_exist(
                coin=coin, df=df, dt=dt
            )
            if not exists:
                _data = self.obj_handler_gecko.get_coin_market_date_range(
                    coin_id=coin.coin_id,
                    currency=currency,
                    date_from=date_from,
                    date_to=date_to,
                )
                data = {}
                for key, value in _data.items():
                    if key != "market_caps":
                        data[key] = value

                # this annotation it's not quite working
                # return_data: CoinHistoricalData = {}

                if "prices" in _data and "total_volumes" in _data:
                    meta = json.dumps(_data)
                else:
                    meta = json.dumps(meta)

            if cache:
                if not exists:
                    return_data = (
                        meta if isinstance(meta, dict) else {"meta": meta}
                    )
                    return_data.update(
                        {"coin": coin_id, "since": date_from, "limit": date_to}
                    )
                #self.stdout.write(self.style.WARNING(return_data))

            elif commit:
                if exists:
                    raise AttributeError("The object already exists")
                else:
                    return_data = coin.coinhistoricaldata_set.create(
                        from_date=df, to_date=dt, meta=meta
                    )
                    # if Coin.objects.filter(
                #     name=coin_id, currency=currency
                # ).exists():
                #     # Get the coin
                #     # coin = Coin.objects.get(name=coin_id, currency=currency)
                #     # if the historical data from that coin does not exists for the
                #     # date range then create it
                #     # basically all process is done here, either exists or not, it creates the coin and the historical
                #     # data then returns the historical data and a flag.
                #     exists, return_data = CoinHistoricalData.exists(coin_name=coin_id, df=df, dt=dt)
                #     # if not CoinHistoricalData.exists(coin=coin, df=df, dt=dt):
                #     #     CoinHistoricalData.objects.create(
                #     #         coin=coin, from_date=df, to_date=dt, meta=meta
                #     #     )
                #     # else:
                #     #     # Just get it here.
                #     #     pass
                #     # # Just get it here or assign it in both inside the if and else.
                #     # return_data = CoinHistoricalData.objects.get(
                #     #     coin=coin, from_date=dt, to_date=dt
                #     # )
                # else:
                #     # Create the coin and the historical data, because without coin
                #     # there is no historical data, so it's safe to assume we need to
                #     # create both here.
                #     coin = Coin.objects.create(name=coin_id, currency=currency)
                #     return_data = CoinHistoricalData.objects.create(
                #         coin=coin, from_date=dt, to_date=df, meta=meta
                #     )
        except Exception as error:
            error = str(error)
            logger.exception(error)
            return False, f"[ERROR] {error}."

        return True, return_data

    def serialize_historical_data(self, value):
        """
        formats the value of the given structure
        changing the timestamps to datetime
        :param value: list of lists
        :return: list of lists
        """
        return [
            [datetime.datetime.fromtimestamp(record[0]), record[1]] for record in value
        ]

    def list_exchange_trade_pair_ohlcv(self, params):
        """
        lists the ohlcv for the given exchange with the given filters
        this one works with cctx
        :param params: dict containing:
            :param trade_pair: identification for the exhange
            :param since: time to start fetching: this is a timestamp of a date obj
            :param limit: time to stop fetching from: this is a timestamp of a date obj
            :param granularity: how long the difference is between records
        :return:json
        """
        t1 = params['time_frame'].split('/')
        t2 = params['exchange']
        t3 = params['trade_pair']
        t4 = datetime.datetime.strptime(t1[0], '%d%m%Y')
        t5 = datetime.datetime.strptime(t1[1], '%d%m%Y')
        t8 = '%s/%s' % (t3[0], t3[1])
        t11 = params['cache']
        t17 = params["granularity"]

        t12 = arbitrage.models.Ticker.objects.all().filter(
            timestamp__gte=t4.timestamp(),
            timestamp__lt=t5.timestamp(),
            exchange=t2,
            trade_pair=t8,
        )
        t14 = t12.count() > 0
        t15 = params['commit']

        if not t11:
            exchange = self.obj_handler.load_exchange_manager(
                exchange=t2,
            )
            t6 = t4
            data = []

            while t6 < t5 and not t14:
                t7 = self.obj_handler.list_ohlcvs(
                    exchange_obj=exchange,
                    symbol=t8,
                    since=int(t6.timestamp()) * 1000,
                    limit=1000,
                    timeframe=t17,
                )
                t10 = [
                    dict(
                        timestamp=int(o[0] / 1000),
                        open=float(o[1]),
                        high=float(o[2]),
                        low=float(o[3]),
                        close=float(o[4]),
                        volume=float(o[5]),
                    )
                    for o in t7
                ]

                if len(t10) == 0:
                    break

                t6 = datetime.datetime.fromtimestamp(
                    t10[-1]['timestamp'] + 1
                )

                if t15:
                    for t9 in t10:
                        t13 = arbitrage.models.Ticker.objects.create(
                            timestamp=t9['timestamp'],
                            open=t9['open'],
                            high=t9['high'],
                            low=t9['low'],
                            close=t9['close'],
                            volume=t9['volume'],
                            exchange=t2,
                            trade_pair=t8,
                            granularity=t17,
                        )
                        t13.save()
                        del t13
                else:
                    data.extend(t10)
        else:
            for o in t12:
                assert o.exchange == t2
                assert o.trade_pair == t8
                assert o.timestamp >= t4.timestamp() and o.timestamp < t5.timestamp()

            data = [
                dict(
                    timestamp=int(o.timestamp),
                    open=float(o.open),
                    high=float(o.high),
                    low=float(o.low),
                    close=float(o.close),
                    volume=float(o.volume),
                )
                for o in t12
            ]

        return True, data

    def populate(self, params):
        t1 = self.list_exchanges()[1]
        t2 = {
            k : self.list_trade_pairs_by_exchange(
                dict(
                    exchange=k,
                )
            )[1]
            for k in t1
        }
        for k, v in t2.items():
            t15 = arbitrage.models.Ticker.objects.all().filter(
                exchange=k,
            )
            t16 = t15.count()
            if t16:
                continue

            for t3 in v:
                for t4 in ['1d', '1h']:
                    pprint.pprint(
                        dict(
                            granularity=t4,
                            exchange=k,
                            trade_pair=t3.split('/')[0:2],
                        )
                    )
                    self.list_exchange_trade_pair_ohlcv(
                        dict(
                            trade_pair=t3.split('/')[0:2],
                            time_frame=params['time_frame'],
                            granularity=t4,
                            exchange=k,
                            cache=False,
                            commit=True,
                        )
                    )
        raise NotImplementedError()
