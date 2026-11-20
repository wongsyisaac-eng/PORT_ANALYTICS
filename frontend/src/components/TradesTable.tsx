// TradesTable — saved executions, newest first. Uses /trades.

import type { Trade } from "../api";
import { money, num } from "../format";

export default function TradesTable({ trades }: { trades: Trade[] }) {
  if (trades.length === 0) {
    return (
      <p className="empty">
        No trades saved yet. The IB API only returns the current day's trades, so run{" "}
        <code>python backend/sync.py</code> on days you trade.
      </p>
    );
  }

  const newestFirst = [...trades].reverse();

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Time</th><th>Symbol</th><th>Side</th><th>Qty</th><th>Price</th>
            <th>Commission</th><th>Realised PnL</th>
          </tr>
        </thead>
        <tbody>
          {newestFirst.map((t, i) => (
            <tr key={i}>
              <td>{t.time.replace("T", " ").slice(0, 19)}</td>
              <td>{t.symbol}</td>
              <td className={t.side === "BOT" ? "pos" : "neg"}>{t.side === "BOT" ? "Buy" : "Sell"}</td>
              <td>{num(t.shares, 4)}</td>
              <td>{money(t.price)}</td>
              <td>{money(t.commission)}</td>
              <td className={(t.realized_pnl ?? 0) >= 0 ? "pos" : "neg"}>{money(t.realized_pnl)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
