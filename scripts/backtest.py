import time
#from datetime import datetime
import datetime

import sys
import io
import json
import backtrader as bt
import pprint
import ccxtbt
import backtrader

from ccxtbt import CCXTFeed


def main():
    class TestStrategy(bt.Strategy):
        def __init__(self):
            self.next_runs = 0

        def next(self, dt=None):
            dt = dt or self.datas[0].datetime.datetime(0)
            print('%s closing price: %s' % (dt.isoformat(), self.datas[0].close[0]))
            self.next_runs += 1

    cerebro = bt.Cerebro()

    cerebro.addstrategy(TestStrategy)

    # Add the feed
    t2 = [
        ccxtbt.CCXTFeed(
            exchange=exchange,
            dataname=pair,
            currency='USD',
            config={},
            retries=1,
            historical=True,
            timeframe=backtrader.TimeFrame.Minutes,
            compression=60,
            fromdate=datetime.datetime(2019, 1, 1, 0, 0),
            todate=datetime.datetime(2020, 1, 1, 0, 0),
            ohlcv_limit=1000
        )
        for exchange, pair in [
            (
                'kraken',
                'ETH/USD',
            ),
        ]
    ]
    for t3 in t2:
        t3._fetch_ohlcv()
        assert len(t3._data) > 200
        pprint.pprint(
            dict(
                pair=t3.p.dataname,
                exchange=t3.store.exchange.name,
                amount=len(t3._data),
            )
        )
        t4 = dict(
            data=[o for o in t3._data],
            pair=t3.p.dataname,
            exchange=t3.store.exchange.name,
        )
        t5 = t4['pair']
        with io.open(
            '%s-%s.json' % (
                t4['exchange'],
                '-'.join(t5),
            ),
            'w'
        ) as f:
            json.dump(
                t4,
                f,
            )
        sys.exit(0)


    t1 = CCXTFeed(
        exchange='kraken',
        dataname='ETH/USD',
        timeframe=bt.TimeFrame.Days,
        fromdate=datetime.datetime(2019, 1, 1, 0, 0),
        todate=datetime.datetime(2020, 1, 1, 0, 2),
        compression=1,
        ohlcv_limit=2,
        currency='BNB',
        retries=5,
        historical=True,

        # 'apiKey' and 'secret' are skipped
        config={
            'enableRateLimit': True,
            'nonce': lambda: str(int(time.time() * 1000))
        }
    )
    cerebro.adddata(t1)

    # Run the strategy
    cerebro.run()


if __name__ == '__main__':
    main()
