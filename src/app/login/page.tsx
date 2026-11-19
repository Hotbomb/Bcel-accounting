import { signInWithGoogle } from "./actions";

export default async function LoginPage({ searchParams }: { searchParams: Promise<{ error?: string }> }) {
  const { error } = await searchParams;
  return (
    <main className="mx-auto flex min-h-dvh max-w-sm flex-col px-6 pb-10 pt-[max(4rem,env(safe-area-inset-top))]">
      <div className="hero-glow" aria-hidden />
      <div className="mb-10 text-center text-white">
        <div className="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-[28px] border border-white/50 bg-white/20 text-5xl font-bold shadow-[0_10px_30px_-10px_rgb(80_0_10/0.5),inset_0_1px_0_rgb(255_255_255/0.7)] backdrop-blur-xl">
          ₭
        </div>
        <h1 className="text-3xl font-bold tracking-tight">Kip Tracker</h1>
        <p className="mt-2 text-white/90">Your spending, read from BCEL One receipts.</p>
      </div>

      <div className="card space-y-4 p-6">
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border-2 border-tick text-tick" aria-hidden>
            <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth={3} strokeLinecap="round" strokeLinejoin="round">
              <path d="M5 12l5 5 9-10" />
            </svg>
          </span>
          <p className="text-sm text-ink/75">Private and invite only. Receipt photos are deleted right after they&apos;re read.</p>
        </div>
        <form action={signInWithGoogle}>
          <button className="btn-primary w-full py-4 text-base">Sign in with Google</button>
        </form>
        {error && (
          <p className="text-center text-sm text-brand" role="alert">
            Sign-in didn&apos;t finish. Please try again.
          </p>
        )}
      </div>
      <p className="mt-6 text-center text-xs text-ink/55">New accounts need approval from the admin.</p>
    </main>
  );
}
