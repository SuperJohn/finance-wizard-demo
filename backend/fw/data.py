"""Read-only access to the finance lake.

We never open the live lake file (another process may hold the write lock).
Instead we copy it to data/lake_snapshot.duckdb (gitignored) and ATTACH it
READ_ONLY as catalog `lake` (dbt views reference that catalog name).
Canonical app views live in an in-memory DuckDB on top:
  fw.txns(txn_id, date, merchant, category, account, amount, tags, notes, kind)
  fw.balances(date, account, balance, klass)
"""
import shutil
import threading
import time
import duckdb
import numpy as np
import pandas as pd
from . import config, fixtures

INCOME_CATS = {"Income", "Paychecks", "Other Income", "Interest", "Dividends & Capital Gains", "Business Income", "INCOME"}
TRANSFER_CATS = {"Transfer", "Credit Card Payment", "Loan Repayment", "Balance Adjustments", "Buy", "Sell"}
_lock = threading.RLock()
_state = {"con": None, "source": None, "loaded_at": None}

LIAB_HINTS = ("card", "mortgage", "loan", "visa", "credit")


def _klass(account: str) -> str:
    a = (account or "").lower()
    if any(h in a for h in LIAB_HINTS):
        return "liability"
    if any(h in a for h in ("ira", "invst", "brokerage", "401k", "roth")):
        return "investment"
    if any(h in a for h in ("property", "home", "vehicle")):
        return "property"
    return "cash"


def _build_views(con, tx: pd.DataFrame, bal: pd.DataFrame):
    tx = tx.copy()
    if "is_transfer" not in tx:
        tx["is_transfer"] = tx["category"].isin(TRANSFER_CATS)
    tr = tx["is_transfer"].fillna(False).astype(bool) | tx["category"].isin(TRANSFER_CATS)
    is_inc = tx["category"].isin(INCOME_CATS)
    # positive amounts outside income categories are refunds/credits: they net against spend, not income
    # lake flag (fact_transaction.is_refund) wins: card/loan credits are refunds even when the provider tags them INCOME_*
    if "is_refund" in tx:
        is_inc = is_inc & ~tx["is_refund"].fillna(False).astype(bool)
    tx["kind"] = np.where(tr, "transfer", np.where(tx["amount"] < 0, "expense", np.where(is_inc, "income", "refund")))
    tx.loc[tx["amount"] == 0, "kind"] = "transfer"
    # a refund nets against the category its merchant is usually charged under (not "Income"/"Other")
    exp = tx[tx["kind"] == "expense"]
    if len(exp):
        dom = exp.groupby("merchant")["category"].agg(lambda c: c.value_counts().index[0])
        rf = (tx["kind"] == "refund") & tx["merchant"].isin(dom.index)
        tx.loc[rf, "category"] = tx.loc[rf, "merchant"].map(dom)
    bal = bal.copy()
    if "klass" not in bal:
        bal["klass"] = bal["account"].map(_klass)
    con.execute("CREATE SCHEMA IF NOT EXISTS fw")
    con.register("_tx", tx)
    con.register("_bal", bal)
    con.execute("CREATE OR REPLACE TABLE fw.txns AS SELECT txn_id, CAST(date AS DATE) date, CAST(merchant AS VARCHAR) merchant, CAST(category AS VARCHAR) category, CAST(account AS VARCHAR) account, CAST(amount AS DOUBLE) amount, CAST(tags AS VARCHAR) tags, CAST(notes AS VARCHAR) notes, kind FROM _tx")
    con.execute("CREATE OR REPLACE TABLE fw.balances AS SELECT CAST(date AS DATE) date, account, CAST(balance AS DOUBLE) balance, klass FROM _bal")
    con.unregister("_tx"); con.unregister("_bal")


def load(force_fixture: bool | None = None):
    use_fixture = config.FIXTURE if force_fixture is None else force_fixture
    con = duckdb.connect(":memory:")
    source = "fixture"
    nw = None
    if not use_fixture and config.LAKE_PATH.exists():
        snap = config.DATA_DIR / "lake_snapshot.duckdb"
        try:
            shutil.copy2(config.LAKE_PATH, snap)
            wal = config.LAKE_PATH.with_suffix(".duckdb.wal")
            if wal.exists():
                shutil.copy2(wal, snap.with_suffix(".duckdb.wal"))
            con.execute(f"ATTACH '{snap}' AS lake (READ_ONLY)")
            tx, bal, nw = _from_models(con)
            source = f"lake models:{config.LAKE_PATH.name}"
            if len(tx) == 0:
                raise RuntimeError("lake has no transactions yet")
        except Exception as e:  # lake not ready -> fixture
            nw = None
            print(f"[fw] lake unavailable ({e}); using fixture data")
            tx, bal = fixtures.build()
    else:
        tx, bal = fixtures.build()
    _apply_overrides(tx)
    _build_views(con, tx, bal)
    if nw is not None:
        con.register("_nw", nw)
        con.execute("CREATE OR REPLACE TABLE fw.net_worth AS SELECT * FROM _nw")
        con.unregister("_nw")
    with _lock:
        _state.update(con=con, source=source, loaded_at=time.time())
    return con


