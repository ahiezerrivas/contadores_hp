import logging
import threading
import time

from django.utils import timezone

logger = logging.getLogger(__name__)

_started = False
_lock = threading.Lock()


def _loop():
    from django.core.management import call_command
    from django.db import close_old_connections

    from .models import ExportSchedule

    last_run_time = None

    while True:
        try:
            close_old_connections()
            schedule = ExportSchedule.get_solo()
            now = timezone.localtime()
            if (
                schedule.enabled
                and last_run_time != schedule.run_time
                and now.time() >= schedule.run_time
            ):
                logger.info("Ejecutando export automatico programado (%s)...", schedule.run_time)
                try:
                    call_command("run_export")
                finally:
                    last_run_time = schedule.run_time
        except Exception:
            logger.exception("Error en el scheduler de export automatico")

        time.sleep(30)


def start():
    global _started
    with _lock:
        if _started:
            return
        _started = True
    thread = threading.Thread(target=_loop, name="export-scheduler", daemon=True)
    thread.start()
