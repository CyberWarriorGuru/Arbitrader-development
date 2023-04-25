import pdb
import logging
import json
import subprocess
import requests

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from arbitrage.models import Spread, Tri_Spread
from arbitrage.api.mixins import MonitorMixin, BackTestingMixin
from .serializers import (
    ActionSerialier,
    HistoricalDataSerializer,
    serialize_change,
)


logger = logging.getLogger(__name__)


# ~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~
# Spread endpoints.
# ~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~


class TriSpread(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            tri_spreads = []
            for spread in Tri_Spread.objects.all().order_by("-recorded_date"):
                tri_xchange_buy1 = spread.tri_xchange_buy1
                tri_xchange_buy2 = spread.tri_xchange_buy2
                tri_xchange_sell = spread.tri_xchange_sell
                tri_spreads.append(
                    {
                        "id": spread.pk,
                        "tri_exchange_buy1_id": spread.tri_exchange_buy1_id,
                        "tri_exchange_sell_id": spread.tri_exchange_sell_id,
                        "tri_exchange_buy2_id": spread.tri_exchange_buy2_id,
                        "tri_xchange_buy1": serialize_change(tri_xchange_buy1),
                        "tri_xchange_buy2": serialize_change(tri_xchange_buy2),
                        "tri_xchange_sell": serialize_change(tri_xchange_sell),
                        "recorded_date": spread.recorded_date,
                        "tri_spread": spread.tri_spread,
                    }
                )
        except Exception as error:
            logger.exception(str(error))
            return Response({"status": "error"}, status=400)
        return Response({"data": tri_spreads}, status=200)


class InterSpread(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            spreads = []
            for spread in Spread.objects.all().order_by("-recorded_date")[:5]:
                exchange_buy = spread.xchange_buy
                exchange_sell = spread.xchange_sell
                value = {
                    "id": spread.pk,
                    "inter_xchange_buy1": serialize_change(exchange_buy),
                    "inter_xchange_sell": serialize_change(exchange_sell),
                    "recorded_date": spread.recorded_date.ctime(),
                    "inter_spread": spread.spread,
                    "profit": int(spread.spread) > 0,
                }
                spreads.append(value)
        except Exception as error:
            pdb.set_trace()
            logger.exception(str(error))
            return Response({"status": "error"}, status=400)
        return Response({"data": spreads}, status=200)


# ~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~
# Monitor Endpoints
# ~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~


class TriangularMonitor(APIView, MonitorMixin):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        file_name = "triangular_monitor.txt"
        username = request.user.username
        kwargs = {"file": file_name, "monitor": "start_tri", "user": username}

        serializer = ActionSerialier(data=request.data)
        if serializer.is_valid():
            action = serializer.data.get("action")

            if action == "start":
                if self.start_monitor(**kwargs):
                    return Response({"status": "success"}, status=200)
                return Response({"status": "error"}, status=400)

            elif action == "stop":
                if self.stop_monitor(username, file_name):
                    return Response({"status": "success"}, status=200)
                return Response({"status": "success"}, status=200)

            return Response({"status": "error"}, status=400)
        return Response({"status": serializer.errors}, status=400)


class InterExchangeMonitor(APIView, MonitorMixin):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        file_name = "inter_exchange_monitor.txt"
        username = request.user.username
        kwargs = {
            "file": file_name,
            "monitor": "start_inter",
            "user": username,
        }

        serializer = ActionSerialier(data=request.data)
        if serializer.is_valid():
            action = serializer.data.get("action")

            if action == "start":
                if self.start_monitor(**kwargs):
                    return Response({"status": "success"}, status=200)
                pdb.set_trace()
                return Response({"status": "error"}, status=400)

            elif action == "stop":
                if self.stop_monitor(username, file_name):
                    return Response({"status": "success"}, status=200)
                return Response({"status": "error"}, status=400)

            return Response({"status": "error"}, status=400)
        return Response({"status": serializer.errors}, status=400)


# ~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~
# Historical data Endpoints
# Split the endpoints so each one has it's own task.
# ~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~


class ExchangeHistoricalDataView(APIView, BackTestingMixin):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        resulting_data = {}
        serializer = HistoricalDataSerializer(data=request.data)
        if serializer.is_valid():
            option = serializer.data.get("option")
            params = dict(
                start_date=serializer.data.get("start_date"),
                end_date=serializer.data.get("end_date"),
                trade_pair=serializer.data.get("trade_pair"),
                option=serializer.data.get("option"),
                commit=True,
            )
            if option == "list_general_trade_pair_ohlcv":
                params["coin_id"] = params["trade_pair"]

            result, resulting_data = self.load_data(option=option, **params)
            if result:
                return Response(data={"data": resulting_data}, status=200)
        return Response({"error": resulting_data}, status=400)


class FeedExchangeListExchanges(APIView, BackTestingMixin):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        with subprocess.Popen(
            [
                'python3',
                'manage.py',
                'feed_exchange_history',
                '--list_exchanges',
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ) as p:
            t1 = p.communicate()
            t2 = t1[0].decode('utf-8').split("\n")

        return Response(
            data={
                "data": t2
            },
            status=200
        )


class FeedExchangeListTradePairs(APIView, BackTestingMixin):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        res = []
        with subprocess.Popen(
            [
                'python3',
                'manage.py',
                'feed_exchange_history',
                '--list_exchanges',
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ) as p:
            t1 = p.communicate()
            t2 = t1[0].decode('utf-8')
            t20 = json.loads(t2)

        for t3 in t20:
            with subprocess.Popen(
                [
                    'python3',
                    'manage.py',
                    'feed_exchange_history',
                    '--list_trade_pairs',
                    '--exchange',
                    t3,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ) as p:
                t1 = p.communicate()
                t2 = t1[0].decode('utf-8')
                res.append(
                    json.loads(t2)
                )

        return Response(
            data={
                "data": json.dumps(res, indent=4)
            },
            status=200
        )


class FeedExchangeListGeneralTradePairOHLCV(APIView, BackTestingMixin):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        with subprocess.Popen(
            [
                'python3',
                'manage.py',
                'feed_exchange_history',
                '--list_general_trade_pair_ohlcv',
                '--currency',
                'usd',
                '--coin_id',
                'ethereum',
                '--since',
                '1602219600',
                '--limit',
                '1612591200',
                '--commit',
                'false',
                '--cache',
                'false',
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ) as p:
            t1 = p.communicate()
            t2 = t1[0].decode('utf-8')

        return Response(
            data={
                "data": t2
            },
            status=200
        )


class FeedExchangeListExchangeTradePairOHLCV(APIView, BackTestingMixin):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        t4 = ''

        with subprocess.Popen(
            [
                'python3',
                'manage.py',
                'feed_exchange_history',
                '--list_exchanges',
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ) as p:
            t1 = p.communicate()
            t2 = t1[0].decode('utf-8')
            t20 = json.loads(t2)

        for t3 in t20:
            with subprocess.Popen(
                [
                    'python3',
                    'manage.py',
                    'feed_exchange_history',
                    '--list_trade_pairs',
                    '--exchange',
                    t3,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ) as p:
                t1 = p.communicate()
                t2 = t1[0].decode('utf-8')
                t5 = json.loads(t2)[0]

            with subprocess.Popen(
                [
                    'python3',
                    'manage.py',
                    'feed_exchange_history',
                    '--list_exchange_trade_pair_ohlcv',
                    '--trade_pair',
                    t5,
                    '--exchange',
                    t3,
                    '--time_frame',
                    '01012020/01012021',
                    '--granularity',
                    '1d',
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ) as p:
                t1 = p.communicate()
                t2 = t1[0].decode('utf-8')
                t4 += t2

        return Response(
            data={
                "data": t4
            },
            status=200
        )


class HummingbotStart(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        with requests.post(
            "http://hummingbot:1234/start"
        ) as p:
            t1 = p.json()

        return Response(
            data={
                "data": json.dumps(t1)
            },
            status=200
        )

class HummingbotStatus(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        res = []

        with requests.post(
            "http://hummingbot:1234/status"
        ) as p:
            res.append(json.loads(p.text))

        return Response(
            data={
                "data": json.dumps(res)
            },
            status=200
        )

class HummingbotInterexchangeArbitrage(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        res = []

        with requests.post(
            "http://hummingbot:1234/interexchange_arbitrage"
        ) as p:
            res.append(json.loads(p.text))

        return Response(
            data={
                "data": json.dumps(res)
            },
            status=200
        )

class HummingbotTriangularArbitrage(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        res = []

        with requests.post(
            "http://hummingbot:1234/triangular_arbitrage"
        ) as p:
            res.append(json.loads(p.text))

        return Response(
            data={
                "data": json.dumps(res)
            },
            status=200
        )

class HummingbotStop(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        with requests.post(
            "http://hummingbot:1234/stop"
        ) as p:
            t1 = p.json()

        return Response(
            data={
                "data": json.dumps(t1)
            },
            status=200
        )


class BacktestV1(APIView, BackTestingMixin):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        with subprocess.Popen(
            [
                'python3',
                'scripts/backtest.py',
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ) as p:
            t1 = p.communicate()
            t2 = t1[0].decode('utf-8')

        return Response(
            data={
                "data": t2
            },
            status=200
        )


class BacktestV2(APIView, BackTestingMixin):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        with subprocess.Popen(
            [
                'python3',
                'scripts/backtest_v2.py',
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ) as p:
            t1 = p.communicate()
            t2 = t1[0].decode('utf-8')

        return Response(
            data={
                "data": t2
            },
            status=200
        )


class GetAvailableExchanges(APIView, BackTestingMixin):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        result, resulting_data = self.load_data(option="list_exchanges")
        return Response(
            data={"data" if result else "error": resulting_data},
            status=200 if result else 400,
        )


class GetTradePairByExchange(APIView, BackTestingMixin):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        result, resulting_data = self.load_data(
            option="list_trade_pair_by_exchange",
            params={"exchange": data["exchange"]},
        )
        return Response(
            data={"data" if result else "error": resulting_data},
            status=200 if result else 400,
        )
