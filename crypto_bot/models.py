import json
import logging
import pdb

from django.db import models


logger = logging.getLogger(__name__)


EXCHANGES = [
    ("plx", "ploniex"),
    ("kr", "kraken"),
    ("btx", "bittrex"),
    ("gdx", "gdax"),
    ("bn", "binance"),
    ("cry", "cryptoia"),
    ("bit", "bitfinex"),
    ("kc", "kucoin"),
    ("cx", "cexio"),
    ("hi", "htbtc"),
]


class BaseModel(models.Model):
    class Meta:
        abstract = True

    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True)


class Hooper(BaseModel):
    exchange = models.CharField(
        max_length=10, choices=EXCHANGES, default=EXCHANGES[4]
    )
    base_currency = models.CharField(max_length=100)
    name = models.CharField(max_length=200)
    buying_enabled = models.IntegerField()
    start_balance = models.FloatField()
    enabled = models.BooleanField(default=True)
    selling_enabled = models.BooleanField(default=False)


class HooperConfiguration(BaseModel):
    strategies = [
        ("N", "none"),
        ("bba", "bbands_easy"),
        ("rsi", "rsi"),
        ("fr", "fixed_rates"),
    ]
    tickets = [
        ("hga", "highest_bid_lowest_ask"),
        ("ltl", "last_tick_if_higher_lower"),
        ("alt", "always_last_tick"),
    ]
    hooper = models.ForeignKey(Hooper, on_delete=models.CASCADE)
    exchange = models.CharField(
        max_length=10, choices=EXCHANGES, default=EXCHANGES[4]
    )
    base_currency = models.CharField(max_length=10)
    selected_coins = models.CharField(max_length=10)
    strategy = models.CharField(
        max_length=10, choices=strategies, default=strategies[0]
    )
    sell_with_strategy = models.IntegerField()
    targets_to_buy = models.IntegerField()
    pct_profit = models.IntegerField()
    ticket_rate = models.CharField(
        max_length=5, choices=tickets, default=tickets[0]
    )
    cool_down = models.IntegerField()
    one_open_order_coin = models.IntegerField()
    pct_lower_bid = models.IntegerField()
    pct_higher_ask = models.IntegerField()
    stop_loss_pct = models.IntegerField()
    trailing_stop_loss = models.IntegerField()
    trailing_stop_loss_pct = models.IntegerField()


class HopperPool(BaseModel):
    hopper_config = models.ForeignKey(
        HooperConfiguration, on_delete=models.CASCADE
    )
    pool_name = models.CharField(max_length=100)
    exchange = models.CharField(
        max_length=10, choices=EXCHANGES, default=EXCHANGES[4]
    )
    base_currency = models.CharField(max_length=10)
    selected_coins = models.CharField(max_length=10)
    enabled = models.IntegerField()


class HopperTemplate(BaseModel):
    hooper = models.ForeignKey(Hooper, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=100)


class HooperPosition(BaseModel):
    hooper = models.ForeignKey(Hooper, on_delete=models.CASCADE)
    take_profit = models.IntegerField()
    stop_loss = models.IntegerField()
    stop_loss_percentage = models.IntegerField()
    trailing_stop_loss = models.IntegerField()
    trailing_stop_loss_percentage = models.FloatField()
    trailing_stop_loss_arm = models.IntegerField()
    auto_close = models.IntegerField()
    auto_close_time = models.IntegerField()


class Strategy(BaseModel):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    image = models.CharField(max_length=100)
    min_buys = models.IntegerField()
    min_sells = models.IntegerField()


class StrategyConfiguration(BaseModel):
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    chartperiod = models.CharField(max_length=100)
    params = models.CharField(max_length=100)
    config_type = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    signal_when = models.CharField(max_length=100)
    signal_when_value = models.CharField(max_length=100)
    candle_value = models.CharField(max_length=100)
    candle_pattern = models.CharField(max_length=100)
    keep_signal = models.CharField(max_length=100)


