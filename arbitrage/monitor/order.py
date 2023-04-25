from enum import Enum

from ccxt import Exchange

OrderId = str


class OrderState(Enum):
    PENDING = "pending"
    DONE = "done"
    CANCELLED = "cancelled"


class Order:
    def __init__(self, exchange: Exchange, order_id: OrderId, api_data: dict):
        self.exchange = exchange
        self.order_id = order_id
        self.state = OrderState.PENDING
        self.api_data = api_data

    def get_state(self):
        self.state = self.exchange.get_order_state(self)
        return self.state
