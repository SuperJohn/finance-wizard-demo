import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load_env():
    f = ROOT / ".env"
    if f.exists():
        for line in f.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


_load_env()

DATA_DIR = Path(os.environ.get("FW_DATA_DIR", ROOT / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
LAKE_PATH = Path(os.path.expanduser(os.environ.get("FW_LAKE_PATH") or str(ROOT.parent / "finance-lake-demo" / "lake.duckdb")))
FIXTURE = os.environ.get("FW_FIXTURE", "0") == "1"
HOST = "127.0.0.1"  # localhost only, by design
PORT = int(os.environ.get("FW_PORT", "8765"))
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
MODEL = os.environ.get("FW_MODEL", "gemma3:27b")
CLOUD_BASE_URL = os.environ.get("FW_CLOUD_BASE_URL", "")
CLOUD_API_KEY = os.environ.get("FW_CLOUD_API_KEY", "")
CLOUD_MODEL = os.environ.get("FW_CLOUD_MODEL", "")
