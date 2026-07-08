"""Config loading with env overrides (POLYFLOW_CONFIG points to an alternate
settings.json; POLYFLOW_MOCK=1 forces the offline mock API everywhere)."""
import json
import os

from .paths import CONFIG_PATH


def load_config() -> dict:
    with open(CONFIG_PATH) as fh:
        cfg = json.load(fh)
    if os.environ.get("POLYFLOW_MOCK") == "1":
        cfg["mock_api"] = True
    if os.environ.get("POLYFLOW_DRY_RUN") == "1":
        cfg["execution"]["dry_run"] = True
    return cfg
