// Read at runtime (not baked in at build time) so the same build works on any
// host. The NEXT_PUBLIC_ names are still accepted for older setups.
export function supabaseUrl(): string {
  return (process.env.SUPABASE_URL ?? process.env.NEXT_PUBLIC_SUPABASE_URL ?? "").trim().replace(/\/$/, "");
}

export function supabasePublishableKey(): string {
  return (
    process.env.SUPABASE_PUBLISHABLE_KEY ??
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ??
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ??
    ""
  ).trim();
}

export function supabaseSecretKey(): string {
  return (process.env.SUPABASE_SECRET_KEY ?? process.env.SUPABASE_SERVICE_ROLE_KEY ?? "").trim();
}

export function supabaseConfigured(): boolean {
  return Boolean(supabaseUrl() && supabasePublishableKey());
}
