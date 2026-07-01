"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, ListOrdered, Info } from "lucide-react";

const mainLinks = [
  { href: "/", label: "仪表盘", icon: LayoutDashboard, color: "text-brand-400" },
  { href: "/listings", label: "数据列表", icon: ListOrdered, color: "text-cyan-400" },
];

export function Nav() {
  const path = usePathname();
  const onHidden = path === "/config" || path === "/logs";

  return (
    <header className="sticky top-0 z-50 border-b border-surface-800 bg-surface-950/80 backdrop-blur-xl">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center gap-8">
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center group-hover:scale-105 transition-transform">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M22 21v-2a4 4 0 0 0-3-3.87"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
          </div>
          <div>
            <span className="font-bold text-base tracking-tight text-surface-100">聚职住</span>
            <span className="text-[10px] text-surface-500 ml-1.5 font-mono">JobPulse</span>
          </div>
        </Link>
        <nav className="flex gap-1">
          {mainLinks.map((l) => {
            const active = path === l.href;
            const Icon = l.icon;
            return (
              <Link
                key={l.href}
                href={l.href}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                  active
                    ? `${l.color} bg-surface-800/80 ring-1 ring-surface-700`
                    : "text-surface-500 hover:text-surface-200 hover:bg-surface-800/40"
                }`}
              >
                <Icon size={14} className={active ? l.color : "text-surface-500"} />
                {l.label}
              </Link>
            );
          })}
          {onHidden && (
            <Link
              href={path}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-150 text-amber-400 bg-surface-800/80 ring-1 ring-surface-700"
            >
              {path === "/config" ? "配置" : "日志"}
            </Link>
          )}
        </nav>
        <div className="ml-auto flex items-center gap-2">
          <Link
            href="/about"
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-sm font-medium transition-all duration-150 ${
              path === "/about"
                ? "text-brand-400 bg-surface-800/80 ring-1 ring-surface-700"
                : "text-surface-500 hover:text-surface-300"
            }`}
          >
            <Info size={14} />
            关于
          </Link>
        </div>
      </div>
    </header>
  );
}
