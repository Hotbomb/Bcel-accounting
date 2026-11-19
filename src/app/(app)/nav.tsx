"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const ITEMS = [
  { href: "/", label: "Home", icon: "M3 11l9-7 9 7v9a1 1 0 01-1 1h-5v-6h-6v6H4a1 1 0 01-1-1z" },
  { href: "/upload", label: "Add receipts", icon: "M12 16V4m0 0l-4 4m4-4l4 4M4 16v3a1 1 0 001 1h14a1 1 0 001-1v-3" },
  { href: "/transactions", label: "Transactions", icon: "M4 6h16M4 12h16M4 18h10" },
  { href: "/transactions/new", label: "Manual entry", icon: "M12 5v14M5 12h14" },
];

export function Nav() {
  const path = usePathname();
  const active = (href: string) =>
    href === "/" ? path === "/" : href === "/transactions" ? path === "/transactions" || /^\/transactions\/(?!new)/.test(path) : path.startsWith(href);
  return (
    <nav className="fixed inset-x-0 bottom-0 z-20 border-t border-stone-200 bg-white/95 pb-[env(safe-area-inset-bottom)] backdrop-blur md:static md:border-0 md:bg-transparent md:pb-0">
      <ul className="mx-auto grid max-w-2xl grid-cols-4 md:flex md:gap-2">
        {ITEMS.map((it) => (
          <li key={it.href}>
            <Link
              href={it.href}
              className={`flex flex-col items-center gap-1 px-2 py-2 text-[11px] font-medium md:flex-row md:rounded-lg md:px-3 md:text-sm ${
                active(it.href) ? "text-brand md:bg-brand-soft" : "text-stone-500 hover:text-stone-800"
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
