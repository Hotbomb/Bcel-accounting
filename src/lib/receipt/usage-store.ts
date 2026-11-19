import "server-only";
import { createAdminClient } from "../supabase/admin";
import type { UsageRecord, UsageStore } from "./extract";

/** UsageStore backed by Supabase (uses the server-only secret key). */
export function supabaseUsageStore(userId: string): UsageStore {
  const db = createAdminClient();
  return {
    async claudeSpentThisMonth(month) {
      const { data, error } = await db
        .from("api_usage")
        .select("cost_usd")
        .eq("usage_month", month)
        .eq("provider", "anthropic");
      if (error) throw new Error("usage lookup failed");
      return (data ?? []).reduce((sum, r) => sum + Number(r.cost_usd), 0);
    },
    async claudeCapUsd() {
      const { data } = await db.from("app_settings").select("claude_monthly_cap_usd").eq("id", 1).single();
      return Number(data?.claude_monthly_cap_usd ?? 5);
    },
    async claudePausedMonth() {
      const { data } = await db.from("app_settings").select("claude_paused_month").eq("id", 1).single();
      return data?.claude_paused_month ?? null;
    },
    async pauseClaude(month) {
      await db.from("app_settings").update({ claude_paused_month: month, updated_at: new Date().toISOString() }).eq("id", 1);
    },
    async record(u: UsageRecord) {
      await db.from("api_usage").insert({
        user_id: userId,
        provider: u.provider,
        model: u.model,
        input_tokens: u.inputTokens,
        output_tokens: u.outputTokens,
        cost_usd: u.costUsd,
        success: u.success,
        error_kind: u.errorKind,
        usage_month: u.usageMonth,
      });
    },
  };
}

/** How many receipt images this person has had read this month. */
export async function userReceiptCountThisMonth(userId: string, month: string): Promise<number> {
  const db = createAdminClient();
  const { count } = await db
    .from("api_usage")
    .select("id", { count: "exact", head: true })
    .eq("user_id", userId)
    .eq("usage_month", month)
    .eq("success", true);
  return count ?? 0;
}

export async function perUserLimit(profileLimit: number | null): Promise<number> {
  if (profileLimit !== null) return profileLimit;
  const db = createAdminClient();
  const { data } = await db.from("app_settings").select("per_user_monthly_receipt_limit").eq("id", 1).single();
  return Number(data?.per_user_monthly_receipt_limit ?? 500);
}

/** Simple rate limit: at most `max` AI calls by this person in the last minute. */
export async function recentCallCount(userId: string, seconds = 60): Promise<number> {
  const db = createAdminClient();
  const since = new Date(Date.now() - seconds * 1000).toISOString();
  const { count } = await db
    .from("api_usage")
    .select("id", { count: "exact", head: true })
    .eq("user_id", userId)
    .gte("created_at", since);
  return count ?? 0;
}
