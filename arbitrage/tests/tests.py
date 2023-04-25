import logging
import os
import pdb
import datetime as dt

import ccxt

from config.settings import get_env_var
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import User
from arbitrage.api import views
from arbitrage.monitor.currency import CurrencyPair
from arbitrage.monitor.settings import Bitfinex


class TestBitFinex(TestCase):
    def setUp(self):
        self.exchange = Bitfinex(CurrencyPair.ETH_USD)

    def test_platform_status(self):
        self.exchange.get_current_platform_status()


class TestBitStamp(TestCase):
    def setUp(self):
        pass


class TestGdax(TestCase):
    def setUp(self):
        pass
