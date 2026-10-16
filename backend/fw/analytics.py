"""Analytics engine: pure functions over fw.txns / fw.balances."""
import datetime as dt
import numpy as np
import pandas as pd
from . import data, cpi, store


def _d(x) -> str:
    """Calendar date as YYYY-MM-DD (no time part, no timezone conversion)."""
    return pd.Timestamp(x).date().isoformat()


def _tx(since=None, until=None, kinds=None):
    w, p = [], []
    if since: w.append("date >= ?"); p.append(since)
    if until: w.append("date <= ?"); p.append(until)
    if kinds: w.append("kind IN (" + ",".join("?" * len(kinds)) + ")"); p += list(kinds)
    sql = "SELECT * FROM fw.txns" + (" WHERE " + " AND ".join(w) if w else "")
    return data.q(sql, p)


def net_worth_history(freq="W"):
    if data.has_table("fw.net_worth"):
        n = data.q("SELECT * FROM fw.net_worth ORDER BY date")
        n["date"] = pd.to_datetime(n["date"])
        n = n.set_index("date").resample(freq).last().dropna(how="all")
        return [{"date": d.date().isoformat(), **{k: round(float(v), 2) for k, v in r.items()}} for d, r in n.iterrows()]
    b = data.q("SELECT date, account, balance, klass FROM fw.balances")
    if b.empty:
        return []
    b["date"] = pd.to_datetime(b["date"])
    piv = b.pivot_table(index="date", columns="account", values="balance", aggfunc="last").sort_index()
    piv = piv.asfreq("D").ffill()
    klass = b.drop_duplicates("account").set_index("account")["klass"]
    out = []
    for d, row in piv.resample(freq).last().iterrows():
        by = {"cash": 0.0, "investment": 0.0, "property": 0.0, "liability": 0.0}
        for acct, v in row.dropna().items():
            k = klass[acct]
            by[k] += -abs(v) if k == "liability" else v
        out.append({"date": d.date().isoformat(), **{k: round(v, 2) for k, v in by.items()},
                    "net_worth": round(sum(by.values()), 2)})
    return out


def accounts():
    b = data.q("""SELECT account, klass, arg_max(balance, date) balance, max(date) as_of
                  FROM fw.balances GROUP BY 1,2 ORDER BY klass, balance DESC""")
    b["balance"] = b.apply(lambda r: -abs(r.balance) if r.klass == "liability" else r.balance, axis=1)
    return b.assign(as_of=b.as_of.astype(str)).to_dict("records")


def monthly_cashflow(months=24, real=False):
    t = _tx(kinds=("income", "expense", "refund"))
    if t.empty:
        return []
    t["kind"] = t["kind"].replace({"refund": "expense"})  # refunds net against spend
    t["ym"] = pd.to_datetime(t["date"]).dt.to_period("M")
    g = t.groupby(["ym", "kind"])["amount"].sum().unstack(fill_value=0)
    g = g.reindex(columns=["income", "expense"], fill_value=0).tail(months)
    defl = cpi.deflator()
    out = []
    for ym, r in g.iterrows():
        inc, exp = float(r["income"]), float(-r["expense"])
        f = 1 / defl.get(ym, 1.0) if real else 1.0
        out.append({"month": str(ym), "income": round(inc * f, 2), "spend": round(exp * f, 2),
                    "net": round((inc - exp) * f, 2),
                    "savings_rate": round((inc - exp) / inc, 4) if inc > 0 else None})
    return out


def spending_by(dim="category", since=None, until=None, limit=25):
    assert dim in ("category", "merchant", "account")
    since = since or (dt.date.today() - dt.timedelta(days=90)).isoformat()
    t = _tx(since, until, ("expense", "refund"))
    if t.empty:
        return []
    g = t.groupby(dim)["amount"].agg(["sum", "count"]).sort_values("sum").head(limit)
    total = -t["amount"].sum()
    return [{"name": k, "spend": round(-v["sum"], 2), "count": int(v["count"]),
             "share": round(-v["sum"] / total, 4) if total else 0} for k, v in g.iterrows()]


def category_trend(top=8, months=12):
    t = _tx(kinds=("expense", "refund"))  # refunds net against their category
    t["ym"] = pd.to_datetime(t["date"]).dt.to_period("M").astype(str)
    cats = t.groupby("category")["amount"].sum().sort_values().head(top).index
    t["cat"] = t["category"].where(t["category"].isin(cats), "Other")
    p = (-t.pivot_table(index="ym", columns="cat", values="amount", aggfunc="sum", fill_value=0)).tail(months)
    return {"series": list(p.columns), "rows": [{"month": i, **{c: round(float(v), 2) for c, v in r.items()}} for i, r in p.iterrows()]}


