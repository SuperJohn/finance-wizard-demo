"""Typed tools the agent can call. Each returns JSON-serializable data.
Write tools only touch data/app_state.json (never the lake)."""
import re
import datetime as dt
from . import analytics as A, data, store

FORBIDDEN = re.compile(r"\b(insert|update|delete|drop|create|alter|attach|detach|copy|export|install|load|pragma|set|call|checkpoint)\b", re.I)


def run_sql(sql: str, limit: int = 200):
    s = sql.strip().rstrip(";")
    if not re.match(r"^(select|with)\b", s, re.I) or FORBIDDEN.search(s) or ";" in s:
        raise ValueError("Only a single read-only SELECT/WITH statement is allowed.")
    d = data.q(f"SELECT * FROM ({s}) LIMIT {int(min(limit, 1000))}")
    return {"columns": list(d.columns), "rows": d.astype(object).where(d.notna(), None).astype(str).values.tolist()}


def categorize(merchant: str | None = None, category: str = "", txn_id: str | None = None):
    if not category:
        raise ValueError("category required")
    if txn_id:
        ov = store.get("category_overrides", {}); ov[txn_id] = category; store.put("category_overrides", ov)
    elif merchant:
        r = store.get("merchant_rules", {}); r[merchant.lower()] = category; store.put("merchant_rules", r)
    else:
        raise ValueError("merchant or txn_id required")
    data.load()
    return {"ok": True, "rule": {"merchant": merchant, "txn_id": txn_id, "category": category}}


def set_budget(category: str, monthly_amount: float):
    b = store.get("budgets", {}); b[category] = float(monthly_amount); store.put("budgets", b)
    return {"ok": True, "budgets": A.budgets_status()}


def add_goal(name: str, target: float, by: str | None = None, track: str | None = None, current: float | None = None):
    g = store.get("goals", []); g = [x for x in g if x["name"] != name]
    g.append({"name": name, "target": float(target), "by": by, "track": track, "current": current}); store.put("goals", g)
    return {"ok": True, "goals": A.goals_status()}


TOOLS = {
    "run_sql": (run_sql, "Read-only DuckDB SQL. Tables: fw.txns(txn_id,date,merchant,category,account,amount[neg=outflow],tags,notes,kind in income|expense|transfer), fw.balances(date,account,balance,klass in cash|investment|property|liability), fw.net_worth(date,cash,investment,property,liability,net_worth). Also the raw lake (read-only): lake.core.fact_transaction, lake.core.dim_account, lake.core.fact_balance_snapshot, lake.marts.net_worth, lake.marts.monthly_cashflow, lake.marts.runway, lake.marts.debt_schedule, lake.core.fact_holding_snapshot. Args: sql"),
    "summary": (lambda: A.summary(), "Headline numbers: net worth, liquid cash, avg spend/income, runway, recurring total."),
    "spending_by": (lambda dim="category", since=None, until=None, limit=15: A.spending_by(dim, since, until, limit), "Spend grouped by category|merchant|account. Args: dim, since(YYYY-MM-DD), until, limit"),
    "monthly_cashflow": (lambda months=12, real=False: A.monthly_cashflow(months, real), "Monthly income/spend/net/savings_rate. Args: months, real(bool, CPI-deflated)"),
    "forecast_spend": (lambda months=6: A.forecast_spend(months), "Forecast monthly spend with 80% interval. Args: months"),
    "detect_anomalies": (lambda days=90, z=3.5: A.detect_anomalies(days, z), "Unusual charges via robust z-score per category + large new merchants. Args: days, z"),
    "detect_subscriptions": (lambda: A.detect_recurring(), "Recurring charges/subscriptions with cadence, annualized cost, price change."),
    "runway": (lambda **p: {k: v for k, v in A.runway({**A.default_runway_inputs(), **p}).items() if k != "rows"}, "Cash runway. Args (optional): cash, monthly_burn, months, lump_sums[{label,amount,month}], income[{label,monthly_net,start}], extra_monthly[{label,amount,start}]"),
    "spend_decomposition": (lambda a, b: A.spend_decomposition(a, b), "Explain spend change between months a and b (YYYY-MM) into category volume vs price effects."),
    "categorize": (categorize, "ACTION: recategorize. Args: category, and merchant (rule for all) or txn_id (single)."),
    "set_budget": (set_budget, "ACTION: set monthly budget. Args: category, monthly_amount"),
    "add_goal": (add_goal, "ACTION: create/update goal. Args: name, target, by(YYYY-MM), track(net_worth|cash|investment optional), current"),
}


def call(name: str, args: dict):
    if name not in TOOLS:
        raise ValueError(f"unknown tool {name}")
    return TOOLS[name][0](**(args or {}))


def catalog():
    return "\n".join(f"- {k}: {v[1]}" for k, v in TOOLS.items())
