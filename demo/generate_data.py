#!/usr/bin/env python3
"""Generate the Finance Lab synthetic demo dataset under demo/data (seeded, deterministic, stdlib only).

Twelve months (2025-11-01 to 2026-10-28) for a fictional person ("Jordan Demo"): accounts, transactions in the
fw.txns shape (txn_id, date, merchant, category, account, amount, tags, notes, kind), weekly balance snapshots in
the fw.balances shape, monthly cash flow and net worth, recurring bills with price creep, budgets, goals, runway
scenarios (Scenarios page shape), transaction notes/labels and a ready-to-use app_state.json. All invented.

    python3 demo/generate_data.py      # -> demo/data/*.json (byte-identical for the same seed)
"""
import hashlib, json
from pathlib import Path


def _enc(o, level=0):
    """Pretty JSON where arrays of objects/arrays put one compact record per line (small, diff-friendly)."""
    pad, pad1 = " " * level, " " * (level + 1)
    if isinstance(o, dict):
        if not o:
            return "{}"
        items = [f'{pad1}{json.dumps(k, ensure_ascii=False)}: {_enc(v, level + 1)}' for k, v in o.items()]
        return "{\n" + ",\n".join(items) + "\n" + pad + "}"
    if isinstance(o, list) and o and all(isinstance(x, (dict, list)) for x in o):
        rows = [pad1 + json.dumps(x, ensure_ascii=False, separators=(", ", ": ")) for x in o]
        return "[\n" + ",\n".join(rows) + "\n" + pad + "]"
    return json.dumps(o, ensure_ascii=False)


