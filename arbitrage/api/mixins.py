import logging
import os
import psutil
import sys

from crypto_bot.management.commands.feed_exchange_history import Command

from django.conf import settings


logger = logging.getLogger(__name__)


class MonitorMixin(object):
    """
    Mixin helper that takes care
    of the operations needed
    to make the monitor work
    and updates the prices required for
    the site.

    """
    def get_file(self, username, filename):
        """ Helper to get a file to deposit the process id of the monitor. """
        path = settings.BASE_DIR / "monitor_ref" / username

        if not os.path.exists(path):
            os.makedirs(path)
        else:
            pass

        file_path = path / filename

        if not os.path.exists(file_path):
            os.system(f"touch {file_path}")

        return file_path

    def start_monitor(self, **kwargs):
        """
        Starts a monitor
        :param kwargs: dict
        :return: bool

        required kwargs requirements:
        -user: username trying to activate the monitor
        -monitor: type of monitor to use
        -file: configuration file to use
        """
        try:

            username = kwargs["user"]
            monitor = kwargs["monitor"]
            file_name = kwargs["file"]

            file = self.get_file(username, file_name)

            args = [sys.executable, "manage.py", "startmonitor", monitor]

            with open(file, "r") as ts:
                try:
                    pid = ts.readlines()[0]
                    pid = psutil.Process(pid=int(pid))
                    pid.terminate()
                except psutil.NoSuchProcess:
                    pass
                except Exception as error:
                    logger.exception(str(error))
                    pass

            with open(file, "w") as ts:
                proc = psutil.Popen(args)
                ts.write(str(proc.pid))

        except Exception as error:
            logger.exception(str(error))
            return False

        return True

    def stop_monitor(self, username, file):
        """
        Stops the monitor by killing the process
        :param username: str: current user using the monitor
        :param file: str: path
        :return: bool
        """
        try:
            file = self.get_file(username, file)

            with open(file, "r") as ts:
                pid = ts.readlines()[0]
                pid = int(pid)

            proc = psutil.Process(pid=pid)
            logger.info(msg=f"Shutting down monitor process {proc.pid}")
            proc.terminate()

        except Exception as error:
            logger.exception(str(error))
            return False

        return True


class BackTestingMixin(object):
    """
    this mixin will help to process and serve
    the data required in order to get historical
    data related to the given exchange and coin
    """

    command_obj = Command()

    def load_data(self, option, **params):
        """
        loads the data by default to the database and returns the
        values provided
        :param option: string, basically the supported options
        :param params: the params required for the command to provide the data
        :return: list
        """
        list_exchanges = self.command_obj.list_exchanges
        ltpbe = self.command_obj.list_trade_pairs_by_exchange
        lgtpo = self.command_obj.list_general_trade_pair_ohlcv
        letpo = self.command_obj.list_exchange_trade_pair_ohlcv

        available_options = {
            "list_exchanges": list_exchanges,
            "list_trade_pair_by_exchange": ltpbe,
            "list_general_trade_pair_ohlcv": lgtpo,
            "list_exchange_trade_pair_ohlcv": letpo,
        }

        return available_options[option](params)
