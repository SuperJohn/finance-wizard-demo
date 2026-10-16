import json
import pytest
from fastapi.testclient import TestClient
from fw import analytics as A, tools, agent
from fw.main import app

c = TestClient(app)


def test_fixture_source():
    assert c.get("/api/health").json()["source"] == "fixture"


@pytest.mark.parametrize("path", ["/api/summary", "/api/accounts", "/api/networth", "/api/cashflow", "/api/spending?dim=merchant",
    "/api/recurring", "/api/anomalies", "/api/forecast", "/api/analytics/real", "/api/analytics/savings",
    "/api/analytics/distribution", "/api/analytics/cohorts", "/api/category_trend", "/api/transactions?q=streamflix", "/api/daily"])
def test_endpoints(path):
    r = c.get(path); assert r.status_code == 200, r.text


def test_subscriptions_found():
    names = {r["merchant"] for r in A.detect_recurring()}
    assert {"StreamFlix", "TuneWave Music"} <= names


def test_anomaly_flags_big_purchase():
    assert any(a["merchant"] == "Brightline Electronics" for a in A.detect_anomalies(days=2000))


def test_runway_math():
    r = A.runway({"cash": 10000, "monthly_burn": 1000, "months": 24, "inflation": 0, "return_rate": 0})
    assert r["runway_months"] == 10
    r2 = A.runway({"cash": 10000, "monthly_burn": 1000, "months": 24, "inflation": 0, "return_rate": 0, "lump_sums": [{"amount": 5000, "month": r["rows"][0]["month"]}]})
    assert r2["runway_months"] == 15


def test_monte_carlo_bands_ordered():
    mc = A.runway_monte_carlo({"cash": 50000, "monthly_burn": 4000, "months": 12, "spend_vol": 0.2}, sims=500)
    assert all(b["p10"] <= b["p50"] <= b["p90"] for b in mc["bands"])


def test_decomposition_additive():
    d = A.spend_decomposition("2025-05", "2025-06")
    for r in d["rows"]:
        assert abs(r["volume_effect"] + r["price_effect"] - r["delta"]) < 0.05


def test_sql_readonly():
    assert tools.run_sql("select count(*) n from fw.txns")["rows"][0][0] != "0"
    for bad in ["drop table fw.txns", "select 1; delete from fw.txns", "copy fw.txns to 'x.csv'", "attach 'x' as y"]:
        with pytest.raises(ValueError):
            tools.run_sql(bad)


def test_categorize_action_and_budget():
    tools.categorize(merchant="Taco Truck 22", category="Fast Food")
    assert any(r["name"] == "Fast Food" for r in A.spending_by("category", since="2020-01-01", limit=100))
    assert tools.set_budget("Groceries", 500)["ok"]


def test_agent_loop_with_fake_model():
    script = iter([json.dumps({"tool": "summary", "args": {}}), json.dumps({"answer": "done"})])
    out = agent.run([{"role": "user", "content": "how am I doing?"}], chat=lambda *a: next(script))
    assert out["answer"] == "done" and out["trace"][0]["tool"] == "summary" and out["trace"][0]["ok"]


def test_scenarios():
    res = A.scenarios({"cash": 20000, "monthly_burn": 3000, "months": 24}, [{"name": "Windfall", "lump_sums": [{"amount": 25000, "month": "2026-12"}]}])
    assert res[1]["end_cash"] > res[0]["end_cash"]


def test_transactions_json_safe_with_nulls():
    from fw import data
    data.q("UPDATE fw.txns SET amount = NULL WHERE txn_id = 'fx0'")
    r = c.get("/api/transactions?limit=100000"); assert r.status_code == 200


def test_transfers_and_refunds_classified():
    from fw import data
    k = dict(data.q("SELECT category, any_value(kind) FROM fw.txns WHERE category='Credit Card Payment' GROUP BY 1").values)
    assert k["Credit Card Payment"] == "transfer"
    r = data.q("SELECT kind FROM fw.txns WHERE merchant='MegaMart' AND amount > 0")
    assert set(r["kind"]) == {"refund"}
    cf = {m["month"]: m for m in A.monthly_cashflow(60)}
    assert cf["2026-05"]["income"] == 8400  # payroll only: the MegaMart refund nets spend, not income


