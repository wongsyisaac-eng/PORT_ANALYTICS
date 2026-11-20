// NavChart — line chart of NAV (left axis) and cumulative PnL (right axis) over time.
// Uses /nav. Hover over the chart to see each day's values.

import {
  CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import type { NavRow } from "../api";
import { compact, money } from "../format";

export default function NavChart({ nav }: { nav: NavRow[] }) {
  if (nav.length < 2) {
    return (
      <p className="empty">
        {nav.length} day of NAV saved so far. The chart appears once there are 2 or more days; run{" "}
        <code>python backend/sync.py</code> once a day.
      </p>
    );
  }

  return (
    // ResponsiveContainer makes the chart fill the width of its card.
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={nav} margin={{ top: 8, right: 8, bottom: 0, left: 8 }}>
        <CartesianGrid stroke="var(--grid)" vertical={false} />
        <XAxis dataKey="date" stroke="var(--muted)" fontSize={12} />
        <YAxis yAxisId="nav" stroke="var(--muted)" fontSize={12} tickFormatter={compact}
               domain={["auto", "auto"]} />
        <YAxis yAxisId="pnl" orientation="right" stroke="var(--muted)" fontSize={12}
               tickFormatter={compact} />
        <Tooltip
          formatter={(value) => money(Number(value))}
          contentStyle={{ background: "var(--card)", border: "1px solid var(--border)" }}
        />
        <Legend />
        <Line yAxisId="nav" dataKey="nav" name="NAV" stroke="var(--series-1)" strokeWidth={2} dot={false} />
        <Line yAxisId="pnl" dataKey="cumulative_pnl" name="Cumulative PnL" stroke="var(--series-2)"
              strokeWidth={2} dot={false} connectNulls />
      </LineChart>
    </ResponsiveContainer>
  );
}
