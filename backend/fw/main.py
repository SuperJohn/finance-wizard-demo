from pathlib import Path
from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from . import analytics as A, agent, data, store, tools, config

app = FastAPI(title="Finance Lab", version="0.1.0")


@app.on_event("startup")  # noqa
def _startup():
    data.load()


def _h(fn, *a, **k):
    try:
        return fn(*a, **k)
    except (ValueError, TypeError) as e:
        raise HTTPException(400, str(e))


@app.get("/api/health")
def health(): return {"ok": True, **data.info()}
@app.post("/api/reload")
def reload(): data.load(); return data.info()
@app.get("/api/summary")
def summary(): return A.summary()
@app.get("/api/accounts")
def accounts(): return A.accounts()
@app.get("/api/networth")
def networth(freq: str = "W"): return A.net_worth_history(freq)
@app.get("/api/cashflow")
def cashflow(months: int = 24, real: bool = False): return A.monthly_cashflow(months, real)
@app.get("/api/spending")
def spending(dim: str = "category", since: str | None = None, until: str | None = None, limit: int = 25): return _h(A.spending_by, dim, since, until, limit)
@app.get("/api/category_trend")
def ctrend(top: int = 8, months: int = 18): return A.category_trend(top, months)
@app.get("/api/daily")
def daily(days: int = 730): return A.daily_spend(days)
@app.get("/api/transactions")
def txns(since: str | None = None, until: str | None = None, category: str | None = None, merchant: str | None = None, q: str | None = None, limit: int = 500):
    return A.transactions(since, until, category, merchant, q, limit)
@app.get("/api/recurring")
def recurring(): return A.detect_recurring()
@app.get("/api/anomalies")
def anomalies(days: int = 180, z: float = 3.5): return A.detect_anomalies(days, z)
@app.get("/api/forecast")
def forecast(months: int = 6): return A.forecast_spend(months)
@app.get("/api/runway/defaults")
def rdefaults(): return A.default_runway_inputs()
@app.post("/api/runway")
def runway(p: dict = Body(...)): return _h(A.runway, p)
@app.post("/api/runway/mc")
def runway_mc(p: dict = Body(...)): return _h(A.runway_monte_carlo, p, int(p.get("sims", 2000)))
@app.post("/api/scenarios")
def scen(p: dict = Body(...)): return _h(A.scenarios, p.get("base", A.default_runway_inputs()), p.get("variants", []))
@app.get("/api/decomposition")
def decomp(a: str, b: str): return A.spend_decomposition(a, b)
@app.get("/api/analytics/real")
def real(months: int = 36): return A.real_vs_nominal(months)
@app.get("/api/analytics/savings")
def savings(months: int = 24): return A.savings_rate_series(months)
@app.get("/api/analytics/distribution")
def dist(days: int = 365): return A.distribution(days)
@app.get("/api/analytics/cohorts")
def cohorts(): return A.merchant_cohorts()
@app.get("/api/goals")
def goals(): return A.goals_status()
@app.post("/api/goals")
def add_goal(g: dict = Body(...)): return _h(tools.add_goal, **g)
@app.delete("/api/goals/{name}")
def del_goal(name: str): store.put("goals", [g for g in store.get("goals", []) if g["name"] != name]); return A.goals_status()
@app.get("/api/budgets")
def budgets(): return A.budgets_status()
@app.post("/api/budgets")
def set_budget(b: dict = Body(...)): return _h(tools.set_budget, b["category"], b["monthly_amount"])
@app.post("/api/categorize")
def categorize(b: dict = Body(...)): return _h(tools.categorize, **b)
@app.post("/api/sql")
def sql(b: dict = Body(...)): return _h(tools.run_sql, b["sql"], b.get("limit", 200))
@app.get("/api/models")
def models(): return agent.models()
@app.post("/api/agent")
def chat(b: dict = Body(...)):
    try:
        return agent.run(b["messages"], b.get("model"), bool(b.get("cloud")))
    except Exception as e:
        raise HTTPException(502, f"Model error: {e}")
@app.get("/api/state/{key}")
def get_state(key: str): return store.get(f"ui_{key}")
@app.put("/api/state/{key}")
def put_state(key: str, v=Body(...)): return store.put(f"ui_{key}", v)


DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{path:path}")
    def spa(path: str):
        f = DIST / path
        return FileResponse(f if path and f.is_file() else DIST / "index.html")


def serve():
    import uvicorn
    uvicorn.run("fw.main:app", host=config.HOST, port=config.PORT)
