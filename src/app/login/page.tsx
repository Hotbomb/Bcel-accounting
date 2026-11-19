"use client";
import { useState } from "react";
import { createClient } from "@/lib/supabase/client";

export default function LoginPage() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function signIn() {
    setBusy(true);
    setError(null);
    const { error } = await createClient().auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: `${window.location.origin}/auth/callback` },
    });
    if (error) {
      setError("Could not start Google sign-in. Please try again.");
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-dvh max-w-sm flex-col justify-center px-6">
      <div className="mb-8 text-center">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-brand text-4xl font-bold text-white">₭</div>
        <h1 className="text-2xl font-bold">Kip Tracker</h1>
        <p className="mt-2 text-stone-600">Your spending, read from BCEL One receipts.</p>
      </div>
      <button onClick={signIn} disabled={busy} className="btn-primary w-full py-4 text-base">
        {busy ? "Opening Google…" : "Sign in with Google"}
      </button>
      {error && <p className="mt-4 text-center text-sm text-red-700">{error}</p>}
      <p className="mt-6 text-center text-xs text-stone-500">Invite only. New accounts need approval from the admin.</p>
    </main>
  );
}