class DataHistory(BaseModel):

    currency = models.CharField(max_length=100)
    time_open = models.DateField()
    time_close = models.DateField()
    time_high = models.DateField()
    time_low = models.DateField()
    open = models.DecimalField(decimal_places=10, max_digits=255)
    high = models.DecimalField(decimal_places=10, max_digits=255)
    low = models.DecimalField(decimal_places=10, max_digits=255)
    close = models.DecimalField(decimal_places=10, max_digits=255)
    volume = models.DecimalField(decimal_places=10, max_digits=255)
    market_cap = models.DecimalField(decimal_places=10, max_digits=255)


# ~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+
# cctx models for the feed.
# ~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+


# works with the rest of the exchanges, need to find out if it accepts bitfinex as well.
class Order(BaseModel):
    order_status = [("open", "open"), ("closed", "closed"), ("cx", "canceled")]
    order_types = [("lm", "limit"), ("mk", "market")]
    order_sides = [("buy", "buy"), ("sell", "sell")]

    order_id = models.CharField(blank=True, max_length=255)
    order_datetime = models.DateTimeField(null=True)
    order_timestamp = models.CharField(blank=True, max_length=255)
    status = models.CharField(
        max_length=255, choices=order_status, default=order_status[0]
    )
    symbol = models.CharField(blank=True, max_length=100)
    side = models.CharField(
        max_length=255, choices=order_sides, default=order_sides[0]
    )
    price = models.DecimalField(decimal_places=10, null=True, max_digits=255)
    amount = models.DecimalField(decimal_places=10, max_digits=255)
    filled = models.DecimalField(null=True, decimal_places=10, max_digits=255)
    remaining = models.DecimalField(
        decimal_places=10, null=True, max_digits=255
    )
    cost = models.DecimalField(null=True, decimal_places=10, max_digits=255)
    trades = models.TextField(default="[]")
    fee = models.TextField(default="{}")
    info = models.TextField(default="{}")


class Market(BaseModel):
    market_id = models.CharField(max_length=20)
    symbol = models.CharField(max_length=20)
    base = models.CharField(max_length=20)
    base_id = models.CharField(max_length=20)
    quote_id = models.CharField(max_length=20)
    active = models.BooleanField()
    taker = models.DecimalField(decimal_places=10, null=True, max_digits=255)
    maker = models.DecimalField(decimal_places=10, null=True, max_digits=255)
    percentage = models.BooleanField()
    info = models.TextField()


class MarketPrecision(BaseModel):
    market = models.ForeignKey(Market, on_delete=models.CASCADE)
    price = models.IntegerField(blank=True)
    amount = models.IntegerField(blank=True)
    cost = models.IntegerField(blank=True)


class MarketLimits(BaseModel):
    market = models.ForeignKey(Market, on_delete=models.CASCADE)
    min_amount = models.DecimalField(
        null=True, decimal_places=5, max_digits=20
    )
    max_amount = models.DecimalField(decimal_places=5, max_digits=20)


class MarketPrice(BaseModel):
    market = models.ForeignKey(Market, on_delete=models.CASCADE)
    min_amount = models.DecimalField(
        null=True, decimal_places=5, max_digits=20
    )
    max_amount = models.DecimalField(
        decimal_places=5, null=True, max_digits=20
    )


class MarketCost(BaseModel):
    market = models.ForeignKey(Market, on_delete=models.CASCADE)
    min_amount = models.DecimalField(
        decimal_places=5, null=True, max_digits=20
    )
    max_amount = models.DecimalField(
        decimal_places=5, null=True, max_digits=20
    )


class Currency(BaseModel):
    currency_id = models.CharField(max_length=20)
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    active = models.BooleanField()
    fee = models.FloatField()
    precision = models.DecimalField(
        decimal_places=10, null=True, max_digits=255
    )


class CurrencyLimits(BaseModel):
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    min_amount = models.DecimalField(
        decimal_places=5, null=True, max_digits=20
    )
    max_amount = models.DecimalField(
        decimal_places=5, null=True, max_digits=20
    )


class CurrencyPrice(BaseModel):
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    min_amount = models.DecimalField(
        decimal_places=5, null=True, max_digits=20
    )
    max_amount = models.DecimalField(
        decimal_places=5, null=True, max_digits=20
    )


class CurrencyCost(BaseModel):
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    min_amount = models.DecimalField(
        decimal_places=5, null=True, max_digits=20
    )
    max_amount = models.DecimalField(
        decimal_places=5, null=True, max_digits=20
    )