def detect_recurring(min_occ=3):
    t = _tx(kinds=("expense",))
    out = []
    for m, g in t.groupby("merchant"):
        if len(g) < min_occ or not m:
            continue
        g = g.sort_values("date")
        d = pd.to_datetime(g["date"]).diff().dt.days.dropna()
        if d.empty:
            continue
        med = d.median()
        amts = -g["amount"]
        cv = amts.std() / amts.mean() if amts.mean() else 9
        cadence = next((c for c, lo, hi in (("weekly", 6, 8), ("monthly", 26, 35), ("quarterly", 85, 95), ("annual", 350, 380)) if lo <= med <= hi), None)
        regular = (d.between(med * 0.6, med * 1.4)).mean() if med else 0
        if cadence and cv < 0.35 and regular >= 0.6:
            last = pd.to_datetime(g["date"]).max()
            per_year = {"weekly": 52, "monthly": 12, "quarterly": 4, "annual": 1}[cadence]
            typical = float(amts.tail(3).median())
            active = (pd.Timestamp.today() - last).days < med * 1.8
            out.append({"merchant": m, "category": g["category"].iloc[-1], "cadence": cadence, "typical": round(typical, 2),
                        "annualized": round(typical * per_year, 2), "occurrences": len(g), "last": last.date().isoformat(),
                        "next_expected": (last + pd.Timedelta(days=med)).date().isoformat(), "active": bool(active),
                        "price_change": round(float(amts.iloc[-1] - amts.iloc[0]), 2), "confidence": round(float(regular * (1 - min(cv, 1))), 2)})
    return sorted(out, key=lambda r: (not r["active"], -r["annualized"]))


def detect_anomalies(days=120, z=3.5):
    t = _tx(kinds=("expense",))
    t["amt"] = -t["amount"]
    out = []
    cutoff = (dt.date.today() - dt.timedelta(days=days))
    for c, g in t.groupby("category"):
        if len(g) < 8:
            continue
        x = np.log1p(g["amt"].clip(lower=0))
        med = x.median(); mad = (x - med).abs().median() * 1.4826 or 1e-6
        rz = (x - med) / mad
        hits = g[(rz > z) & (pd.to_datetime(g["date"]).dt.date >= cutoff) & (g["amt"] > 50)]
        for _, r in hits.iterrows():
            out.append({"txn_id": r.txn_id, "date": _d(r.date), "merchant": r.merchant, "category": c,
                        "amount": round(r.amt, 2), "typical": round(float(np.expm1(med)), 2), "robust_z": round(float(rz[_]), 2)})
    # merchants never seen before with large charges
    first = t.groupby("merchant")["date"].transform("min")
    new = t[(t["date"] == first) & (pd.to_datetime(t["date"]).dt.date >= cutoff) & (t["amt"] > 250)]
    for _, r in new.iterrows():
        out.append({"txn_id": r.txn_id, "date": _d(r.date), "merchant": r.merchant, "category": r.category,
                    "amount": round(r.amt, 2), "typical": None, "robust_z": None, "reason": "new merchant, large"})
    return sorted(out, key=lambda r: r["date"], reverse=True)


def forecast_spend(months=6):
    """Per-category EWMA level + damped trend; total with ~80% interval from residual sd."""
    t = _tx(kinds=("expense",))
    t["ym"] = pd.to_datetime(t["date"]).dt.to_period("M")
    p = -t.pivot_table(index="ym", columns="category", values="amount", aggfunc="sum", fill_value=0)
    p = p.iloc[:-1].tail(24)  # drop partial current month
    if p.empty:
        return {"history": [], "forecast": []}
    tot = p.sum(axis=1)
    lvl = tot.ewm(halflife=3).mean()
    slope = np.polyfit(range(min(12, len(tot))), tot.tail(12).values, 1)[0] if len(tot) > 2 else 0
    sd = float((tot - lvl.shift(1)).dropna().std() or 0)
    last = p.index[-1]
    fc = []
    for h in range(1, months + 1):
        mu = float(lvl.iloc[-1] + slope * 0.5 * h)
        fc.append({"month": str(last + h), "spend": round(mu, 2), "lo": round(max(0, mu - 1.28 * sd), 2), "hi": round(mu + 1.28 * sd, 2)})
    bycat = (p.ewm(halflife=3).mean().iloc[-1]).sort_values(ascending=False).head(12)
    return {"history": [{"month": str(i), "spend": round(float(v), 2)} for i, v in tot.items()], "forecast": fc,
            "by_category_next_month": {k: round(float(v), 2) for k, v in bycat.items()}}


