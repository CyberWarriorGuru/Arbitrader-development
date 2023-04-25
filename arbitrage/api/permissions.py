import pdb
import psutil

from django.conf import settings
from django.contrib.sessions.backends import file
from rest_framework.permissions import BasePermission


class IsUsingMonitor(BasePermission):

    message = "User is already using the monitor."

    def has_permission(self, request, view):
        """Check various things before making a move."""

        if request.data.get("action") is None:
            return False

        user = request.user
        monitor_file = None
        view_name = view.get_view_name()
        action = request.data.get("action")

        # get the file where the pid of the monitor lives.
        if action == "start":

            if view_name == "Triangular Monitor":
                monitor_file = view.get_file(
                    user.username, "triangular_monitor.txt"
                )

            elif monitor_file == "Inter Exchange Monitor":
                monitor_file = view.get_file(
                    user.username, "inter_exchange_monitor.txt"
                )

            elif monitor_file == "Strategy Backtest Monitor":
                monitor_file = view.get_file(
                    user.username, "strategy_back_test.txt"
                )

            if monitor_file is None:
                return False

            try:
                with open(file, "r") as ts:
                    pid = ts.readlines()[0]
                    pid = int(pid)
            except:  # there is nothing to read or file does not exist
                return True

            try:
                pid = psutil.Process(pid=pid)
            except psutil.NoSuchProcess:  # the process is dead, safe to spawn new.
                return True

            if (
                pid.is_running()
            ):  # if the prvious process is still running, kill it.
                pid.terminate()

        return True
