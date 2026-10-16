"""Synthetic data (ALL FAKE: fictional merchants and accounts) with the same shape as the finance lake views,
used for tests and as the fallback when no lake is available. Deterministic (seeded)."""
import datetime as dt
import numpy as np
import pandas as pd

MERCHANTS = [
    ("Greenleaf Market", "Groceries", 85, 6), ("FreshCo Grocers", "Groceries", 60, 4),
    ("QuickFuel", "Gas", 55, 4), ("StreamFlix", "Digital Subscriptions", 15.49, 0),
    ("TuneWave Music", "Digital Subscriptions", 11.99, 0), ("CloudBox", "Digital Subscriptions", 20, 0),
    ("ShopStream.com", "Shopping", 45, 2), ("MegaMart", "Shopping", 70, 2),
    ("Taco Truck 22", "Restaurants & Bars", 18, 3), ("Blue Door Cafe", "Restaurants & Bars", 42, 2),
    ("City Power & Light", "Gas & Electric", 140, 0), ("Nimbus Mobile", "Phone", 85, 0), ("IronPeak Gym", "Fitness", 39.99, 0),
]


def build(seed: int = 7):
    rng = np.random.default_rng(seed)
    start, end = dt.date(2024, 1, 1), dt.date(2026, 10, 12)
    days = pd.date_range(start, end, freq="D")
    rows = []
    for d in days:
        for m, cat, amt, per_month in MERCHANTS:
            if per_month == 0:
                if d.day == (hash(m) % 27) + 1:
                    rows.append((d.date(), m, cat, "Checking (...0001)", -amt, None))
            elif rng.random() < per_month / 30:
                rows.append((d.date(), m, cat, "Card (...0003)", -round(float(rng.lognormal(np.log(amt), 0.4)), 2), None))
        if d.day in (1, 15):
            rows.append((d.date(), "Acme Analytics Payroll", "Paychecks", "Checking (...0001)", 4200.0, None))
        if d.day == 3:
            rows.append((d.date(), "Card Payment", "Credit Card Payment", "Checking (...0001)", -1500.0, None))
    rows.append((dt.date(2026, 5, 2), "Brightline Electronics", "Electronics", "Card (...0003)", -3499.0, None))
    rows.append((dt.date(2026, 5, 20), "MegaMart", "Shopping", "Card (...0003)", 120.0, None))  # refund
    tx = pd.DataFrame(rows, columns=["date", "merchant", "category", "account", "amount", "tags"])
    tx["notes"] = None
    tx["txn_id"] = [f"fx{i}" for i in range(len(tx))]
    bal = []
    for d in pd.date_range("2025-01-01", end, freq="D"):
        t = (d - pd.Timestamp("2025-01-01")).days
        bal.append((d.date(), "Checking (...0001)", 30000 - 5 * t))
        bal.append((d.date(), "Brokerage (...0004)", 60000 + 30 * t + 4000 * np.sin(t / 40)))
        bal.append((d.date(), "Card (...0003)", -2500.0))
    b = pd.DataFrame(bal, columns=["date", "account", "balance"])
    return tx, b