def baseline_burn(months=6, exclude_categories=()):
    t = _tx(kinds=("expense", "refund"))
    t["ym"] = pd.to_datetime(t["date"]).dt.to_period("M")
    t = t[~t["category"].isin(exclude_categories)]
    m = -t.groupby("ym")["amount"].sum()
    m = m.iloc[:-1].tail(months)
    return round(float(m.mean()), 2) if len(m) else 0.0


def liquid_cash():
    a = accounts()
    return round(sum(x["balance"] for x in a if x["klass"] == "cash"), 2)


def runway(p: dict):
    """Month-by-month cash projection. p keys (all optional):
    cash, monthly_burn, extra_monthly (list of {label, amount, start, end}), lump_sums (list {label, amount, month}),
    income (list {label, monthly_net, start}), months, inflation (annual), return_rate (annual on cash)"""
    months = int(p.get("months", 36))
    cash = float(p.get("cash", liquid_cash()))
    burn = float(p.get("monthly_burn", baseline_burn()))
    infl = float(p.get("inflation", 0.03)); r = float(p.get("return_rate", 0.04))
    start = pd.Period(p.get("start") or dt.date.today().strftime("%Y-%m"), "M")
    months_list = [str(start + h) for h in range(months)]
    rows, zero = [], None
    for h in range(months):
        m = start + h
        spend = burn * (1 + infl) ** (h / 12)
        for e in p.get("extra_monthly", []):
            if pd.Period(e.get("start", str(start)), "M") <= m and (not e.get("end") or m <= pd.Period(e["end"], "M")):
                spend += float(e["amount"])
        inc = sum(float(i["monthly_net"]) for i in p.get("income", []) if pd.Period(i["start"], "M") <= m)
        lump = sum(float(l["amount"]) for l in p.get("lump_sums", []) if pd.Period(l["month"], "M") == m)
        cash = cash * (1 + r / 12) + inc + lump - spend
        rows.append({"month": str(m), "spend": round(spend, 2), "income": round(inc, 2), "lump": round(lump, 2), "cash": round(cash, 2)})
        if cash < 0 and zero is None:
            zero = str(m)
    return {"rows": rows, "runs_out": zero, "runway_months": next((i for i, x in enumerate(rows) if x["cash"] < 0), None),
            "inputs": {"cash": float(p.get("cash", liquid_cash())), "monthly_burn": burn}}


def default_runway_inputs():
    return {"cash": liquid_cash(), "monthly_burn": baseline_burn(), "months": 36, "inflation": 0.03, "return_rate": 0.04,
            "extra_monthly": [], "lump_sums": [], "income": []}


def scenarios(base: dict, variants: list[dict]):
    res = [{"name": "Baseline", **runway(base)}]
    for v in variants:
        p = {**base, **{k: v[k] for k in v if k != "name"}}
        for k in ("extra_monthly", "lump_sums", "income"):
            p[k] = base.get(k, []) + v.get(k, [])
        res.append({"name": v.get("name", "Scenario"), **runway(p)})
    for r in res:
        r["end_cash"] = r["rows"][-1]["cash"] if r["rows"] else None
    return res


def distribution(days=365):
    t = _tx((dt.date.today() - dt.timedelta(days=days)).isoformat(), kinds=("expense",))
    a = -t["amount"]
    if a.empty:
        return {}
    bins = [0, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 1e9]
    labels = ["<5", "5-10", "10-25", "25-50", "50-100", "100-250", "250-500", "500-1k", "1k-2.5k", "2.5k+"]
    c = pd.cut(a, bins, labels=labels)
    h = pd.DataFrame({"b": c, "a": a}).groupby("b", observed=False)["a"].agg(["count", "sum"])
    dow = t.assign(d=pd.to_datetime(t["date"]).dt.day_name()).groupby("d")["amount"].sum()
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    lor = np.sort(a.values); cum = np.cumsum(lor) / lor.sum()
    top10 = 1 - cum[int(len(cum) * 0.9) - 1] if len(cum) > 10 else None
    gini = 1 - 2 * np.trapezoid(cum, dx=1 / len(cum)) if len(cum) else None
    return {"histogram": [{"bucket": k, "count": int(v["count"]), "spend": round(float(v["sum"]), 2)} for k, v in h.iterrows()],
            "day_of_week": [{"day": d[:3], "spend": round(float(-dow.get(d, 0)), 2)} for d in order],
            "stats": {"n": int(len(a)), "mean": round(float(a.mean()), 2), "median": round(float(a.median()), 2),
                      "p90": round(float(a.quantile(0.9)), 2), "p99": round(float(a.quantile(0.99)), 2),
                      "top10pct_share": round(float(top10), 3) if top10 is not None else None, "gini": round(float(gini), 3) if gini is not None else None}}


