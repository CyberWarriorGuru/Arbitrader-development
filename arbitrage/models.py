from django.db import models
import json

BTCAmount = float
FiatAmount = float


BTC_USD = "BTC/USD"
BTC_EUR = "BTC/EUR"
BCH_USD = "BCH/USD"
BCH_EUR = "BCH/EUR"
ETH_USD = "ETH/USD"
ETH_EUR = "ETH/EUR"
BNB_BTC = "BNB/BTC"


CurrencyPair = (
    ("BTC_USD", BTC_USD),
    ("BTC_EUR", BTC_EUR),
    ("BCH_USD", BCH_USD),
    ("BCH_EUR", BCH_EUR),
    ("ETH_USD", ETH_USD),
    ("ETH_EUR", ETH_EUR),
    ("BNB_BTC", BNB_BTC),
)


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Exchange(BaseModel):
    class Meta:
        ordering = ["-name"]
        db_table = "exchange"

    name = models.CharField(null=False, max_length=64)
    currency_pair = models.CharField(choices=CurrencyPair, max_length=255)
    last_ask_price = models.FloatField(null=True)
    last_bid_price = models.FloatField(null=True)
    api_data = models.TextField(default="{}")

    @property
    def fiat_symbol(self):
        if self.currency_pair in [BTC_EUR, BCH_EUR, ETH_EUR]:
            return "€"
        elif self.currency_pair in [BTC_USD, BCH_USD, ETH_USD]:
            return "$"
        else:
            return "B"

    @property
    def detailed_data(self):
        """
        loaded information from the
        api in the exchange
        :return: dict
        """
        return json.loads(self.api_data)


class Ticker(BaseModel):
    class Meta:
        ordering = ["exchange", "granularity", "timestamp"]
        db_table = "arbitrage_ticker"

    timestamp = models.FloatField()
    open  = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    volume = models.FloatField()
    exchange = models.CharField(max_length=64)
    trade_pair = models.CharField(max_length=64)
    granularity = models.CharField(max_length=64)


class Spread(BaseModel):
    class Meta:
        ordering = ["-recorded_date"]
        db_table = "spread"

    exchange_buy_id = models.IntegerField()
    exchange_sell_id = models.IntegerField()
    xchange_buy = models.ForeignKey(
        Exchange, on_delete=models.CASCADE, related_name="exchange_buy"
    )
    xchange_sell = models.ForeignKey(
        Exchange, on_delete=models.CASCADE, related_name="exchange_sell"
    )
    recorded_date = models.DateTimeField(auto_now_add=True)
    spread = models.IntegerField(blank=True)

    def save(self, *args, **kwargs):
        self.exchange_buy_id = self.xchange_buy.pk
        self.exchange_sell_id = self.xchange_sell.pk
        super().save(*args, **kwargs)


class Tri_Spread(BaseModel):
    class Meta:
        ordering = ["-recorded_date"]
        db_table = "tri_spread"

    tri_exchange_buy1_id = models.IntegerField()
    tri_exchange_sell_id = models.IntegerField()
    tri_exchange_buy2_id = models.IntegerField()
    tri_xchange_buy1 = models.ForeignKey(
        Exchange, on_delete=models.CASCADE, related_name="tri_exchange_buy1"
    )
    tri_xchange_buy2 = models.ForeignKey(
        Exchange, on_delete=models.CASCADE, related_name="tri_exchange_buy2"
    )
    tri_xchange_sell = models.ForeignKey(
        Exchange, on_delete=models.CASCADE, related_name="tri_exchange_sell"
    )
    recorded_date = models.DateTimeField(auto_now_add=True)
    tri_spread = models.FloatField(blank=True)

    def save(self, *args, **kwargs):
        self.tri_exchange_buy1_id = self.tri_xchange_buy1.pk
        self.tri_exchange_buy2_id = self.tri_xchange_buy2.pk
        self.tri_exchange_sell_id = self.tri_xchange_sell.pk
        super().save(*args, **kwargs)
