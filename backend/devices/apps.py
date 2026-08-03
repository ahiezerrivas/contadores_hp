import os
import sys

from django.apps import AppConfig


class DevicesConfig(AppConfig):
    name = 'devices'

    def ready(self):
        if "runserver" not in sys.argv:
            return
        # Evita que el watcher del autoreloader arranque el scheduler dos veces.
        if os.environ.get("RUN_MAIN") != "true" and "--noreload" not in sys.argv:
            return

        from . import scheduler

        scheduler.start()