def test_model_loader_falls_back_cleanly():
    import duckdb
    from fw import data as D
    with pytest.raises(Exception):
        D._from_models(duckdb.connect(":memory:"))


def _mini_views(rows):
    import duckdb, pandas as pd
    from fw import data
    tx = pd.DataFrame(rows, columns=["txn_id", "date", "merchant", "category", "account", "amount", "is_refund"])
    tx["tags"] = None; tx["notes"] = None; tx["is_transfer"] = False
    c = duckdb.connect(":memory:")
    data._build_views(c, tx, pd.DataFrame({"date": [], "account": [], "balance": []}))
    return c.execute("SELECT txn_id, CAST(date AS VARCHAR) d, category, kind, amount FROM fw.txns ORDER BY txn_id").df()


CARD_ROWS = [  # synthetic statement lines on a demo card (transaction dates)
    ("a", "2026-04-23", "Summit Outdoor Supply", "Shopping", "Demo Card …0003", -640.00, False),
    ("b", "2026-04-27", "Summit Outdoor Supply", "Shopping", "Demo Card …0003", -212.48, False),
    ("c", "2026-04-30", "Summit Outdoor Supply", "Shopping", "Demo Card …0003", -1260.00, False),
    ("d", "2026-05-14", "Summit Outdoor Supply", "INCOME", "Demo Card …0003", 195.00, True),  # provider mis-tagged the credit as income
]


def test_date_fidelity_no_timezone_shift():
    d = _mini_views(CARD_ROWS)
    assert list(d["d"]) == ["2026-04-23", "2026-04-27", "2026-04-30", "2026-05-14"]


def test_card_credit_is_refund_netted_in_merchant_category():
    d = _mini_views(CARD_ROWS)
    r = d[d.txn_id == "d"].iloc[0]
    assert r.kind == "refund" and r.category == "Shopping"
    net = -d[d.kind.isin(["expense", "refund"])]["amount"].sum()
    assert round(net, 2) == round(640 + 212.48 + 1260 - 195, 2)
    assert "income" not in set(d["kind"])


def test_refunds_flow_into_spending_views():
    from fw import data
    s = {r["name"]: r["spend"] for r in A.spending_by("merchant", since="2026-05-01", until="2026-05-31")}
    raw = data.q("SELECT -sum(amount) s FROM fw.txns WHERE merchant='MegaMart' AND date BETWEEN '2026-05-01' AND '2026-05-31' AND kind IN ('expense','refund')")["s"][0]
    assert round(s["MegaMart"], 2) == round(raw, 2)
    daily = sum(x["spend"] for x in A.daily_spend(4000) if x["date"] == "2026-05-20" and x["category"] == "Shopping")
    exp = -data.q("SELECT sum(amount) s FROM fw.txns WHERE date='2026-05-20' AND category='Shopping' AND kind IN ('expense','refund')")["s"][0]
    assert round(daily, 2) == round(exp, 2)


@pytest.mark.skipif(not __import__("os").environ.get("FW_TEST_LAKE"), reason="set FW_TEST_LAKE=/path/to/lake.duckdb (built by finance-lake-demo)")
def test_reads_synthetic_lake_models():
    import os
    from pathlib import Path
    from fw import config, data
    config.LAKE_PATH = Path(os.environ["FW_TEST_LAKE"])
    try:
        data.load(force_fixture=False)
        assert data.info()["source"].startswith("lake models")
        k = dict(data.q("SELECT kind, count(*) FROM fw.txns GROUP BY 1").values)
        assert k["income"] > 0 and k["expense"] > 0 and k["transfer"] > 0 and k["refund"] > 0
        assert data.has_table("fw.net_worth")
        assert c.get("/api/summary").status_code == 200
    finally:
        data.load(force_fixture=True)
