import "server-only";
import { createClient } from "@supabase/supabase-js";
import { supabaseSecretKey, supabaseUrl } from "../env";

/**
 * Bypasses row-level security. Only used for app-wide bookkeeping (AI usage
 * rows, the global cost cap). Never use it to read or write someone's
 * transactions.
 */
export function createAdminClient() {
  const key = supabaseSecretKey();
  if (!key) throw new Error("SUPABASE_SECRET_KEY is not set");
  return createClient(supabaseUrl(), key, { auth: { persistSession: false, autoRefreshToken: false } });
}
