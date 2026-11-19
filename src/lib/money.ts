const SYMBOLS: Record<string, string> = { LAK: "₭", THB: "฿", USD: "$" };

/** 125000 -> "125,000 ₭" */
export function formatMoney(amount: number | null | undefined, currency = "LAK"): string {
  if (amount === null || amount === undefined || Number.isNaN(amount)) return "—";
  const decimals = currency === "LAK" ? 0 : 2;
  const text = new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 0,
    maximumFractionDigits: decimals,
  }).format(amount);
  return `${text} ${SYMBOLS[currency] ?? currency}`;
}

export function formatKip(amount: number | null | undefined): string {
  return formatMoney(amount, "LAK");
}

/** Accepts "125,000" or "125000" from a form field. */
export function parseAmountInput(s: string): number | null {
  const cleaned = s.replace(/[,\s₭]/g, "");
  if (!/^\d+(\.\d{1,2})?$/.test(cleaned)) return null;
  const n = Number(cleaned);
  return Number.isFinite(n) ? n : null;
}
