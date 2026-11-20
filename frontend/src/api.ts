// api.ts — the ONLY file that talks to the backend.
//
// Each `type` below describes the JSON one FastAPI endpoint returns, so TypeScript
// can warn us if we use a field that doesn't exist. `number | null` means the
// backend may send null (e.g. returns before there are 2 days of NAV).

// The API address. Can be changed with a VITE_API_URL line in frontend/.env.
export const API_URL: string = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

export type Position = {
  symbol: string;
  quantity: number;
  avg_cost: number | null;
  market_price: number | null;
  market_value: number | null;
  currency: string | null;
  weight: number | null; // market value as a share of NAV (negative = short)
};

export type Trade = {
  time: string;
  symbol: string;
  side: string; // "BOT" (bought) or "SLD" (sold)
  shares: number;
  price: number;
  commission: number | null;
  realized_pnl: number | null; // IB's own figure; null for opening trades
};

export type NavRow = {
  date: string;
  nav: number;
  daily_pnl: number | null;
  cumulative_pnl: number | null;
  twr_daily: number | null;
  twr_cumulative: number | null;
};

export type Returns = {
  start_date: string | null;
  end_date: string | null;
  days: number;
  twr_total: number | null;
  mwr: number | null;
};

export type Risk = {
  ex_ante_daily: number | null;
  ex_ante_annual: number | null;
  price_days: number;
  realised_daily: number | null;
  realised_annual: number | null;
  weights: { symbol: string; weight: number | null }[];
};

export type Correlation = {
  symbols: string[];
  matrix: (number | null)[][]; // matrix[i][j] = correlation of symbols[i] and symbols[j]
};

// Everything the dashboard needs, bundled together.
export type Dashboard = {
  positions: Position[];
  trades: Trade[];
  nav: NavRow[];
  returns: Returns;
  risk: Risk;
  correlation: Correlation;
};

// Fetch one endpoint and parse its JSON. `async` functions return a Promise:
// a value that arrives later, which callers wait for with `await`.
async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(API_URL + path);
  if (!response.ok) {
    throw new Error(`${path} returned HTTP ${response.status}`);
  }
  return (await response.json()) as T;
}

// Fetch all six endpoints at the same time (Promise.all runs them in parallel).
export async function fetchDashboard(): Promise<Dashboard> {
  const [positions, trades, nav, returns, risk, correlation] = await Promise.all([
    getJson<Position[]>("/positions"),
    getJson<Trade[]>("/trades"),
    getJson<NavRow[]>("/nav"),
    getJson<Returns>("/returns"),
    getJson<Risk>("/risk"),
    getJson<Correlation>("/correlation"),
  ]);
  return { positions, trades, nav, returns, risk, correlation };
}
