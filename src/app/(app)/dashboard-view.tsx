import Link from "next/link";
import { categoryBySlug } from "@/lib/categories";
import { formatKip } from "@/lib/money";
import type { DashboardStats } from "@/lib/stats";
import { DailyChart } from "./charts";

export function DashboardView({ s }: { s: DashboardStats }) {
  const maxCat = s.byCategory[0]?.total || 1;

  return (
    <main className="space-y-4">
      {s.needsReview > 0 && (
        <Link href="/transactions?view=review" className="card flex items-center justify-between border-amber-200/70 !bg-amber-50/75">
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
            <span className={`rounded-full px-2 py-0.5 text-sm font-semibold ${s.changeVsLastMonthPct > 0 ? "bg-red-100/80 text-red-800" : "bg-emerald-100/80 text-emerald-800"}`}>
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
                  <div className="mt-1 h-2 overflow-hidden rounded-full bg-white/70 shadow-[inset_0_1px_2px_rgb(120_10_20/0.08)]">
                    <div className="h-full rounded-full bg-gradient-to-r from-brand to-[#e2444c]" style={{ width: `${Math.max(2, (c.total / maxCat) * 100)}%` }} />
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
          <ol className="divide-y divide-white/70">
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
    <div className={`${highlight ? "glass-red rounded-3xl p-3" : "card p-3"}`}>
      <div className={`text-xs ${highlight ? "text-white/85" : "text-ink/60"}`}>{label}</div>
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
