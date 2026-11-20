// App.tsx — the whole dashboard page.
// It loads data from the API once, keeps it in "state", and passes pieces of it
// to each section component as "props" (inputs, like function arguments).

import { useEffect, useState } from "react";
import { API_URL, fetchDashboard } from "./api";
import type { Dashboard } from "./api";
import KpiCards from "./components/KpiCards";
import NavChart from "./components/NavChart";
import WeightsChart from "./components/WeightsChart";
import PositionsTable from "./components/PositionsTable";
import CorrelationHeatmap from "./components/CorrelationHeatmap";
import TradesTable from "./components/TradesTable";

export default function App() {
  // useState creates a value React remembers between renders.
  // Calling the setter (e.g. setData) updates it and redraws the page.
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Fetch everything, then store the result (or the error) in state.
  // `.then` / `.catch` / `.finally` run once the data has arrived (or failed).
  function fetchAndStore() {
    return fetchDashboard()
      .then((dashboard) => {
        setData(dashboard);
        setError(null);
      })
      .catch(() => setError(`Can't reach the API at ${API_URL}.`))
      .finally(() => setLoading(false));
  }

  // The Refresh button: show "Loading…", then fetch again.
  function refresh() {
    setLoading(true);
    fetchAndStore();
  }

  // useEffect runs code after the page first appears. The empty list [] means
  // "only once", so the data is fetched when the dashboard opens.
  useEffect(() => {
    fetchAndStore();
  }, []);

  const asOf = data?.nav.at(-1)?.date; // "?." means: stop and give undefined if missing

  return (
    <main className="page">
      <header className="page-header">
        <div>
          <h1>Portfolio dashboard</h1>
          <p className="muted">
            Interactive Brokers paper account{asOf ? ` · data as of ${asOf}` : ""}
          </p>
        </div>
        <button onClick={refresh} disabled={loading}>
          {loading ? "Loading…" : "Refresh"}
        </button>
      </header>

      {/* Curly braces in JSX run TypeScript. `cond && <X/>` shows X only if cond is true. */}
      {error && (
        <div className="notice error">
          <strong>{error}</strong>
          <p>
            Start it with <code>cd backend &amp;&amp; fastapi dev main.py</code>, then press Refresh.
          </p>
        </div>
      )}

      {data && (
        <>
          <KpiCards nav={data.nav} returns={data.returns} risk={data.risk} />

          <section className="card">
            <h2>NAV and cumulative PnL</h2>
            <NavChart nav={data.nav} />
          </section>

          <div className="two-col">
            <section className="card">
              <h2>Weights (share of NAV)</h2>
              <WeightsChart weights={data.risk.weights} />
            </section>
            <section className="card">
              <h2>Correlation of daily returns</h2>
              <CorrelationHeatmap correlation={data.correlation} />
            </section>
          </div>

          <section className="card">
            <h2>Positions</h2>
            <PositionsTable positions={data.positions} />
          </section>

          <section className="card">
            <h2>Trading history</h2>
            <TradesTable trades={data.trades} />
          </section>
        </>
      )}
    </main>
  );
}
