import logging
from abc import ABC, abstractmethod


from arbitrage.monitor import settings
from arbitrage.monitor.exchange import Exchange

logger = logging.getLogger(__name__)


class SpreadABC(ABC):
    @property
    @abstractmethod
    def summary(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def spread_with_currency(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def spread_percentage(self):
        raise NotImplementedError

    @abstractmethod
    def _calculate_spread(self):
        raise NotImplementedError

    @property
    def is_above_trading_thresehold(self) -> bool:
        return self.spread > settings.MINIMUM_SPREAD_TRADING

    def __str__(self):
        return self.summary

    def __repr__(self):
        return self.__str__()