def merchant_cohorts():
    """Cohort = year a merchant first appears; spend by calendar year per cohort (merchant retention/lock-in)."""
    t = _tx(kinds=("expense", "refund"))
    t["y"] = pd.to_datetime(t["date"]).dt.year
    t["cohort"] = t.groupby("merchant")["y"].transform("min")
    p = -t.pivot_table(index="y", columns="cohort", values="amount", aggfunc="sum", fill_value=0)
    return {"cohorts": [str(c) for c in p.columns], "rows": [{"year": str(y), **{str(c): round(float(v), 2) for c, v in r.items()}} for y, r in p.iterrows()]}


def real_vs_nominal(months=36):
    nom = {r["month"]: r for r in monthly_cashflow(months)}
    real = {r["month"]: r for r in monthly_cashflow(months, real=True)}
    return [{"month": m, "spend_nominal": nom[m]["spend"], "spend_real": real[m]["spend"],
             "income_nominal": nom[m]["income"], "income_real": real[m]["income"]} for m in nom]


def savings_rate_series(months=24):
    cf = monthly_cashflow(months)
    out, acc_i, acc_s = [], [], []
    for r in cf:
        acc_i.append(r["income"]); acc_s.append(r["spend"])
        i12, s12 = sum(acc_i[-12:]), sum(acc_s[-12:])
        out.append({"month": r["month"], "savings_rate": r["savings_rate"], "ttm_savings_rate": round((i12 - s12) / i12, 4) if i12 > 0 else None})
    return out


def budgets_status():
    b = store.get("budgets", {})
    if not b:
        return []
    start = dt.date.today().replace(day=1).isoformat()
    spent = {r["name"]: r["spend"] for r in spending_by("category", since=start, limit=200)}
    day = dt.date.today().day; import calendar
    dim = calendar.monthrange(dt.date.today().year, dt.date.today().month)[1]
    return [{"category": c, "budget": v, "spent": spent.get(c, 0.0), "pace": round(spent.get(c, 0.0) / (v * day / dim), 2) if v else None} for c, v in b.items()]


def goals_status():
    gs = store.get("goals", [])
    nw = net_worth_history("ME")
    cur = nw[-1] if nw else {}
    out = []
    for g in gs:
        cur_v = g.get("current")
        if g.get("track") in cur:
            cur_v = cur[g["track"]]
        cur_v = float(cur_v or 0)
        tgt = float(g["target"])
        months_left = max(1, (pd.Period(g["by"], "M") - pd.Period(dt.date.today().strftime("%Y-%m"), "M")).n) if g.get("by") else None
        out.append({**g, "current": cur_v, "progress": round(min(1, cur_v / tgt), 3) if tgt else None,
                    "needed_per_month": round((tgt - cur_v) / months_left, 2) if months_left else None})
    return out


def summary():
    nw = net_worth_history("ME")
    cf = monthly_cashflow(13)
    complete = cf[:-1] if len(cf) > 1 else cf
    last3 = complete[-3:]
    rw = runway(default_runway_inputs())
    return {"net_worth": nw[-1] if nw else None, "net_worth_change_30d": (nw[-1]["net_worth"] - nw[-2]["net_worth"]) if len(nw) > 1 else None,
            "avg_spend_3m": round(np.mean([r["spend"] for r in last3]), 2) if last3 else None,
            "avg_income_3m": round(np.mean([r["income"] for r in last3]), 2) if last3 else None,
            "liquid_cash": liquid_cash(), "runway_months": rw["runway_months"], "runs_out": rw["runs_out"],
            "recurring_annual": round(sum(r["annualized"] for r in detect_recurring() if r["active"]), 2),
            "anomalies": len(detect_anomalies(30)), "source": data.info()}