def write(path: Path, obj) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = _enc(obj) + "\n"
    json.loads(text)  # must round-trip
    path.write_text(text, encoding="utf-8")
    b = text.encode()
    return {"name": path.name, "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()}
# ---------------------------------------------------------------------------------------------------------------
import argparse
import calendar
import datetime as dt
import random

SEED = 42
START, END = dt.date(2025, 11, 1), dt.date(2026, 10, 28)
PERSONA = "Jordan Demo (fictional)"

# id, display name (fw.balances/fw.txns `account`), institution, type, subtype, klass, last4, opening balance
ACCOUNTS = [
    ("demo-chk", "Demo Bank Checking (...0001)", "Demo Bank", "depository", "checking", "cash", "0001", 6200.0),
    ("demo-sav", "Demo Bank Savings (...0002)", "Demo Bank", "depository", "savings", "cash", "0002", 18500.0),
    ("demo-card", "Demo Rewards Card (...0003)", "Demo Card Co", "credit", "credit card", "liability", "0003", -1850.0),
    ("demo-brk", "Demo Brokerage (...0004)", "Demo Brokerage", "investment", "brokerage", "investment", "0004", 41200.0),
    ("demo-ira", "Demo Roth IRA (...0005)", "Demo Brokerage", "investment", "roth", "investment", "0005", 27800.0),
    ("demo-loan", "Demo Auto Loan (...0006)", "Demo Credit Union", "loan", "auto", "liability", "0006", -14600.0),
    ("demo-car", "Demo Vehicle (est. value)", "Manual", "other", "vehicle", "property", "", 21500.0),
]
ACC = {a[0]: a[1] for a in ACCOUNTS}
CATEGORIES = {
    "Income": ["Paychecks", "Business Income", "Interest", "Dividends & Capital Gains"],
    "Housing": ["Rent", "Gas & Electric", "Internet & Cable", "Renters Insurance"],
    "Food & Dining": ["Groceries", "Restaurants & Bars", "Coffee Shops"],
    "Transportation": ["Gas", "Auto Insurance", "Auto Payment", "Parking & Tolls", "Taxi & Ride Shares"],
    "Shopping": ["Shopping", "Clothing", "Electronics"],
    "Lifestyle": ["Entertainment & Recreation", "Fitness", "Digital Subscriptions", "Travel & Vacation", "Gifts"],
    "Health": ["Medical", "Pharmacy"],
    "Bills": ["Phone"],
    "Transfers": ["Transfer", "Credit Card Payment", "Buy"],
}
# card spending: merchant, category, mean, sd, visits per month, {month: multiplier}
CARD = [
    ("Greenleaf Market", "Groceries", 78, 22, 5.0, {11: 1.25, 12: 1.35}), ("Corner Fresh Grocer", "Groceries", 31, 10, 3.0, {}),
    ("Bluebird Coffee", "Coffee Shops", 6.5, 1.5, 8.0, {}), ("Saffron Table", "Restaurants & Bars", 58, 18, 1.5, {12: 1.6}),
    ("Noodle Theory", "Restaurants & Bars", 24, 6, 2.0, {}), ("Harbor Pizza Co", "Restaurants & Bars", 32, 8, 1.2, {}),
    ("Sunburst Fuel", "Gas", 46, 9, 3.0, {7: 1.3}), ("Maple & Main Goods", "Shopping", 48, 25, 2.0, {11: 1.8, 12: 2.2}),
    ("Everyday Mart", "Shopping", 36, 15, 2.0, {}), ("Thread & Needle", "Clothing", 72, 30, 0.5, {4: 2.0, 9: 1.8}),
    ("ZipRide", "Taxi & Ride Shares", 19, 7, 1.5, {12: 1.5}), ("Oakview Clinic", "Medical", 45, 20, 0.25, {}),
    ("Willow Pharmacy", "Pharmacy", 18, 6, 0.6, {}), ("Petal Post Florist", "Gifts", 55, 15, 0.15, {2: 6.0, 5: 4.0, 12: 5.0}),
    ("Paper Lantern Books", "Entertainment & Recreation", 22, 8, 1.0, {}), ("Starlight Cinemas", "Entertainment & Recreation", 28, 6, 0.8, {}),
    ("Metro Park & Go", "Parking & Tolls", 12, 4, 1.5, {}),
]
# recurring bills: merchant, category, day, [(from, price)], account
SUBS = [
    ("StreamFlix", "Digital Subscriptions", 9, [(START, 17.99), (dt.date(2026, 3, 1), 19.99)], "demo-card"),
    ("TuneBox Music", "Digital Subscriptions", 14, [(START, 11.99)], "demo-card"),
    ("CloudNotes Pro", "Digital Subscriptions", 3, [(START, 10.00)], "demo-card"),
    ("PixelForge Photo", "Digital Subscriptions", 21, [(START, 9.99)], "demo-card"),
    ("Peak Climbing Gym", "Fitness", 1, [(START, 79.00), (dt.date(2026, 1, 1), 85.00)], "demo-card"),
    ("Shieldwell Auto Insurance", "Auto Insurance", 22, [(START, 151.00), (dt.date(2026, 3, 1), 164.00)], "demo-card"),
    ("Hearthstone Renters Insurance", "Renters Insurance", 5, [(START, 14.50)], "demo-card"),
    ("Orbit Mobile", "Phone", 18, [(START, 65.00)], "demo-chk"),
    ("Skyline Internet", "Internet & Cable", 11, [(START, 70.00)], "demo-chk"),
    ("Brightwater Power & Light", "Gas & Electric", 16, None, "demo-chk"),  # seasonal amount
]
RENT = [(START, 2340.0), (dt.date(2026, 8, 1), 2410.0)]
PAY = [(START, 2890.0), (dt.date(2026, 4, 1), 3010.0)]   # semi-monthly net
LOAN_PMT = 412.0
TRIPS = [(dt.date(2025, 12, 19), "Wanderly Air", 402.0, None, 0.0), (dt.date(2026, 7, 10), "Wanderly Air", 476.0, "Seaside Inn", 760.0)]
FREELANCE = [(dt.date(2026, 1, 23), 1800.0), (dt.date(2026, 4, 17), 2400.0), (dt.date(2026, 6, 12), 950.0), (dt.date(2026, 9, 18), 2100.0)]


def _at(sched, d):
    v = sched[0][1]
    for since, x in sched:
        if d >= since:
            v = x
    return v


def build(seed=SEED):
    rng = random.Random(seed)
    tx = []

    def add(d, merchant, category, acct, amount, notes=None, tags=None):
        tx.append({"date": d.isoformat(), "merchant": merchant, "category": category, "account": ACC[acct],
                   "amount": round(amount, 2), "tags": tags or [], "notes": notes})

    d = START
    while d <= END:
        m = d.month
        for merch, cat, mean, sd, per_month, season in CARD:
            if rng.random() < per_month * season.get(m, 1.0) / 30.4:
                add(d, merch, cat, "demo-card", -max(2.5, rng.gauss(mean, sd)))
        if d.day in (1, 15):
            add(d, "Northwind Studio Payroll", "Paychecks", "demo-chk", _at(PAY, d))
        if d.day == 1:
            add(d, "Lakeside Property Mgmt", "Rent", "demo-chk", -_at(RENT, d))
        if d.day == 7:
            add(d, "Demo Credit Union", "Auto Payment", "demo-chk", -LOAN_PMT)
            add(d, "Transfer to Savings", "Transfer", "demo-chk", -600.0)
            add(d, "Transfer from Checking", "Transfer", "demo-sav", 600.0)
        if d.day == 10:
            add(d, "Index Fund Purchase", "Buy", "demo-brk", 0.0, tags=["auto-invest"])
            add(d, "Transfer to Brokerage", "Transfer", "demo-chk", -500.0)
        if d.day == 20 and m in (1, 4, 7, 10):
            add(d, "Roth IRA Contribution", "Transfer", "demo-chk", -1750.0)
        if d.day == 28:
            add(d, "Demo Bank Interest", "Interest", "demo-sav", round(18500 * 0.041 / 12 + rng.uniform(0, 8), 2))
        for merch, cat, day, sched, acct in SUBS:
            if d.day == min(day, calendar.monthrange(d.year, m)[1]):
                if sched is None:
                    amt = 62 + 48 * (1 if m in (12, 1, 2) else 0) + 35 * (1 if m in (7, 8, 9) else 0) + rng.uniform(-9, 9)
                else:
                    amt = _at(sched, d)
                add(d, merch, cat, acct, -amt)
        for td, air, fare, hotel, cost in TRIPS:
            if d == td - dt.timedelta(days=45):
                add(d, air, "Travel & Vacation", "demo-card", -fare, tags=["trip"])
            if hotel and d == td:
                add(d, hotel, "Travel & Vacation", "demo-card", -cost, tags=["trip"])
        for fd, amt in FREELANCE:
            if d == fd:
                add(d, "Halcyon Labs (freelance)", "Business Income", "demo-chk", amt, tags=["freelance"])
        d += dt.timedelta(days=1)
    # one-offs: a big purchase, a refund, a duplicate charge, a fee
    add(dt.date(2026, 5, 2), "Brightline Electronics", "Electronics", "demo-card", -1299.0, tags=["big-purchase"])
    add(dt.date(2026, 5, 20), "Everyday Mart", "Shopping", "demo-card", 64.0, notes="Returned a lamp")
    add(dt.date(2026, 8, 14), "Saffron Table", "Restaurants & Bars", "demo-card", -142.30)
    add(dt.date(2026, 8, 14), "Saffron Table", "Restaurants & Bars", "demo-card", -142.30, notes="Duplicate charge; disputed")
    add(dt.date(2026, 3, 3), "Oakview Clinic", "Medical", "demo-card", -385.0, notes="Urgent care visit (sprained ankle)")
    # monthly card payoff from checking (statement balance approximation)
    months = sorted({t["date"][:7] for t in tx})
    for ym in months:
        y, mo = map(int, ym.split("-"))
        spend = -sum(t["amount"] for t in tx if t["date"][:7] == ym and t["account"] == ACC["demo-card"])
        pd_ = dt.date(y, mo, 25)
        if pd_ <= END:
            add(pd_, "Demo Card Co Payment", "Credit Card Payment", "demo-chk", -round(spend, 2))
            add(pd_, "Payment received", "Credit Card Payment", "demo-card", round(spend, 2))
    tx.sort(key=lambda t: (t["date"], t["account"], t["merchant"], t["amount"]))
    for i, t in enumerate(tx, 1):
        t["txn_id"] = f"demo-{i:05d}"
        t["short_id"] = f"T-{(i * 7919) % 100000:05d}"
        cat = t["category"]
        t["kind"] = ("transfer" if cat in CATEGORIES["Transfers"] or t["amount"] == 0 else
                     "income" if cat in CATEGORIES["Income"] else "expense" if t["amount"] < 0 else "refund")
    return tx


def balances(tx, rng):
    """Weekly snapshots (Sundays). Cash/card/loan follow the transactions; investments get a seeded market walk."""
    by_acct = {a[1]: a[7] for a in ACCOUNTS}
    out, mkt = [], {"demo-brk": 1.0, "demo-ira": 1.0}
    tx_by_day = {}
    for t in tx:
        tx_by_day.setdefault(t["date"], []).append(t)
    contrib = {"demo-brk": 0.0, "demo-ira": 0.0}
    loan = -14600.0
    d = START
    while d <= END:
        for t in tx_by_day.get(d.isoformat(), []):
            name = t["account"]
            if name in (ACC["demo-chk"], ACC["demo-sav"], ACC["demo-card"]):
                by_acct[name] += t["amount"]
            if t["merchant"] == "Transfer to Brokerage":
                contrib["demo-brk"] += 500
            if t["merchant"] == "Roth IRA Contribution":
                contrib["demo-ira"] += 1750
            if t["merchant"] == "Demo Credit Union":
                loan += LOAN_PMT - abs(loan) * 0.059 / 12
        if d.weekday() == 6:
            for k in mkt:
                mkt[k] *= 1 + rng.gauss(0.0016, 0.021)
            by_acct[ACC["demo-brk"]] = 41200.0 * mkt["demo-brk"] + contrib["demo-brk"]
            by_acct[ACC["demo-ira"]] = 27800.0 * mkt["demo-ira"] + contrib["demo-ira"]
            by_acct[ACC["demo-loan"]] = loan
            weeks = (d - START).days / 7
            by_acct[ACC["demo-car"]] = 21500.0 * (1 - 0.0028 * weeks)
            for a in ACCOUNTS:
                out.append({"date": d.isoformat(), "account": a[1], "balance": round(by_acct[a[1]], 2), "klass": a[5]})
        d += dt.timedelta(days=1)
    return out


def main():
    ap = argparse.ArgumentParser(description="Generate the Finance Lab synthetic demo dataset (seeded, deterministic).")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent / "data"))
    ap.add_argument("--seed", type=int, default=SEED)
    a = ap.parse_args()
    out = Path(a.out)
    rng = random.Random(a.seed + 1)
    tx = build(a.seed)
    bal = balances(tx, rng)
    last = {}
    for b in bal:
        last[b["account"]] = b
    accounts = [{"id": i, "account": n, "institution": inst, "type": ty, "subtype": st_, "klass": k, "last4": l4 or None,
                 "balance": last[n]["balance"], "as_of": last[n]["date"]} for i, n, inst, ty, st_, k, l4, _ in ACCOUNTS]
    # monthly cash flow + net worth
    months = sorted({t["date"][:7] for t in tx})
    cash = []
    for ym in months:
        rows = [t for t in tx if t["date"][:7] == ym]
        inc = sum(t["amount"] for t in rows if t["kind"] == "income")
        spend = -sum(t["amount"] for t in rows if t["kind"] in ("expense", "refund"))
        cash.append({"month": ym, "income": round(inc, 2), "spend": round(spend, 2), "net": round(inc - spend, 2),
                     "savings_rate": round((inc - spend) / inc, 3) if inc else None})
    nw = []
    for ym in months:
        snap = [b for b in bal if b["date"][:7] == ym]
        if not snap:
            continue
        lastd = max(b["date"] for b in snap)
        s = [b for b in snap if b["date"] == lastd]
        agg = {k: round(sum(b["balance"] for b in s if b["klass"] == k), 2) for k in ("cash", "investment", "property", "liability")}
        nw.append({"month": ym, "date": lastd, **agg, "net_worth": round(sum(agg.values()), 2)})
    # recurring
    rec = []
    for merch, cat, day, sched, acct in SUBS:
        charges = [t for t in tx if t["merchant"] == merch]
        amts = [-t["amount"] for t in charges]
        lastc = charges[-1]
        nm = dt.date.fromisoformat(lastc["date"])
        nxt = (nm.replace(day=1) + dt.timedelta(days=32)).replace(day=min(day, 28))
        rec.append({"merchant": merch, "category": cat, "account": ACC[acct], "cadence": "monthly", "charges": len(charges),
                    "last_amount": amts[-1], "first_amount": amts[0], "price_creep_pct": round(100 * (amts[-1] / amts[0] - 1), 1),
                    "annualized": round(sum(amts[-12:]) if sched is None else amts[-1] * 12, 2), "last_charge": lastc["date"],
                    "next_expected": nxt.isoformat(), "variable": sched is None})
    budgets = {"Groceries": 650, "Restaurants & Bars": 300, "Shopping": 250, "Coffee Shops": 60, "Entertainment & Recreation": 120,
               "Gas": 160, "Digital Subscriptions": 70, "Taxi & Ride Shares": 50}
    bud_rows = []
    for ym in months:
        for c, v in budgets.items():
            spent = -sum(t["amount"] for t in tx if t["date"][:7] == ym and t["category"] == c and t["kind"] in ("expense", "refund"))
            bud_rows.append({"month": ym, "category": c, "budget": v, "spent": round(spent, 2), "pct": round(spent / v, 3)})
    cur_cash = round(sum(x["balance"] for x in accounts if x["klass"] == "cash"), 2)
    cur_inv = round(sum(x["balance"] for x in accounts if x["klass"] == "investment"), 2)
    goals = [
        {"name": "Emergency fund (6 months)", "target": 30000, "by": "2027-06", "track": "cash", "current": cur_cash},
        {"name": "Home down payment", "target": 90000, "by": "2029-12", "track": "investment", "current": cur_inv},
        {"name": "Pay off auto loan", "target": 0, "by": "2028-03", "track": "liability", "current": accounts[5]["balance"]},
        {"name": "Japan trip fund", "target": 6000, "by": "2027-04", "track": "cash", "current": None},
    ]
    scenarios = [
        {"name": "Annual bonus $8k in March", "lump": 8000, "lumpM": "2027-03", "income": 0, "incomeStart": "2027-03", "extra": 0, "on": True},
        {"name": "Raise: +$450/mo net from January", "lump": 0, "lumpM": "2027-01", "income": 450, "incomeStart": "2027-01", "extra": 0, "on": True},
        {"name": "Freelance retainer +$1,200/mo", "lump": 0, "lumpM": "2026-12", "income": 1200, "incomeStart": "2026-12", "extra": 0, "on": False},
        {"name": "Move to a bigger place (+$650/mo)", "lump": -3000, "lumpM": "2027-02", "income": 0, "incomeStart": "2027-02", "extra": 650, "on": True},
        {"name": "Sabbatical: 3 months unpaid", "lump": -18000, "lumpM": "2027-06", "income": 0, "incomeStart": "2027-06", "extra": 0, "on": False},
        {"name": "Car paid off early (-$412/mo)", "lump": -9000, "lumpM": "2027-01", "income": 0, "incomeStart": "2027-01", "extra": -412, "on": False},
    ]
    pick = lambda merch, n=0: [t for t in tx if t["merchant"] == merch][n]["txn_id"]
    notes = [
        {"txn_id": pick("Brightline Electronics"), "comment": "New laptop for freelance work; keep the receipt for taxes.", "labels": ["freelance", "big-purchase", "tax"]},
        {"txn_id": pick("Seaside Inn"), "comment": "Summer trip lodging, split with two friends (they paid me back).", "labels": ["trip", "shared"]},
        {"txn_id": [t for t in tx if t["merchant"] == "Saffron Table" and t["notes"]][0]["txn_id"], "comment": "Charged twice for one dinner; dispute opened.", "labels": ["dispute"]},
        {"txn_id": pick("Oakview Clinic", -1), "comment": "Ask the insurer about reimbursement.", "labels": ["medical", "reimbursable"]},
        {"txn_id": pick("Halcyon Labs (freelance)"), "comment": "First freelance invoice of the year.", "labels": ["freelance", "income"]},
        {"txn_id": pick("PixelForge Photo"), "comment": "Barely used; candidate to cancel.", "labels": ["cancel?"]},
    ]
    merchant_rules = {"bluebird coffee": "Coffee Shops", "zipride": "Taxi & Ride Shares", "metro park & go": "Parking & Tolls"}
    app_state = {"goals": [{k: v for k, v in g.items() if k != "current"} | {"current": None} for g in goals], "budgets": budgets,
                 "merchant_rules": merchant_rules, "ui_dashboard": ["kpis", "networth", "cashflow", "forecast", "categories", "recurring", "anomalies"],
                 "ui_scenarios": scenarios}
    meta = {"synthetic": True, "persona": PERSONA, "seed": a.seed, "start": START.isoformat(), "end": END.isoformat(),
            "note": "Every account, merchant, amount and note is invented from a fixed seed. No real financial data."}
    cats = [{"group": g, "category": c, "kind": "income" if g == "Income" else "transfer" if g == "Transfers" else "expense"}
            for g, cs in CATEGORIES.items() for c in cs]
    files = [
        write(out / "accounts.json", {**meta, "accounts": accounts}),
        write(out / "categories.json", {**meta, "categories": cats}),
        write(out / "transactions.json", {**meta, "count": len(tx), "transactions": tx}),
        write(out / "balances.json", {**meta, "count": len(bal), "cadence": "weekly (Sundays)", "balances": bal}),
        write(out / "net_worth.json", {**meta, "months": nw}),
        write(out / "cashflow.json", {**meta, "months": cash}),
        write(out / "recurring.json", {**meta, "recurring": rec}),
        write(out / "budgets.json", {**meta, "budgets": budgets, "monthly": bud_rows}),
        write(out / "goals.json", {**meta, "goals": goals}),
        write(out / "scenarios.json", {**meta, "scenarios": scenarios}),
        write(out / "notes.json", {**meta, "notes": notes}),
        write(out / "app_state.json", app_state),
    ]
    counts = {"accounts": len(accounts), "categories": len(cats), "transactions": len(tx), "balance_snapshots": len(bal),
              "months": len(months), "recurring": len(rec), "budgets": len(budgets), "goals": len(goals), "scenarios": len(scenarios),
              "notes": len(notes)}
    write(out / "manifest.json", {"app": "finance-lab", **meta, "generator": "demo/generate_data.py", "rows": counts, "files": files})
    print(json.dumps(counts))


if __name__ == "__main__":
    main()
