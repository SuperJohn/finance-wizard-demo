"""CPI-U (US city average, all items, NSA) annual averages, 1982-84=100.
2019-2024 are BLS published annual averages; 2025-2026 are approximations.
Drop a BLS CSV (columns: date,cpi) at data/cpi.csv to override with monthly data."""
import pandas as pd
from . import config

ANNUAL = {2019: 255.657, 2020: 258.811, 2021: 270.970, 2022: 292.655, 2023: 304.702, 2024: 313.689, 2025: 322.2, 2026: 330.5}


def monthly() -> pd.Series:
    f = config.DATA_DIR / "cpi.csv"
    if f.exists():
        d = pd.read_csv(f, parse_dates=["date"])
        return d.set_index(d["date"].dt.to_period("M"))["cpi"]
    pts = pd.Series({pd.Period(f"{y}-07", "M"): v for y, v in ANNUAL.items()})
    idx = pd.period_range("2019-01", "2027-12", freq="M")
    s = pts.reindex(idx).astype(float)
    s = pd.Series(s.values, index=range(len(s))).interpolate(limit_direction="both")
    return pd.Series(s.values, index=idx)


def deflator(base: str | None = None) -> pd.Series:
    s = monthly()
    b = s[pd.Period(base, "M")] if base else s.iloc[-1 - 14]  # ~today
    return s / b
