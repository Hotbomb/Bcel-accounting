import Link from "next/link";
import { requireUser } from "@/lib/auth";
import { CATEGORIES, categoryBySlug } from "@/lib/categories";
import { formatKip, formatMoney } from "@/lib/money";
import { dayKey, vientianeParts } from "@/lib/time";
import { confirmTransaction } from "../actions";

export const dynamic = "force-dynamic";

interface Search {
  view?: string;
  q?: string;
  kind?: string;
  category?: string;
}

export default async function TransactionsPage({ searchParams }: { searchParams: Promise<Search> }) {
  const sp = await searchParams;
  const { supabase } = await requireUser();

  let query = supabase
    .from("transactions")
    .select("id, kind, status, review_reasons, occurred_at, amount, currency, amount_lak, category, counterparty_name, memo, source")
    .order("occurred_at", { ascending: false })
    .limit(300);
  if (sp.view === "review") query = query.eq("status", "needs_review");
  if (sp.kind && ["expense", "income", "own_transfer"].includes(sp.kind)) query = query.eq("kind", sp.kind);
  if (sp.category && CATEGORIES.some((c) => c.slug === sp.category)) query = query.eq("category", sp.category);
  const q = sp.q?.trim().slice(0, 100);
  if (q) {
    // Escape characters that have meaning in the filter syntax.
    const safe = q.replace(/[%_,().\\]/g, " ");
    query = query.or(`counterparty_name.ilike.%${safe}%,memo.ilike.%${safe}%`);
  }
  const { data: rows } = await query;
  const txs = rows ?? [];

  const groups = new Map<string, typeof txs>();
  for (const t of txs) {
    const k = dayKey(new Date(t.occurred_at));
    groups.set(k, [...(groups.get(k) ?? []), t]);
  }

  return (
    <main className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">{sp.view === "review" ? "Needs review" : "Transactions"}</h1>
        <Link href={sp.view === "review" ? "/transactions" : "/transactions?view=review"} className="rounded-full border border-white/40 bg-white/20 px-3 py-1 text-sm font-medium text-white backdrop-blur-md">
          {sp.view === "review" ? "Show all" : "Needs review"}
        </Link>
      </div>

      <form className="card grid grid-cols-2 gap-2 sm:grid-cols-4">
        {sp.view && <input type="hidden" name="view" value={sp.view} />}
        <input name="q" defaultValue={q} placeholder="Search name or note" className="input col-span-2" />
        <select name="kind" defaultValue={sp.kind ?? ""} className="input">
          <option value="">All types</option>
          <option value="expense">Spending</option>
          <option value="income">Income</option>
          <option value="own_transfer">Own transfers</option>
        </select>
        <select name="category" defaultValue={sp.category ?? ""} className="input">
          <option value="">All categories</option>
          {CATEGORIES.map((c) => (
            <option key={c.slug} value={c.slug}>
              {c.emoji} {c.en}
            </option>
          ))}
        </select>
        <button className="btn-secondary col-span-2 sm:col-span-4">Filter</button>
      </form>

      {txs.length === 0 && (
        <p className="card text-sm text-stone-500">
          {sp.view === "review" ? "Nothing to review. 🎉" : "No transactions yet."}{" "}
          <Link href="/upload" className="text-brand underline">Add receipts</Link>
        </p>
      )}

      {[...groups.entries()].map(([day, items]) => {
        const p = vientianeParts(new Date(items[0].occurred_at));
        const label = new Date(Date.UTC(p.year, p.month - 1, p.day)).toLocaleDateString("en-GB", {
          weekday: "short",
          day: "numeric",
          month: "short",
          year: "numeric",
          timeZone: "UTC",
        });
        const spent = items.filter((t) => t.kind === "expense").reduce((s, t) => s + Number(t.amount_lak ?? 0), 0);
        return (
          <section key={day}>
            <div className="mb-1 flex justify-between px-2 text-xs font-semibold uppercase tracking-wide text-ink/55">
              <span>{label}</span>
              {spent > 0 && <span>{formatKip(spent)}</span>}
            </div>
            <ul className="card divide-y divide-white/70 overflow-hidden p-0">
              {items.map((t) => {
                const cat = categoryBySlug(t.category);
                const p2 = vientianeParts(new Date(t.occurred_at));
                const time = `${String(p2.hour).padStart(2, "0")}:${String(p2.minute).padStart(2, "0")}`;
                const sign = t.kind === "income" ? "+" : t.kind === "expense" ? "−" : "";
                const color = t.kind === "income" ? "text-emerald-700" : t.kind === "own_transfer" ? "text-stone-400" : "text-stone-900";
                return (
                  <li key={t.id} className="flex items-center gap-3 px-4 py-3">
                    <span className="text-xl" aria-hidden>
                      {t.kind === "own_transfer" ? "🔁" : cat.emoji}
                    </span>
                    <Link href={`/transactions/${t.id}`} className="min-w-0 flex-1">
                      <div className="truncate font-medium">{t.counterparty_name || (t.kind === "income" ? "Income" : cat.en)}</div>
                      <div className="truncate text-xs text-stone-500">
                        {time} · {t.kind === "own_transfer" ? "Own transfer (not spending)" : cat.en}
                        {t.source === "manual" ? " · manual" : ""}
                        {t.memo ? ` · ${t.memo}` : ""}
                      </div>
                      {t.status === "needs_review" && (
                        <div className="mt-1 text-xs text-amber-800">⚠ {t.review_reasons?.[0] ?? "Needs review"}</div>
                      )}
                    </Link>
                    <div className="text-right">
                      <div className={`font-semibold tabular-nums ${color}`}>
                        {sign}
                        {formatMoney(Number(t.amount), t.currency)}
                      </div>
                      {t.currency !== "LAK" && t.amount_lak !== null && <div className="text-xs text-stone-500">{formatKip(Number(t.amount_lak))}</div>}
                      {t.status === "needs_review" && (
                        <form action={confirmTransaction.bind(null, t.id)}>
                          <button className="glass-red mt-1 rounded-full px-3 py-1 text-xs font-semibold">Confirm</button>
                        </form>
                      )}
                    </div>
                  </li>
                );
              })}
            </ul>
          </section>
        );
      })}
    </main>
  );
}
