// KpiCards — the row of headline numbers at the top.
// Uses /nav (latest NAV), /returns (TWR, MWR) and /risk (std, weights).

import type { NavRow, Returns, Risk } from "../api";
import { money, pct } from "../format";

// The props this component expects. App.tsx passes them in like <KpiCards nav={...} />.
type Props = { nav: NavRow[]; returns: Returns; risk: Risk };

// One card. `note` is the small grey line under the value.
function Kpi({ label, value, note }: { label: string; value: string; note?: string }) {
  return (
    <div className="kpi">
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{value}</div>
      {note && <div className="kpi-note">{note}</div>}
    </div>
  );
}

export default function KpiCards({ nav, returns, risk }: Props) {
  const latest = nav.at(-1);
  // Invested share = sum of absolute weights (shorts count as invested too).
  const invested = risk.weights.reduce((sum, w) => sum + Math.abs(w.weight ?? 0), 0);
  const needsHistory = "needs 2+ days of NAV";

  return (
    <div className="kpis">
      <Kpi label="NAV" value={money(latest?.nav)} note={latest?.date} />
      <Kpi label="Invested" value={pct(invested, 1)} note={`${pct(1 - invested, 1)} cash`} />
      <Kpi
        label="Std (ex-ante, annual)"
        value={pct(risk.ex_ante_annual)}
        note={`daily ${pct(risk.ex_ante_daily)} · ${risk.price_days} days of prices`}
      />
      <Kpi
        label="Std (realised, annual)"
        value={pct(risk.realised_annual)}
        note={risk.realised_annual === null ? "needs 20+ days of NAV" : `daily ${pct(risk.realised_daily)}`}
      />
      <Kpi
        label="Time-weighted return"
        value={pct(returns.twr_total)}
        note={returns.twr_total === null ? needsHistory : `since ${returns.start_date}`}
      />
      <Kpi
        label="Money-weighted return"
        value={pct(returns.mwr)}
        note={returns.mwr === null ? needsHistory : `since ${returns.start_date}`}
      />
    </div>
  );
}
