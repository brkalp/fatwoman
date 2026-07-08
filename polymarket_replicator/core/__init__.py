"""Core package for the Polymarket top-trader replicator.

Importing this package configures project logging automatically, so scripts
never call any logging setup themselves - only logging.info / logging.error.
"""
from . import log_setup  # noqa: F401  (import side effect: logging config)
