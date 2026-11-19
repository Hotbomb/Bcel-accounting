import Link from "next/link";
import { requireUser } from "@/lib/auth";
import { signOut } from "./actions";
import { Nav } from "./nav";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const { profile } = await requireUser();
  return (
    <div className="mx-auto max-w-2xl px-4 pb-28 pt-4 md:pb-10">
      <header className="mb-4 flex items-center justify-between gap-2">
        <Link href="/" className="flex items-center gap-2 font-bold">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand text-white">₭</span>
          Kip Tracker
        </Link>
        <div className="hidden md:block">
          <Nav />
        </div>
        <form action={signOut}>
          <button className="text-sm text-stone-500 hover:text-stone-800" title={profile.email}>
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
