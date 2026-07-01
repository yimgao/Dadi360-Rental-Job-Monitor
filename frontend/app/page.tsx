"use client";

import { useEffect, useState } from "react";
import { supabaseOrNull } from "@/lib/supabase";
import {
  LayoutDashboard,
  Home,
  Building2,
  UtensilsCrossed,
  ArrowUpRight,
  Clock,
  Activity,
  List,
} from "lucide-react";

interface Stat {
  label: string;
  key: string;
  icon: React.ReactNode;
  gradient: string;
}

const stats: Stat[] = [
  {
    label: "Rental",
    key: "rental",
    icon: <Home size={18} />,
    gradient: "from-cyan-500/20 to-cyan-600/5",
  },
  {
    label: "Nail Jobs",
    key: "nail_jobs",
    icon: <Building2 size={18} />,
    gradient: "from-pink-500/20 to-pink-600/5",
  },
  {
    label: "Restaurant",
    key: "restaurant_jobs",
    icon: <UtensilsCrossed size={18} />,
    gradient: "from-amber-500/20 to-amber-600/5",
  },
];

const badgeColors: Record<string, string> = {
  rental: "bg-cyan-500/10 text-cyan-400 ring-1 ring-cyan-500/20",
  nail_jobs: "bg-pink-500/10 text-pink-400 ring-1 ring-pink-500/20",
  restaurant_jobs: "bg-amber-500/10 text-amber-400 ring-1 ring-amber-500/20",
};

