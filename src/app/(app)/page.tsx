import Link from "next/link";
import { requireUser } from "@/lib/auth";
import { categoryBySlug } from "@/lib/categories";
import { formatKip } from "@/lib/money";
import { computeStats, type TxForStats } from "@/lib/stats";
import { addMonths } from "@/lib/time";
import { DailyChart } from "./charts";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const { supabase } = await requireUser();
  const now = new Date();
  // Last month start, minus a week so "this week" is complete near month start.
  const since = new Date(addMonths(now, -1).getTime() - 7 * 86_400_000).toISOString();
  const { data } = await supabase
    .from("transactions")
    .select("kind, status, occurred_at, amount_lak, category, counterparty_name")
    .gte("occurred_at", since)
    .order("occurred_at", { ascending: false });
  const txs: TxForStats[] = (data ?? []).map((t) => ({ ...t, amount_lak: t.amount_lak === null ? null : Number(t.amount_lak) }));
  const s = computeStats(txs, now);
  const maxCat = s.byCategory[0]?.total || 1;

  return (
    <main className="space-y-4">
      {s.needsReview > 0 && (
        <Link href="/transactions?view=review" className="card flex items-center justify-between bg-amber-50 ring-amber-200">
          <span className="font-medium text-amber-900">
            {s.needsReview} {s.needsReview === 1 ? "receipt needs" : "receipts need"} checking
          </span>
          <span className="text-amber-800">Review →</span>
        </Link>
      )}

      <section className="grid grid-cols-3 gap-3">
        <Stat label="Today" value={s.today} />
        <Stat label="This week" value={s.week} />
        <Stat label="This month" value={s.month} highlight />
      </section>

      <section className="card">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="font-semibold">Compared with last month</h2>
          {s.changeVsLastMonthPct !== null && (
            <span className={`rounded-full px-2 py-0.5 text-sm font-semibold ${s.changeVsLastMonthPct > 0 ? "bg-red-50 text-red-700" : "bg-emerald-50 text-emerald-700"}`}>
              {s.changeVsLastMonthPct > 0 ? "▲" : "▼"} {Math.abs(s.changeVsLastMonthPct)}%
            </span>
          )}
        </div>
        <p className="mt-1 text-sm text-stone-600">
          By this day last month you had spent <b>{formatKip(s.lastMonthSamePeriod)}</b> (whole month: {formatKip(s.lastMonthTotal)}).
        </p>
        <p className="mt-1 text-sm text-stone-600">
          Income this month: <b className="text-emerald-700">{formatKip(s.monthIncome)}</b>
        </p>
      </section>

      <section className="card">
        <h2 className="mb-2 font-semibold">Spending per day</h2>
        <DailyChart data={s.daily} />
      </section>

      <section className="card">
        <h2 className="mb-3 font-semibold">By category</h2>
        {s.byCategory.length === 0 ? (
          <Empty />
        ) : (
          <ul className="space-y-3">
            {s.byCategory.map((c) => {
              const cat = categoryBySlug(c.category);
              return (
                <li key={c.category}>
                  <div className="flex justify-between text-sm">
                    <span>
                      {cat.emoji} {cat.en}
                    </span>
                    <span className="font-medium tabular-nums">{formatKip(c.total)}</span>
                  </div>
                  <div className="mt-1 h-2 overflow-hidden rounded-full bg-stone-100">
                    <div className="h-full rounded-full bg-brand" style={{ width: `${Math.max(2, (c.total / maxCat) * 100)}%` }} />
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </section>

      <section className="card">
        <h2 className="mb-3 font-semibold">Top recipients this month</h2>
        {s.topRecipients.length === 0 ? (
          <Empty />
        ) : (
          <ol className="divide-y divide-stone-100">
            {s.topRecipients.map((r) => (
              <li key={r.name} className="flex justify-between gap-3 py-2 text-sm">
                <span className="min-w-0 truncate">
                  {r.name} <span className="text-stone-400">× {r.count}</span>
                </span>
                <span className="shrink-0 font-medium tabular-nums">{formatKip(r.total)}</span>
              </li>
            ))}
          </ol>
        )}
      </section>
    </main>
  );
}

function Stat({ label, value, highlight }: { label: string; value: number; highlight?: boolean }) {
  return (
    <div className={`card p-3 ${highlight ? "bg-brand text-white ring-0" : ""}`}>
      <div className={`text-xs ${highlight ? "text-white/80" : "text-stone-500"}`}>{label}</div>
      <div className="mt-1 break-words text-base font-bold tabular-nums sm:text-lg">{formatKip(value)}</div>
    </div>
  );
}

function Empty() {
  return (
    <p className="text-sm text-stone-500">
      Nothing yet this month. <Link href="/upload" className="text-brand underline">Add receipts</Link>
    </p>
  );
}
