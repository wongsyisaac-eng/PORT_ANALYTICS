# PORT_ANALYTICS

Personal portfolio analytics tool. It pulls positions, trades and prices from Interactive Brokers (read-only), stores them locally in SQLite, computes PnL and risk analytics with pandas, and serves them through FastAPI to a React/TypeScript dashboard.

## Status
- Built: FastAPI hello-world (`backend/main.py`), IB connection test (`backend/ib.py`), settings loader (`backend/env_config.py`), SQLite storage (`backend/storage.py`), IB sync incl. 1Y daily prices (`backend/sync.py`), analytics (`backend/analytics/returns.py`, `risk.py`) with tests in `tests/`, console report (`backend/report.py`), read-only FastAPI endpoints serving SQLite data (`backend/routers/portfolio.py`: /positions, /trades, /nav, /returns, /risk, /correlation), React dashboard (`frontend/`: KPI cards, NAV/PnL chart, weights chart, sortable positions table, correlation heatmap, trades table).
- Planned, in order: notebook exploration, Flex Query backfill of NAV/trades, second-platform adapter (Trading 212, on hold).

## Stack
- Python in the conda environment `port_analytics`. Always run Python through it (`conda activate port_analytics`).
  - Interpreter path: `/opt/anaconda3/envs/port_analytics/bin/python` (Python 3.14). In VS Code, select it via *Python: Select Interpreter*.
  - Do not use `/usr/bin/python3` (macOS system Python 3.9) or conda `base`; neither has `ib_async`, so imports fail with `ModuleNotFoundError`.
- ib_async, pandas, numpy, scipy, FastAPI, uvicorn, python-dotenv, SQLite (stdlib `sqlite3`), pytest.
- Frontend: Vite + React + TypeScript, Recharts for charts. Node via Homebrew. API calls only in `frontend/src/api.ts`.

## Commands
- Activate: `conda activate port_analytics`
- IB connection test (TWS or Gateway must be open and logged in): `python backend/ib.py`
- API server: `cd backend && fastapi dev main.py` (docs at http://127.0.0.1:8000/docs)
- Sync from IB into SQLite (run daily, Gateway open): `python backend/sync.py`
- Report from SQLite (no IB connection): `python backend/report.py`
- Dashboard (API must be running): `cd frontend && npm install` once, then `npm run dev` (http://localhost:5173). Check: `npm run build && npm run lint`
- Tests: `pytest`
- Save environment: `conda env export --from-history > environment.yml`
- Ports: TWS paper 7497, TWS live 7496, Gateway paper 4002, Gateway live 4001. The port comes from `.env`, never hardcoded.

## Target layout
```
backend/   main.py, env_config.py, ib.py, storage.py, sync.py,
           analytics/ (pnl.py, risk.py), routers/
tests/     pytest tests using synthetic data
notebooks/ exploration only; move working code into backend/
data/      SQLite file and exports (git-ignored)
frontend/  Vite React + TypeScript
```

## Hard rules
- **Read-only.** Never write code that calls `placeOrder`, `cancelOrder` or modifies orders or accounts. The IB API setting "Read-Only API" stays ticked.
- **Paper account or synthetic data by default.** Use the live account only when I explicitly say so.
- **Never read, print, log or commit** `.env`, anything in `data/`, `*.csv`, `*.db`, account IDs, balances or API keys. Use synthetic fixtures in tests, notebooks and examples.
- No hardcoded host, port, clientId or account ID. Load settings from `env_config.py`.
- Do not commit or push unless I ask. Never force-push. Do not weaken `.gitignore`.
- Clear notebook outputs before any commit.

## Conventions
- Type hints on all functions. Small pure functions in `analytics/` that import neither `ib_async` nor FastAPI, so they can be tested alone.
- Endpoints stay thin: fetch data, call an analytics function, return the result.
- One IB connection per process, with a unique clientId (server uses 1, notebooks use 2 and up). Use `connectAsync` inside FastAPI, and `util.startLoop()` in notebooks.
- Saves must be idempotent: executions are keyed by `execId` with `INSERT OR IGNORE`.
- JSON responses: dates as ISO strings, NaN converted to `null`.
- CORS allows only `http://localhost:5173`, never `*`. The server listens on 127.0.0.1 only.
- Test analytics on small synthetic cases whose answers can be checked by hand.

## Decisions made (details in README)
PnL from IB daily NAV; both time-weighted and money-weighted returns; cost basis = IB's own realised PnL; cash flows at start of day; std and correlation from ~1Y of adjusted daily prices with today's weights; prices in local currency (FX ignored).

## Open decisions (ask me before choosing)
Currency treatment for multi-currency portfolios. Record any choice in the relevant docstring and in the README.

## Working style
- I am learning, so explain non-obvious choices in a sentence and prefer simple, readable code over clever code.
- I do not know JavaScript. Keep frontend code simple and well commented.
- British spelling in prose and docs.
