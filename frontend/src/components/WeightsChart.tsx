// WeightsChart — horizontal bars of each holding's share of NAV.
// Uses /risk (weights). Green = long, red = short. Hover a bar to see the exact %.

import { Bar, BarChart, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Risk } from "../api";
import { pct } from "../format";

export default function WeightsChart({ weights }: { weights: Risk["weights"] }) {
  if (weights.length === 0) return <p className="empty">No positions saved yet.</p>;

  // Biggest weight first. [...x] copies the list so we don't change the original.
  const data = [...weights]
    .map((w) => ({ symbol: w.symbol, weight: w.weight ?? 0 }))
    .sort((a, b) => b.weight - a.weight);

  return (
    <ResponsiveContainer width="100%" height={Math.max(160, data.length * 26)}>
      <BarChart data={data} layout="vertical" margin={{ top: 0, right: 16, bottom: 0, left: 0 }}>
        <XAxis type="number" tickFormatter={(v) => pct(v, 0)} stroke="var(--muted)" fontSize={12} />
        <YAxis type="category" dataKey="symbol" width={56} stroke="var(--muted)" fontSize={12} />
        <ReferenceLine x={0} stroke="var(--border)" />
        <Tooltip
          formatter={(value) => pct(Number(value))}
          cursor={{ fill: "var(--hover)" }}
          contentStyle={{ background: "var(--card)", border: "1px solid var(--border)" }}
        />
        <Bar dataKey="weight" name="Weight" radius={3}>
          {/* .map draws one coloured Cell per bar. `key` helps React track each item. */}
          {data.map((d) => (
            <Cell key={d.symbol} fill={d.weight >= 0 ? "var(--long)" : "var(--short)"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
