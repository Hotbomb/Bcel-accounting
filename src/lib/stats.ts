import { addMonths, dayKey, startOfDay, startOfMonth, startOfWeek, vientianeParts } from "./time";

export interface TxForStats {
  kind: "expense" | "income" | "own_transfer";
  status: "confirmed" | "needs_review";
  occurred_at: string;
  amount_lak: number | null;
  category: string;
  counterparty_name: string | null;
}

export interface DashboardStats {
  today: number;
  week: number;
  month: number;
  monthIncome: number;
  lastMonthSamePeriod: number;
  lastMonthTotal: number;
  /** Positive = spending more than last month at this point. null when last month is 0. */
  changeVsLastMonthPct: number | null;
  byCategory: Array<{ category: string; total: number }>;
  topRecipients: Array<{ name: string; total: number; count: number }>;
  daily: Array<{ day: string; label: string; total: number }>;
  needsReview: number;
}

/**
 * Spending = expenses (not transfers between your own accounts). Items still
 * waiting for review are counted too, so nothing is hidden; the dashboard
 * shows how many need checking.
 */
export function computeStats(txs: TxForStats[], now: Date = new Date()): DashboardStats {
  const dayStart = startOfDay(now).getTime();
  const weekStart = startOfWeek(now).getTime();
  const monthStart = startOfMonth(now).getTime();
  const lastMonthStart = addMonths(now, -1).getTime();
  // Same point in last month (e.g. 1st-18th), capped at the end of last month.
  const p = vientianeParts(now);
  const elapsed = now.getTime() - monthStart;
  const lastMonthSameMoment = Math.min(lastMonthStart + elapsed, monthStart);

  let today = 0,
    week = 0,
    month = 0,
    monthIncome = 0,
    lastMonthSamePeriod = 0,
    lastMonthTotal = 0,
    needsReview = 0;
  const byCategory = new Map<string, number>();
  const recipients = new Map<string, { total: number; count: number }>();
  const daily = new Map<string, number>();

  for (const t of txs) {
    if (t.status === "needs_review") needsReview++;
    const time = new Date(t.occurred_at).getTime();
    const amt = t.amount_lak ?? 0;
    if (t.kind === "income") {
      if (time >= monthStart) monthIncome += amt;
      continue;
    }
    if (t.kind !== "expense") continue;

    if (time >= monthStart) {
      month += amt;
      if (time >= weekStart) week += amt;
      if (time >= dayStart) today += amt;
      byCategory.set(t.category, (byCategory.get(t.category) ?? 0) + amt);
      const name = t.counterparty_name?.trim() || "Unknown";
      const r = recipients.get(name) ?? { total: 0, count: 0 };
      r.total += amt;
      r.count++;
      recipients.set(name, r);
      const k = dayKey(new Date(time));
      daily.set(k, (daily.get(k) ?? 0) + amt);
    } else if (time >= lastMonthStart) {
      lastMonthTotal += amt;
      if (time < lastMonthSameMoment) lastMonthSamePeriod += amt;
    }
    // The current week can start in last month; include those days in "week".
    if (time < monthStart && time >= weekStart) week += amt;
  }

  const days: DashboardStats["daily"] = [];
  for (let d = 1; d <= p.day; d++) {
    const k = `${p.year}-${String(p.month).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
    days.push({ day: k, label: String(d), total: daily.get(k) ?? 0 });
  }

  return {
    today,
    week,
    month,
    monthIncome,
    lastMonthSamePeriod,
    lastMonthTotal,
    changeVsLastMonthPct:
      lastMonthSamePeriod > 0 ? Math.round(((month - lastMonthSamePeriod) / lastMonthSamePeriod) * 100) : null,
    byCategory: [...byCategory.entries()]
      .map(([category, total]) => ({ category, total }))
      .sort((a, b) => b.total - a.total),
    topRecipients: [...recipients.entries()]
      .map(([name, v]) => ({ name, ...v }))
      .sort((a, b) => b.total - a.total)
      .slice(0, 5),
    daily: days,
    needsReview,
  };
}
