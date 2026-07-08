"""Automatic logging for every script in this project.

Configured once per interpreter, as an import side effect (core/__init__.py
imports this module, and sitecustomize.py at the project root triggers it for
any python started by cron with PYTHONPATH pointing at the project). Scripts
themselves only ever call logging.info / logging.error.

Everything goes to one .txt file per day for the whole project
(logs/project_one_YYYYMMDD.txt) plus stdout, so the daily file is a readable
overview: run start/end lines with durations, primary information per step,
errors with tracebacks, and claude notes.
"""
import atexit
import datetime
import logging
import os
import sys
import time

from .paths import LOG_DIR

PROJECT_TAG = "project_one"


class ScriptFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, "script"):
            record.script = os.path.basename(sys.argv[0] or "interactive").replace(".py", "")
        return True


def configure_logging():
    root = logging.getLogger()
    if getattr(root, "_polyflow_configured", False):
        return
    root._polyflow_configured = True
    root.setLevel(logging.INFO)

    fname = LOG_DIR / f"{PROJECT_TAG}_{datetime.datetime.utcnow():%Y%m%d}.txt"
    formatter = logging.Formatter(
        "%(asctime)s - %(script)22s - %(levelname)7s - %(message)s",
        datefmt="%y%m%d %H:%M:%S",
    )
    fh = logging.FileHandler(fname)
    sh = logging.StreamHandler(sys.stdout)
    for handler in (fh, sh):
        handler.setFormatter(formatter)
        handler.addFilter(ScriptFilter())
        root.addHandler(handler)

    script = os.path.basename(sys.argv[0] or "interactive").replace(".py", "")
    t0 = time.time()
    if script.startswith(("s0", "backtester", "claude")):
        from .versioning import get_version

        logging.info("=== RUN START %s (strategy v%s) ===", script, get_version())

        def _end():
            logging.info("=== RUN END %s (%.1fs) ===", script, time.time() - t0)

        atexit.register(_end)

    def _excepthook(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_tb))

    sys.excepthook = _excepthook


configure_logging()