def runway_monte_carlo(p: dict, sims=2000, seed=0):
    """Stochastic runway: monthly spend ~ lognormal around burn with sigma estimated from
    history (overridable via p['spend_vol']); returns ~ N(return_rate/12, market_vol/sqrt12) on investable cash.
    Returns percentile bands p10/p50/p90 and P(cash<0) by month."""
    rng = np.random.default_rng(seed)
    base = det = runway(p)
    months = len(base["rows"])
    vol = p.get("spend_vol")
    if vol is None:
        cf = [r["spend"] for r in monthly_cashflow(18)[:-1]]
        vol = float(np.std(np.log(np.array(cf) + 1))) if len(cf) > 3 else 0.2
        vol = min(max(vol, 0.05), 0.6)
    mvol = float(p.get("market_vol", 0.0))
    cash = np.full(sims, float(base["inputs"]["cash"]))
    r = float(p.get("return_rate", 0.04))
    paths = np.zeros((months, sims))
    for h, row in enumerate(base["rows"]):
        shock = rng.lognormal(-vol ** 2 / 2, vol, sims)
        ret = rng.normal(r / 12, mvol / np.sqrt(12), sims) if mvol else r / 12
        cash = cash * (1 + ret) + row["income"] + row["lump"] - row["spend"] * shock
        paths[h] = cash
    q = np.percentile(paths, [10, 50, 90], axis=1)
    out = [{"month": row["month"], "p10": round(float(q[0][h]), 2), "p50": round(float(q[1][h]), 2), "p90": round(float(q[2][h]), 2),
            "p_broke": round(float((paths[h] < 0).mean()), 3), "deterministic": det["rows"][h]["cash"]} for h, row in enumerate(base["rows"])]
    first_neg = (paths < 0).argmax(axis=0).astype(float)
    first_neg[~(paths < 0).any(axis=0)] = np.nan
    return {"bands": out, "spend_vol": round(vol, 3), "median_runway_months": None if np.isnan(first_neg).mean() > 0.5 else float(np.nanmedian(first_neg)),
            "p_broke_end": out[-1]["p_broke"] if out else None, "deterministic": det}


def spend_decomposition(a: str, b: str):
    """Decompose change in spend between months a -> b into category contributions,
    and each category into volume (count) vs price (avg ticket) effects (additive, midpoint/Shapley split)."""
    t = _tx(kinds=("expense", "refund"))  # net spend; refunds don't count as transactions
    t["ym"] = pd.to_datetime(t["date"]).dt.to_period("M").astype(str)
    t["amt"] = -t["amount"]
    t["n"] = (t["kind"] == "expense").astype(int)
    g = t[t["ym"].isin([a, b])].groupby(["category", "ym"]).agg(sum=("amt", "sum"), count=("n", "sum")).unstack(fill_value=0)
    rows = []
    for c, r in g.iterrows():
        s0, s1 = r[("sum", a)] if ("sum", a) in r else 0, r[("sum", b)] if ("sum", b) in r else 0
        n0, n1 = r[("count", a)] if ("count", a) in r else 0, r[("count", b)] if ("count", b) in r else 0
        p0 = s0 / n0 if n0 else (s1 / n1 if n1 else 0); p1 = s1 / n1 if n1 else p0
        vol_eff = (n1 - n0) * (p0 + p1) / 2; price_eff = (p1 - p0) * (n0 + n1) / 2
        rows.append({"category": c, "from": round(float(s0), 2), "to": round(float(s1), 2), "delta": round(float(s1 - s0), 2),
                     "volume_effect": round(float(vol_eff), 2), "price_effect": round(float(price_eff), 2), "n_from": int(n0), "n_to": int(n1)})
    rows.sort(key=lambda x: -abs(x["delta"]))
    return {"from": a, "to": b, "total_from": round(sum(x["from"] for x in rows), 2), "total_to": round(sum(x["to"] for x in rows), 2), "rows": rows}


def transactions(since=None, until=None, category=None, merchant=None, q=None, limit=500):
    w, p = [], []
    for col, v in (("date >=", since), ("date <=", until)):
        if v: w.append(f"{col} ?"); p.append(v)
    if category: w.append("category = ?"); p.append(category)
    if merchant: w.append("merchant = ?"); p.append(merchant)
    if q: w.append("(merchant ILIKE ? OR category ILIKE ? OR coalesce(notes,'') ILIKE ?)"); p += [f"%{q}%"] * 3
    sql = "SELECT txn_id, date, merchant, category, account, amount, kind, tags FROM fw.txns" + (" WHERE " + " AND ".join(w) if w else "") + f" ORDER BY date DESC LIMIT {int(limit)}"
    d = data.q(sql, p)
    d = d.assign(date=d["date"].astype(str)).astype(object)
    return d.where(d.notna(), None).to_dict("records")


def daily_spend(days=730):
    t = _tx((dt.date.today() - dt.timedelta(days=days)).isoformat(), kinds=("expense", "refund"))
    g = t.groupby(["date", "category"])["amount"].sum().reset_index()
    return [{"date": _d(r.date), "category": r.category, "spend": round(-float(r.amount), 2)} for r in g.itertuples()]