export default function Dashboard() {
  const [counts, setCounts] = useState<Record<string, number>>({});
  const [sourceCounts, setSourceCounts] = useState<Record<string, number>>({});
  const [recent, setRecent] = useState<any[]>([]);
  const [lastRun, setLastRun] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const db = supabaseOrNull();
    if (!db) return;

    const load = async () => {
      const cats = ["rental", "nail_jobs", "restaurant_jobs"];
      const c: Record<string, number> = {};
      for (const cat of cats) {
        const { count } = await db
          .from("listings")
          .select("*", { count: "exact", head: true })
          .eq("category", cat);
        c[cat] = count ?? 0;
      }
      setCounts(c);

      // source breakdown per category
      const src: Record<string, number> = {};
      for (const s of ["dadi360", "168worker", "us168168"]) {
        const { count } = await db
          .from("listings")
          .select("*", { count: "exact", head: true })
          .eq("source", s);
        src[s] = count ?? 0;
      }
      setSourceCounts(src);

      const { data: list } = await db
        .from("listings")
        .select("*")
        .order("found_at", { ascending: false })
        .limit(6);
      setRecent(list ?? []);

      const latest: Record<string, string> = {};
      for (const cat of cats) {
        const { data: runs } = await db
          .from("runs")
          .select("started_at")
          .eq("category", cat)
          .order("started_at", { ascending: false })
          .limit(1);
        if (runs?.length) {
          latest[cat] = new Date(runs[0].started_at).toLocaleString("zh-CN");
        }
      }
      setLastRun(latest);
      setLoading(false);
    };
    load();
  }, []);

  const total = Object.values(counts).reduce((a, b) => a + b, 0);

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      {/* Header */}
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center">
              <LayoutDashboard size={16} className="text-white" />
            </div>
            Dashboard
          </h1>
          <p className="text-sm text-surface-500 mt-1 ml-11">
            c.dadi360.com monitoring overview
          </p>
        </div>
        <div className="text-right">
          <p className="text-3xl font-bold text-surface-100">{total}</p>
          <p className="text-xs text-surface-500">total listings tracked</p>
          <div className="flex gap-2 mt-1.5 justify-end text-[11px]">
            <span className="text-emerald-400">● dadi360 {sourceCounts.dadi360 ?? "—"}</span>
            <span className="text-violet-400">● 168worker {sourceCounts["168worker"] ?? "—"}</span>
            <span className="text-orange-400">● us168 {sourceCounts["us168168"] ?? "—"}</span>
          </div>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {stats.map((s) => (
          <div
            key={s.key}
            className={`glow-card rounded-2xl border border-surface-800 bg-gradient-to-br ${s.gradient} p-5 space-y-3 transition-all duration-200`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-surface-400">
                {s.icon}
                <span className="text-sm font-semibold text-surface-300">
                  {s.label}
                </span>
              </div>
              <ArrowUpRight size={14} className="text-surface-600" />
            </div>
            <p className="text-4xl font-bold tracking-tight">
              {loading ? (
                <span className="text-surface-700 animate-pulse">—</span>
              ) : (
                counts[s.key] ?? 0
              )}
            </p>
            <div className="flex items-center gap-1.5 text-xs text-surface-500">
              <Clock size={12} />
              <span>
                {lastRun[s.key]
                  ? lastRun[s.key]
                  : "No runs yet"}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Listings */}
        <section className="rounded-2xl border border-surface-800 bg-surface-900/50 overflow-hidden">
          <div className="px-5 py-3.5 border-b border-surface-800 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-surface-300 flex items-center gap-2">
              <List size={14} className="text-brand-400" />
              Recent Listings
            </h2>
            <a
              href="/listings"
              className="text-xs text-brand-400 hover:text-brand-300 transition-colors"
            >
              View all
            </a>
          </div>
          <div className="divide-y divide-surface-800/50">
            {loading && (
              <p className="text-sm text-surface-600 p-5 text-center animate-pulse">
                Loading...
              </p>
            )}
            {!loading && recent.length === 0 && (
              <p className="text-sm text-surface-600 p-10 text-center">
                No listings yet — waiting for the first scrape.
              </p>
            )}
            {recent.map((r, i) => (
              <a
                key={r.id}
                href={r.link}
                target="_blank"
                rel="noopener noreferrer"
                className="block px-5 py-3 hover:bg-surface-800/30 transition-all duration-150 group"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-surface-200 truncate group-hover:text-brand-300 transition-colors">
                      {r.title}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium ${
                          badgeColors[r.category] || "bg-surface-800 text-surface-400"
                        }`}
                      >
                        {r.category}
                      </span>
                      {r.author && (
                        <span className="text-xs text-surface-500">{r.author}</span>
                      )}
                      <span className="text-xs text-surface-600">{r.date}</span>
                    </div>
                  </div>
                  <span className="text-[11px] text-surface-600 shrink-0 mt-0.5">
                    {new Date(r.found_at).toLocaleDateString("zh-CN")}
                  </span>
                </div>
              </a>
            ))}
          </div>
        </section>

        {/* Recent Runs */}
        <section className="rounded-2xl border border-surface-800 bg-surface-900/50 overflow-hidden">
          <div className="px-5 py-3.5 border-b border-surface-800 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-surface-300 flex items-center gap-2">
              <Activity size={14} className="text-brand-400" />
              Recent Runs
            </h2>
          </div>
          <RecentRuns />
        </section>
      </div>
    </div>
  );
}

function RecentRuns() {
  const [runs, setRuns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const db = supabaseOrNull();
    if (!db) return;
    db
      .from("runs")
      .select("*")
      .order("started_at", { ascending: false })
      .limit(10)
      .then(({ data }) => {
        setRuns(data ?? []);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <p className="text-sm text-surface-600 p-5 text-center animate-pulse">
        Loading...
      </p>
    );
  }

  if (runs.length === 0) {
    return (
      <p className="text-sm text-surface-600 p-10 text-center">
        No runs yet.
      </p>
    );
  }

  return (
    <div className="divide-y divide-surface-800/50">
      {runs.map((r) => (
        <div key={r.id} className="px-5 py-3 flex items-center gap-2 text-sm">
          <div
            className={`w-2 h-2 shrink-0 rounded-full ${
              r.success ? "bg-brand-500 shadow-[0_0_6px_rgba(16,185,129,0.5)]" : "bg-red-500"
            }`}
          />
          <span className="font-mono text-xs text-surface-300 truncate max-w-28">{r.category}</span>
          <span className="text-surface-400 shrink-0">
            {r.new_count} new
          </span>
          <span className="text-surface-600 text-xs shrink-0">{r.duration_s}s</span>
          <span className="text-surface-600 text-xs ml-auto shrink-0">
            {new Date(r.started_at).toLocaleString("zh-CN")}
          </span>
        </div>
      ))}
    </div>
  );
}
