import Link from "next/link";
import { requireUser } from "@/lib/auth";
import { signOut } from "./actions";
import { Nav } from "./nav";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const { profile } = await requireUser();
  return (
    <div className="mx-auto max-w-2xl px-4 pb-32 pt-[max(1rem,env(safe-area-inset-top))] md:pb-10">
      <header className="mb-4 flex items-center justify-between gap-2">
        <Link href="/" className="flex items-center gap-2 font-bold text-white">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl border border-white/50 bg-white/20 text-white shadow-[inset_0_1px_0_rgb(255_255_255/0.6)] backdrop-blur-md">₭</span>
          Kip Tracker
        </Link>
        <div className="hidden md:block">
          <Nav />
        </div>
        <form action={signOut}>
          <button className="rounded-full border border-white/40 bg-white/15 px-3 py-1 text-sm text-white backdrop-blur-md hover:bg-white/25" title={profile.email}>
            Sign out
          </button>
        </form>
      </header>
      <div className="md:hidden">
        <Nav />
      </div>
      {children}
    </div>
  );
}
