// PositionsTable — current holdings. Uses /positions.
// Click a column header to sort by it; click again to reverse the order.

import { useState } from "react";
import type { Position } from "../api";
import { money, num, pct } from "../format";

// Unrealised gain vs average cost, as a %. For a short, a falling price is a gain.
function unrealised(p: Position): number | null {
  if (!p.avg_cost || p.market_price === null) return null;
  return ((p.market_price - p.avg_cost) / p.avg_cost) * Math.sign(p.quantity);
}

// The table's columns: header text, how to get the sortable value, and how to display it.
const COLUMNS = [
  { key: "symbol", label: "Symbol", value: (p: Position) => p.symbol, show: (p: Position) => p.symbol },
  { key: "quantity", label: "Qty", value: (p: Position) => p.quantity, show: (p: Position) => num(p.quantity, 4) },
  { key: "avg_cost", label: "Avg cost", value: (p: Position) => p.avg_cost, show: (p: Position) => money(p.avg_cost) },
  { key: "market_price", label: "Price", value: (p: Position) => p.market_price, show: (p: Position) => money(p.market_price) },
  { key: "market_value", label: "Market value", value: (p: Position) => p.market_value, show: (p: Position) => money(p.market_value) },
  { key: "unrealised", label: "Unrealised", value: unrealised, show: (p: Position) => pct(unrealised(p)) },
  { key: "weight", label: "Weight", value: (p: Position) => p.weight, show: (p: Position) => pct(p.weight) },
];

export default function PositionsTable({ positions }: { positions: Position[] }) {
  const [sortKey, setSortKey] = useState("weight");
  const [descending, setDescending] = useState(true);

  if (positions.length === 0) return <p className="empty">No positions saved yet.</p>;

  function clickHeader(key: string) {
    if (key === sortKey) setDescending(!descending); // same column: flip direction
    else { setSortKey(key); setDescending(true); }
  }

  const column = COLUMNS.find((c) => c.key === sortKey)!;
  const sorted = [...positions].sort((a, b) => {
    const x = column.value(a) ?? -Infinity;
    const y = column.value(b) ?? -Infinity;
    const order = x < y ? -1 : x > y ? 1 : 0;
    return descending ? -order : order;
  });

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {COLUMNS.map((c) => (
              <th key={c.key} onClick={() => clickHeader(c.key)} className="sortable">
                {c.label} {c.key === sortKey ? (descending ? "▼" : "▲") : ""}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((p) => {
            const u = unrealised(p);
            return (
              <tr key={p.symbol}>
                {COLUMNS.map((c) => (
                  <td
                    key={c.key}
                    className={
                      c.key === "unrealised" && u !== null ? (u >= 0 ? "pos" : "neg")
                      : c.key === "quantity" && p.quantity < 0 ? "neg" : ""
                    }
                  >
                    {c.show(p)}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
