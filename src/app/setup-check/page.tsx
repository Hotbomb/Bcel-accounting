import { createClient } from "@supabase/supabase-js";

export const dynamic = "force-dynamic";
export const metadata = { title: "Setup check · Kip Tracker" };

type Status = "ok" | "bad" | "warn";
interface Check {
  name: string;
  status: Status;
  detail: string;
}

/** Checks a setting's format without ever showing its value. */
function checkFormat(name: string, value: string | undefined, test: (v: string) => boolean, hint: string): Check {
  if (!value) return { name, status: "bad", detail: "Missing. Add it in Vercel → Settings → Environment Variables." };
  if (value !== value.trim()) return { name, status: "bad", detail: "Has a space or line break at the start or end. Remove it." };
  if (!test(value)) return { name, status: "bad", detail: hint };
  return { name, status: "ok", detail: "Looks right." };
}

async function runChecks(): Promise<Check[]> {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const pub = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ?? process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  const secret = process.env.SUPABASE_SECRET_KEY ?? process.env.SUPABASE_SERVICE_ROLE_KEY;

  const checks: Check[] = [
    checkFormat("NEXT_PUBLIC_SUPABASE_URL", url, (v) => /^https:\/\/[a-z0-9-]+\.supabase\.co\/?$/.test(v), "Should look exactly like https://abcd1234.supabase.co (nothing after .co)."),
    checkFormat("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY", pub, (v) => v.startsWith("sb_publishable_") || v.startsWith("eyJ"), "Should start with sb_publishable_ (or eyJ for the old 'anon' key)."),
    checkFormat("SUPABASE_SECRET_KEY", secret, (v) => (v.startsWith("sb_secret_") || v.startsWith("eyJ")) && v !== pub, "Should start with sb_secret_ (or eyJ for the old 'service_role' key), and be different from the publishable key."),
    checkFormat("ANTHROPIC_API_KEY", process.env.ANTHROPIC_API_KEY, (v) => v.startsWith("sk-ant-"), "Should start with sk-ant-."),
    checkFormat("GEMINI_API_KEY", process.env.GEMINI_API_KEY, (v) => v.length >= 30 && !/\s/.test(v), "Looks too short or contains spaces."),
    checkFormat("CRON_SECRET", process.env.CRON_SECRET, (v) => v.length >= 16, "Should be at least 16 random characters."),
  ];

  const urlOk = checks[0].status === "ok";
  const pubOk = checks[1].status === "ok";
  const secretOk = checks[2].status === "ok";

  if (urlOk && pubOk) {
    try {
      const res = await fetch(`${url!.replace(/\/$/, "")}/auth/v1/settings`, { headers: { apikey: pub! }, cache: "no-store" });
      if (res.status === 401 || res.status === 403) {
        checks.push({ name: "Supabase connection", status: "bad", detail: "Supabase rejected the publishable key. Copy it again." });
      } else if (!res.ok) {
        checks.push({ name: "Supabase connection", status: "bad", detail: `Supabase answered with error ${res.status}. Is the project paused or the URL wrong?` });
      } else {
        checks.push({ name: "Supabase connection", status: "ok", detail: "Connected." });
        const settings = (await res.json()) as { external?: Record<string, boolean> };
        checks.push(
          settings.external?.google
            ? { name: "Google sign-in in Supabase", status: "ok", detail: "Enabled." }
            : { name: "Google sign-in in Supabase", status: "bad", detail: "Not enabled. Supabase → Authentication → Sign In / Providers → Google → turn on and Save." },
        );
      }
    } catch {
      checks.push({ name: "Supabase connection", status: "bad", detail: "Could not reach Supabase. Check the URL." });
    }
  }

  if (urlOk && secretOk) {
    try {
      const db = createClient(url!, secret!, { auth: { persistSession: false } });
      const { error } = await db.from("app_settings").select("id").eq("id", 1).single();
      if (error) {
        checks.push({
          name: "Database tables",
          status: "bad",
          detail:
            error.code === "PGRST205" || /does not exist|schema cache/i.test(error.message)
              ? "Tables not found. Run the SQL in Supabase → SQL Editor."
              : "Could not read the tables. Check the secret key.",
        });
      } else {
        checks.push({ name: "Database tables", status: "ok", detail: "Found." });
        const { count } = await db.from("profiles").select("id", { count: "exact", head: true });
        checks.push({
          name: "Admin account",
          status: count ? "ok" : "warn",
          detail: count ? "Someone has signed in; the first person is the admin." : "No one has signed in yet. Sign in first so you become the admin.",
        });
      }
    } catch {
      checks.push({ name: "Database tables", status: "bad", detail: "Could not connect with the secret key." });
    }
  }

  return checks;
}

const ICON: Record<Status, string> = { ok: "✅", bad: "❌", warn: "⚠️" };

export default async function SetupCheckPage() {
  const checks = await runChecks();
  const allOk = checks.every((c) => c.status !== "bad");
  return (
    <main className="mx-auto max-w-lg px-4 py-10">
      <div className="card space-y-4 p-6">
        <h1 className="text-xl font-bold">Setup check</h1>
        <p className="text-sm text-ink/70">
          {allOk ? "Everything needed is in place. " : "Fix the items marked ❌, then redeploy (see below). "}
          Values are never shown here.
        </p>
        <ul className="space-y-3">
          {checks.map((c) => (
            <li key={c.name} className="rounded-2xl bg-white/60 p-3">
              <div className="font-medium">
                {ICON[c.status]} <span className="break-all">{c.name}</span>
              </div>
              <div className="mt-1 text-sm text-ink/70">{c.detail}</div>
            </li>
          ))}
        </ul>
        <div className="rounded-2xl bg-white/60 p-3 text-sm text-ink/70">
          <b>After changing a setting in Vercel:</b> open your project → <b>Deployments</b> → tap <b>⋯</b> on the top one → <b>Redeploy</b> →{" "}
          <b>Redeploy</b>. Changes only take effect after a redeploy.
        </div>
        {allOk && (
          <a href="/login" className="btn-primary w-full">
            Go to sign in
          </a>
        )}
      </div>
    </main>
  );
}
