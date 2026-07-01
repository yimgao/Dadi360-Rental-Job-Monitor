"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { LayoutDashboard, ListOrdered, Info, Menu, X } from "lucide-react";

const mainLinks = [
  { href: "/", label: "仪表盘", icon: LayoutDashboard, color: "text-brand-400" },
  { href: "/listings", label: "数据列表", icon: ListOrdered, color: "text-cyan-400" },
];

export function Nav() {
  const path = usePathname();
  const [open, setOpen] = useState(false);
  const onHidden = path === "/config" || path === "/logs";

  return (
    <header className="sticky top-0 z-50 border-b border-surface-800 bg-surface-950/80 backdrop-blur-xl">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between gap-4">
        <Link href="/" className="flex items-center gap-2.5 group shrink-0">
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
            <span className="hidden sm:inline text-[10px] text-surface-500 ml-1.5 font-mono">JobPulse</span>
          </div>
        </Link>

        {/* Desktop nav */}
        <nav className="hidden sm:flex gap-1 items-center">
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
          <Link
            href="/about"
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-sm font-medium transition-all duration-150 ml-2 ${
              path === "/about"
                ? "text-brand-400 bg-surface-800/80 ring-1 ring-surface-700"
                : "text-surface-500 hover:text-surface-300"
            }`}
          >
            <Info size={14} />
            关于
          </Link>
        </nav>

        {/* Mobile hamburger */}
        <button onClick={() => setOpen(!open)} className="sm:hidden text-surface-400 p-1">
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {/* Mobile menu */}
      {open && (
        <div className="sm:hidden border-t border-surface-800 bg-surface-900 px-4 py-3 space-y-1">
          {[...mainLinks, { href: "/about", label: "关于", icon: Info, color: "text-brand-400" },
            ...(onHidden ? [{ href: path, label: path === "/config" ? "配置" : "日志", icon: ListOrdered, color: "text-amber-400" }] : [])
          ].map((l) => {
            const active = path === l.href;
            const Icon = l.icon;
            return (
              <Link
                key={l.href}
                href={l.href}
                onClick={() => setOpen(false)}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  active ? "bg-surface-800 text-surface-200" : "text-surface-400 hover:text-surface-200"
                }`}
              >
                <Icon size={16} />
                {l.label}
              </Link>
            );
          })}
        </div>
      )}
    </header>
  );
}
