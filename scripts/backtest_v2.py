from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import json
import pprint
import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])

# Import the backtrader platform
import backtrader as bt


# Create a Stratey
class TestStrategy(bt.Strategy):

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        self.sources = []
        for t1, t2 in enumerate(self.datas):
            t3 = json.loads(t2.p.name)
            self.sources.append(
                dict(
                    index=t1,
                    data=t2,
                    exchange=t3['exchange'],
                    pair=t3['pair']
                )
            )
        pprint.pprint(self.sources)

    def next(self):
        # Simply log the closing price of the series from the reference
        for t1 in self.sources:
            for t2 in self.sources:
                for t3 in self.sources:

                    t4 = t1['pair'][0]
                    t5 = t2['pair'][0]
                    t6 = t3['pair'][0]
                    try:
                        assert t1['pair'][1] == t5
                        assert t2['pair'][1] == t6
                        assert t3['pair'][1] == t4
                    except:
                        continue

                    t7 = [
                        t1['exchange'],
                        t2['exchange'],
                        t3['exchange'],
                    ]

                    t10 = [t1, t2, t3]
                    t8 = [t4, t5, t6]

                    t9 = [
                        o['data'].datetime.datetime(0)
                        for o in t10
                    ]

                    t11 = [
                        dict(
                            mean_price=o['data'].low[0] + o['data'].high[0],
                            volume=o['data'].volume[0],
                        )
                        for o in t10
                    ]

                    pprint.pprint(
                        dict(
                            t7=t7,
                            t8=t8,
                            t9=t9,
                            t11=t11,
                        )
                    )


if __name__ == '__main__':
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(TestStrategy)

    # Datas are in a subfolder of the samples. Need to find where the script is
    # because it could have been called from anywhere
    datapath = os.path.join(
        os.environ.get(
            'PROJECT_ROOT',
            '/app',
        ),
        'deps',
        'backtrader',
        'datas/orcl-1995-2014.txt'
    )

    # Create a Data Feed
    for exchange, trade_pair in [
        ('kraken', 'ETH/USD'),
        ('kraken', 'USD/BTC'),
        ('kraken', 'BTC/ETH'),
    ]:
        t1 = trade_pair.split('/')
        data = bt.feeds.YahooFinanceCSVData(
            dataname=datapath,
            # Do not pass values before this date
            fromdate=datetime.datetime(2000, 1, 1),
            # Do not pass values before this date
            todate=datetime.datetime(2000, 12, 31),
            # Do not pass values after this date
            reverse=False,
            name=json.dumps(
                dict(
                    exchange=exchange,
                    pair=t1
                )
            )
        )
        cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(100000.0)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
