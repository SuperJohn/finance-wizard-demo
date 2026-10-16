"""Tiny local JSON store for app state (goals, budgets, overrides, scenarios).
Lives in data/ (gitignored). The lake itself is never written."""
import json
import threading
from . import config

_F = config.DATA_DIR / "app_state.json"
_l = threading.Lock()


def _read():
    return json.loads(_F.read_text()) if _F.exists() else {}


def get(key, default=None):
    with _l:
        return _read().get(key, default)


def put(key, value):
    with _l:
        d = _read(); d[key] = value
        _F.write_text(json.dumps(d, indent=2, default=str))
    return value