class CurrencyWithdrawal(BaseModel):
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    min_amount = models.DecimalField(
        decimal_places=5, null=True, max_digits=20
    )
    max_amount = models.DecimalField(
        decimal_places=5, null=True, max_digits=20
    )


class Ticket(BaseModel):
    symbol = models.CharField(max_length=200)
    info = models.CharField(max_length=200)
    timestamp = models.IntegerField()
    datetime = models.DateTimeField()
    high = models.DecimalField(decimal_places=10, null=True, max_digits=200)
    low = models.DecimalField(decimal_places=10, null=True, max_digits=200)
    bid = models.DecimalField(decimal_places=10, null=True, max_digits=200)
    bid_volume = models.DecimalField(
        decimal_places=10, null=True, max_digits=200
    )
    ask = models.DecimalField(decimal_places=10, null=True, max_digits=200)
    ask_volume = models.DecimalField(
        decimal_places=10, null=True, max_digits=200
    )
    vwap = models.DecimalField(decimal_places=10, null=True, max_digits=200)
    open = models.DecimalField(decimal_places=10, null=True, max_digits=200)
    close = models.DecimalField(decimal_places=10, null=True, max_digits=200)
    last = models.DecimalField(decimal_places=10, null=True, max_digits=200)
    previous_close = models.DecimalField(
        decimal_places=10, null=True, max_digits=200
    )
    change = models.DecimalField(decimal_places=10, null=True, max_digits=200)
    percentage = models.DecimalField(
        decimal_places=10, null=True, max_digits=200
    )
    average = models.DecimalField(decimal_places=10, null=True, max_digits=200)
    base_volume = models.DecimalField(
        decimal_places=10, null=True, max_digits=200
    )
    quote_volume = models.DecimalField(
        decimal_places=10, null=True, max_digits=200
    )


class Exchange(BaseModel):
    name = models.CharField(max_length=255, blank=False, unique=True)

    @classmethod
    def exchange_exists(cls, name):
        if cls.objects.filter(name=name).exists():
            return True
        return False


class OHLCV(BaseModel):
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE)
    timestamp = models.IntegerField()
    open_price = models.DecimalField(
        decimal_places=10, null=True, max_digits=200
    )
    highest_price = models.DecimalField(
        decimal_places=10, null=True, max_digits=200
    )
    lowest_price = models.DecimalField(
        decimal_places=10, null=True, max_digits=200
    )
    closing_price = models.DecimalField(
        decimal_places=10, null=True, max_digits=200
    )
    volume = models.DecimalField(decimal_places=10, null=True, max_digits=200)

    @property
    def o(self):
        return self.open_price

    @property
    def h(self):
        return self.highest_price

    @property
    def l(self):
        return self.lowest_price

    @property
    def c(self):
        return self.closing_price

    @property
    def v(self):
        return self.volume


class Coin(BaseModel):
    coin_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255, unique=True)
    currency = models.CharField(max_length=255, blank=False, default="usd")

    @classmethod
    def coin_exists(cls, coin_id):
        return cls.objects.filter(coin_id=coin_id).exists()

    def __str__(self):
        return f"Coin => {self.name}"


class CoinHistoricalData(BaseModel):
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    meta = models.TextField(default="{}")
    from_date = models.DateTimeField(null=False)
    to_date = models.DateTimeField(null=False)

    def __str__(self):
        name = self.coin.name.capitalize()
        currency = self.coin.currency.capitalize()
        return (
            f"Coin name => {name} | "
            f"Coin currency => {currency} | "
            f"From date => {self.from_date} | To date => {self.to_date}"
        )

    @classmethod
    def does_exist(cls, coin, df, dt):
        """
        verifies if there's a record with the matching
        characters.
        :param coin: coin object
        :param df: datefrom
        :param dt: date to
        :return: bool
        """
        value = coin.coinhistoricaldata_set.filter(from_date=df, to_date=dt)
        return value.exists(), value if value.last() else None


class Contract(BaseModel):
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)

    def __str__(self):
        return f"<ContractObject:CreatedAt:{self.created_at}>"


class Trade(BaseModel):
    def __str__(self):
        return f"<TradeObject:CreatedAt:{self.created_at}>"
