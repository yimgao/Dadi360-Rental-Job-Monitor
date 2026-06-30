"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, ListOrdered, Settings, ScrollText, LayoutDashboard } from "lucide-react";

const links = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/listings", label: "Listings", icon: ListOrdered },
  { href: "/config", label: "Config", icon: Settings },
  { href: "/logs", label: "Logs", icon: ScrollText },
];

export function Nav() {
  const path = usePathname();

  return (
    <header className="sticky top-0 z-50 border-b border-surface-800 bg-surface-950/80 backdrop-blur-xl">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center gap-8">
        <Link href="/" className="flex items-center gap-2 group">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center">
            <Home size={14} className="text-white" />
          </div>
          <span className="font-bold text-base tracking-tight text-surface-100">
            dadi360
          </span>
        </Link>
        <nav className="flex gap-1">
          {links.map((l) => {
            const active = path === l.href;
            const Icon = l.icon;
            return (
              <Link
                key={l.href}
                href={l.href}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                  active
                    ? "bg-brand-500/10 text-brand-400 ring-1 ring-brand-500/20"
                    : "text-surface-400 hover:text-surface-200 hover:bg-surface-800/50"
                }`}
              >
                <Icon size={14} />
                {l.label}
              </Link>
            );
          })}
        </nav>
        <div className="ml-auto flex items-center gap-2">
          <span className="text-xs text-surface-600 bg-surface-900 px-2 py-1 rounded-md font-mono">
            v0.2
          </span>
        </div>
      </div>
    </header>
  );
}
