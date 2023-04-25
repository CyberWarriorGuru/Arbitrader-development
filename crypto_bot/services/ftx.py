import os
import time
import json
import hmac
import requests
from .ccxt_api import GenericExchangeHandler


class FTXHandler(GenericExchangeHandler):
    """
    Another API wrapper
    capable of taking care of requests, data processing
    and returning the serialized data for futher processing

    this works for FTX exchange

    Still under development.
    """

    def __init__(self, config):
        super().__init__(config)
        self.api_endpoints = {}
