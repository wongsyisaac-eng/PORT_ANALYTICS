// format.ts — turn numbers into display text. Every helper shows "—" for missing values.

const DASH = "—";

// 0.0765 -> "7.65%"
export function pct(x: number | null | undefined, digits = 2): string {
  if (x === null || x === undefined || !Number.isFinite(x)) return DASH;
  return (x * 100).toFixed(digits) + "%";
}

// 1000381.42 -> "1,000,381.42"
export function money(x: number | null | undefined, digits = 2): string {
  if (x === null || x === undefined || !Number.isFinite(x)) return DASH;
  return x.toLocaleString("en-GB", { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

// Plain number with thousands separators and up to `digits` decimals: 1500 -> "1,500"
export function num(x: number | null | undefined, digits = 2): string {
  if (x === null || x === undefined || !Number.isFinite(x)) return DASH;
  return x.toLocaleString("en-GB", { maximumFractionDigits: digits });
}

// Large values for chart axes: 1000381 -> "1.00M"
export function compact(x: number): string {
  return x.toLocaleString("en-GB", { notation: "compact", maximumFractionDigits: 2 });
}
