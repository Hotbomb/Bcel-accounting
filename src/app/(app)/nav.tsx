"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const ITEMS = [
  { href: "/", label: "Home", icon: "M3 11l9-7 9 7v9a1 1 0 01-1 1h-5v-6h-6v6H4a1 1 0 01-1-1z" },
  { href: "/upload", label: "Receipts", icon: "M12 16V4m0 0l-4 4m4-4l4 4M4 16v3a1 1 0 001 1h14a1 1 0 001-1v-3" },
  { href: "/transactions", label: "Transactions", icon: "M4 6h16M4 12h16M4 18h10" },
  { href: "/transactions/new", label: "Manual", icon: "M12 5v14M5 12h14" },
];

/** Floating frosted-glass tab bar (bottom on phones, inline pill on desktop). */
export function Nav() {
  const path = usePathname();
  const active = (href: string) =>
    href === "/"
      ? path === "/"
      : href === "/transactions"
        ? path === "/transactions" || /^\/transactions\/(?!new)/.test(path)
        : path.startsWith(href);
  return (
    <nav className="fixed inset-x-3 bottom-[max(0.75rem,env(safe-area-inset-bottom))] z-20 md:static md:inset-auto">
      <ul className="glass-strong mx-auto grid max-w-md grid-cols-4 gap-1 rounded-[28px] p-1.5 md:flex md:max-w-none md:rounded-full md:p-1">
        {ITEMS.map((it) => (
          <li key={it.href}>
            <Link
              href={it.href}
              aria-current={active(it.href) ? "page" : undefined}
              className={`flex flex-col items-center gap-0.5 rounded-[22px] px-2 py-2 text-[11px] font-medium transition md:flex-row md:gap-1.5 md:rounded-full md:px-3 md:py-1.5 md:text-sm ${
                active(it.href) ? "glass-red" : "text-ink/60 hover:bg-white/60 hover:text-ink"
              }`}
            >
              <svg viewBox="0 0 24 24" className="h-6 w-6 md:h-5 md:w-5" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                <path d={it.icon} />
              </svg>
              {it.label}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
