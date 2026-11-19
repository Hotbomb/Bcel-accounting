import { describe, expect, it } from "vitest";
import { computeStats, type TxForStats } from "@/lib/stats";
import { formatKip, parseAmountInput } from "@/lib/money";
import { monthKey, parseLocalDateTime, startOfWeek } from "@/lib/time";

const tx = (occurred_at: string, amount: number, extra: Partial<TxForStats> = {}): TxForStats => ({
  kind: "expense",
  status: "confirmed",
  occurred_at,
  amount_lak: amount,
  category: "food",
  counterparty_name: "Shop A",
  ...extra,
});

describe("computeStats", () => {
  // Thursday 19 Nov 2026, 12:00 in Vientiane
  const now = new Date("2026-11-19T05:00:00Z");
  const s = computeStats(
    [
      tx("2026-11-19T01:00:00Z", 30000), // today 08:00
      tx("2026-11-16T03:00:00Z", 50000, { category: "transport", counterparty_name: "Fuel" }), // Monday
      tx("2026-11-02T03:00:00Z", 100000), // earlier this month
      tx("2026-10-10T03:00:00Z", 90000), // last month, same period
      tx("2026-10-25T03:00:00Z", 70000), // last month, later
      tx("2026-11-18T03:00:00Z", 333340, { kind: "own_transfer" }), // must not count
      tx("2026-11-05T03:00:00Z", 2000000, { kind: "income", category: "salary" }),
      tx("2026-11-18T05:00:00Z", 10000, { status: "needs_review" }),
    ],
    now,
  );

  it("totals today, week and month in Vientiane time, ignoring own transfers", () => {
    expect(s.today).toBe(30000);
    expect(s.week).toBe(90000);
    expect(s.month).toBe(190000);
    expect(s.monthIncome).toBe(2000000);
    expect(s.needsReview).toBe(1);
  });

  it("compares with the same point last month", () => {
    expect(s.lastMonthSamePeriod).toBe(90000);
    expect(s.lastMonthTotal).toBe(160000);
    expect(s.changeVsLastMonthPct).toBe(111);
  });

  it("ranks categories and recipients", () => {
    expect(s.byCategory[0]).toEqual({ category: "food", total: 140000 });
    expect(s.topRecipients[0].name).toBe("Shop A");
    expect(s.daily).toHaveLength(19);
  });
});

describe("formatting and time", () => {
  it("formats kip", () => {
    expect(formatKip(125000)).toBe("125,000 ₭");
    expect(parseAmountInput("125,000")).toBe(125000);
    expect(parseAmountInput("abc")).toBeNull();
  });
  it("uses Vientiane time for month and week boundaries", () => {
    expect(monthKey(new Date("2026-11-30T18:00:00Z"))).toBe("2026-12"); // 01:00 on 1 Dec in Laos
    expect(startOfWeek(new Date("2026-11-19T05:00:00Z")).toISOString()).toBe("2026-11-15T17:00:00.000Z");
    expect(parseLocalDateTime("2026-11-18T20:40")?.toISOString()).toBe("2026-11-18T13:40:00.000Z");
  });
});
