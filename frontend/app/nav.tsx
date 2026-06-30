"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Dashboard" },
  { href: "/listings", label: "Listings" },
  { href: "/config", label: "Config" },
  { href: "/logs", label: "Logs" },
];

export function Nav() {
  const path = usePathname();

  return (
    <header className="border-b border-zinc-800">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center gap-6">
        <span className="font-semibold text-lg tracking-tight text-emerald-400">
          dadi360
        </span>
        <nav className="flex gap-1 text-sm">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={`px-3 py-1.5 rounded-md transition-colors ${
                path === l.href
                  ? "bg-zinc-800 text-zinc-100"
                  : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              {l.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
