import { requireUser } from "@/lib/auth";
import { computeStats, type TxForStats } from "@/lib/stats";
import { addMonths } from "@/lib/time";
import { DashboardView } from "./dashboard-view";

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
  return <DashboardView s={s} />;
}
