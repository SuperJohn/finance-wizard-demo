# Demo data (Finance Lab)

A complete **synthetic** personal-finance dataset for demos, screenshots and the static showcase. **All fictional:** a
made-up person ("Jordan Demo"), invented institutions ("Demo Bank", "Demo Card Co", …) and merchants, twelve months
from 2025-11-01 to 2026-10-28. No real accounts, balances, merchants or notes; nothing is derived from real data.

| File | What it is | Rows |
|---|---|---|
| `accounts.json` | Accounts with short display names (the `account` key used everywhere), institution, type/subtype, class (`cash`/`investment`/`property`/`liability`) and latest balance. | 7 |
| `categories.json` | Category → group → kind (income / expense / transfer), matching the app's income/transfer sets. | 30 |
| `transactions.json` | `fw.txns` shape: `txn_id`, `short_id` (`T-XXXXX`), `date`, `merchant`, `category`, `account`, `amount` (negative = outflow), `tags`, `notes`, `kind`. Includes payroll, rent, card spend with seasonality, subscriptions with price creep, transfers, card payoffs, freelance income, a refund, a duplicate charge and a large one-off. | 659 |
| `balances.json` | `fw.balances` shape (`date`, `account`, `balance`, `klass`), weekly on Sundays. | 364 |
| `net_worth.json` | Month-end composition: cash, investment, property, liability, net worth. | 12 |
| `cashflow.json` | Monthly income, spend, net and savings rate (transfers excluded, refunds net against spend). | 12 |
| `recurring.json` | Recurring bills: cadence, last/first amount, price creep %, annualized cost, next expected charge. | 10 |
| `budgets.json` | Monthly budgets by category plus spent-vs-budget for every month. | 8 budgets, 96 rows |
| `goals.json` | Goals tracked against cash / investment / liability, with current values. | 4 |
| `scenarios.json` | Runway scenarios in the Scenarios page shape (`name`, `lump`, `lumpM`, `income`, `incomeStart`, `extra`, `on`). | 6 |
| `notes.json` | Transaction comments and labels keyed by `txn_id`. | 6 |
| `app_state.json` | Drop-in `data/app_state.json` (goals, budgets, merchant rules, dashboard layout, scenarios). | |
| `manifest.json` | Row counts, byte sizes and sha256. | |

Regenerate (seeded, stdlib only, byte-identical): `python3 demo/generate_data.py`.

**Local override.** The live app reads your local finance lake (never committed). Point demo tooling at this folder or
at your own export on the Studio with `HL_DATASET_URI` (e.g. `HL_DATASET_URI=file://…/demo/data`); to see the demo
state in the app, copy `app_state.json` to `data/app_state.json` (git-ignored).

`.gitignore` ignores every `data/` folder except this one (`!demo/data/`). Never put real exports here.
