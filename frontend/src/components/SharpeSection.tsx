// SharpeSection — annualised Sharpe ratio of the account's daily time-weighted returns.
// Uses /sharpe. Shows a hint until there are enough days of NAV history.

import type { Sharpe } from "../api";
import { pct } from "../format";

export default function SharpeSection({ sharpe }: { sharpe: Sharpe }) {
  if (sharpe.annual === null) {
    return (
      <p className="empty">
        Needs {sharpe.min_observations}+ daily returns; {sharpe.observations} so far. Run{" "}
        <code>python backend/sync.py</code> once a day.
      </p>
    );
  }
  return (
    <div className="kpis">
      <div className="kpi">
        <div className="kpi-label">Sharpe (annualised)</div>
        <div className="kpi-value">{sharpe.annual.toFixed(2)}</div>
        <div className="kpi-note">
          daily {sharpe.daily?.toFixed(3)} · risk-free {pct(sharpe.risk_free_annual)} · {sharpe.observations} days
        </div>
      </div>
    </div>
  );
}
