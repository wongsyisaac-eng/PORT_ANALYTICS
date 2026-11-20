// CorrelationHeatmap — grid of correlations between every pair of holdings. Uses /correlation.
// Red = move together (+1), blue = move opposite (−1), pale = unrelated (0).
// Hover a cell to see the pair and value; its row and column light up.

import { useState } from "react";
import type { Correlation } from "../api";

// Colour for a correlation value: stronger colour for values further from 0.
function cellColour(v: number | null): string {
  if (v === null) return "transparent";
  const strength = Math.min(Math.abs(v), 1) * 0.85;
  return v >= 0 ? `rgba(220, 38, 38, ${strength})` : `rgba(37, 99, 235, ${strength})`;
}

export default function CorrelationHeatmap({ correlation }: { correlation: Correlation }) {
  // Which cell the mouse is over: [row, column], or null when not hovering.
  const [hover, setHover] = useState<[number, number] | null>(null);
  const { symbols, matrix } = correlation;

  if (symbols.length < 2) return <p className="empty">Needs price history for at least 2 holdings.</p>;

  const hovered = hover
    ? `${symbols[hover[0]]} / ${symbols[hover[1]]}: ${matrix[hover[0]][hover[1]]?.toFixed(2) ?? "—"}`
    : "Hover a cell to see the pair";

  return (
    <div>
      <div className="heatmap-readout">{hovered}</div>
      <div className="table-wrap">
        <table className="heatmap" onMouseLeave={() => setHover(null)}>
          <thead>
            <tr>
              <th />
              {symbols.map((s, j) => (
                <th key={s} className={hover?.[1] === j ? "hl" : ""}>{s}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {matrix.map((row, i) => (
              <tr key={symbols[i]}>
                <th className={hover?.[0] === i ? "hl" : ""}>{symbols[i]}</th>
                {row.map((v, j) => (
                  <td
                    key={j}
                    onMouseEnter={() => setHover([i, j])}
                    style={{
                      background: cellColour(v),
                      color: v !== null && Math.abs(v) > 0.55 ? "#fff" : undefined,
                    }}
                    className={hover && (hover[0] === i || hover[1] === j) ? "cross" : ""}
                  >
                    {v === null ? "—" : v.toFixed(2)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="legend-scale">
        <span>−1</span><div className="scale-bar" /><span>+1</span>
      </div>
    </div>
  );
}