def _apply_overrides(tx: pd.DataFrame):
    from . import store
    ov = store.get("category_overrides", {})
    rules = store.get("merchant_rules", {})
    if rules:
        m = tx["merchant"].map(lambda x: rules.get((x or "").lower()))
        tx.loc[m.notna(), "category"] = m[m.notna()]
    if ov:
        m = tx["txn_id"].map(ov)
        tx.loc[m.notna(), "category"] = m[m.notna()]


def con():
    with _lock:
        if _state["con"] is None:
            load()
        return _state["con"].cursor()


def info():
    return {"source": _state["source"], "loaded_at": _state["loaded_at"]}


def q(sql: str, params=None) -> pd.DataFrame:
    return con().execute(sql, params or []).df()


PLAID_PRETTY = {"FOOD_AND_DRINK": "Food & Drink", "GENERAL_MERCHANDISE": "Shopping", "GENERAL_SERVICES": "Services",
    "RENT_AND_UTILITIES": "Rent & Utilities", "TRANSPORTATION": "Transportation", "ENTERTAINMENT": "Entertainment & Recreation",
    "HOME_IMPROVEMENT": "Home Improvement", "MEDICAL": "Medical", "PERSONAL_CARE": "Personal Care", "TRAVEL": "Travel & Vacation",
    "BANK_FEES": "Financial Fees", "GOVERNMENT_AND_NON_PROFIT": "Gov & Non-profit", "INCOME": "Income", "LOAN_PAYMENTS": "Loan Payments",
    "TRANSFER_IN": "Transfer", "TRANSFER_OUT": "Transfer", "OTHER": "Other"}
CARD_PAYMENT_CATS = {"LOAN_PAYMENTS", "Credit Card Payment", "Loan Payments", "TRANSFER_IN"}


def _from_models(con):
    """Read the Finance Lake dbt models: core.fact_transaction_enriched (deduplicated provider rows with the lake's
    transfer/refund flags and user enrichment), core.fact_balance_snapshot + core.dim_account, marts.net_worth."""
    tx = con.execute("""
        SELECT t.txn_id, t.date_key AS date,
               coalesce(t.merchant_name, t.description_raw) AS merchant,
               coalesce(t.category_primary, 'Uncategorized') AS category, t.category_primary AS raw_category,
               trim(concat_ws(' ', t.institution, t.account_name, CASE WHEN t.last4 IS NOT NULL THEN '…' || t.last4 END)) AS account,
               CAST(t.amount AS DOUBLE) AS amount,
               array_to_string(coalesce(t.tags, []), ', ') AS tags,
               t.notes, t.is_internal_transfer AS is_transfer, t.is_refund, t.account_class AS acct_class, t.source
        FROM lake.core.fact_transaction_enriched t WHERE NOT t.pending""").df()
    # Narrow supplement to the lake flag: payments received on a card/loan account are transfers, not income.
    pay = (tx["acct_class"] == "liability") & (tx["amount"] > 0) & (
        tx["raw_category"].isin(CARD_PAYMENT_CATS) | tx["category"].isin(CARD_PAYMENT_CATS)
        | tx["merchant"].fillna("").str.contains(r"PAYMENT.*THANK|AUTOPAY|AUTOMATIC PAYMENT|ONLINE PAYMENT", case=False, regex=True))
    tx.loc[pay, "is_transfer"] = True
    tx.loc[pay, "is_refund"] = False
    tx["category"] = tx["category"].map(lambda c: PLAID_PRETTY.get(c, c))
    bal = con.execute("""
        SELECT b.snapshot_date AS date,
               trim(concat_ws(' ', a.institution, a.account_name, CASE WHEN a.last4 IS NOT NULL THEN '…' || a.last4 END)) AS account,
               CAST(b.current_balance AS DOUBLE) AS balance, coalesce(a.account_class, b.account_class) AS klass
        FROM lake.core.fact_balance_snapshot b JOIN lake.core.dim_account a ON a.account_id = b.account_id AND a.is_current""").df()
    nw = con.execute("""SELECT snapshot_date AS date, CAST(cash AS DOUBLE) cash, CAST(investments AS DOUBLE) investment,
               CAST(coalesce(property, 0) AS DOUBLE) property, -CAST(liabilities AS DOUBLE) liability, CAST(net_worth AS DOUBLE) net_worth
        FROM lake.marts.net_worth ORDER BY 1""").df()
    return tx.drop(columns=["raw_category", "acct_class", "source"]), bal, nw


def has_table(name: str) -> bool:
    sch, t = name.split(".")
    return con().execute("SELECT count(*) FROM information_schema.tables WHERE table_schema=? AND table_name=?", [sch, t]).fetchone()[0] > 0
