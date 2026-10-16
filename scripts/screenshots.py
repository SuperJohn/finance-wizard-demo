"""Render every page headlessly and save PNGs to docs/screenshots/.
Only run this against synthetic data (the finance-lake-demo build or FW_FIXTURE=1): these images are committed.
    pip install playwright && playwright install chromium
    python scripts/screenshots.py [http://127.0.0.1:8765]"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

PAGES = ["dash", "nw", "cf", "sp", "rec", "run", "scn", "dec", "ano", "an", "goal", "sql"]
base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765"
out = Path(__file__).resolve().parents[1] / "docs" / "screenshots"
out.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    try:
        b = p.chromium.launch(channel="chrome")  # an installed Chrome, if any
    except Exception:
        b = p.chromium.launch()                  # else `playwright install chromium`
    pg = b.new_page(viewport={"width": 1680, "height": 1100}, device_scale_factor=1)
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    src = pg.request.get(f"{base}/api/health").json().get("source", "")
    if not (src == "fixture" or "lake" in src):
        sys.exit(f"refusing to capture: unexpected data source {src!r}")
    for name in PAGES:
        pg.goto(f"{base}/#{name}"); pg.reload(); pg.wait_for_load_state("networkidle"); pg.wait_for_timeout(1500)
        pg.screenshot(path=str(out / f"{name}.png"), full_page=False)
        print(name, "ok")
    print("page errors:", errs)
    b.close()
