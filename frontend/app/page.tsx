"use client";

import { useEffect, useState } from "react";
import { supabaseOrNull } from "@/lib/supabase";
import { BarChart3, Home, Building2, UtensilsCrossed, List, Activity, Unplug } from "lucide-react";

interface Stat {
  label: string;
  key: string;
  icon: React.ReactNode;
  color: string;
}

const stats: Stat[] = [
  { label: "Rental", key: "rental", icon: <Home size={18} />, color: "text-cyan-400" },
  { label: "Nail Jobs", key: "nail_jobs", icon: <Building2 size={18} />, color: "text-pink-400" },
  { label: "Restaurant", key: "restaurant_jobs", icon: <UtensilsCrossed size={18} />, color: "text-amber-400" },
];

export default function Dashboard() {
  const [counts, setCounts] = useState<Record<string, number>>({});
  const [recent, setRecent] = useState<any[]>([]);
  const [lastRun, setLastRun] = useState<Record<string, string>>({});

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

      const { data: list } = await db
        .from("listings")
        .select("*")
        .order("found_at", { ascending: false })
        .limit(5);
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
    };
    load();
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold flex items-center gap-2">
          <BarChart3 size={20} className="text-emerald-400" />
          Dashboard
        </h1>
        <p className="text-sm text-zinc-500 mt-1">Monitor overview for c.dadi360.com</p>
      </div>

      {/* stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {stats.map((s) => (
          <div key={s.key} className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5 space-y-2">
            <div className={`flex items-center gap-2 ${s.color}`}>
              {s.icon}
              <span className="text-sm font-medium">{s.label}</span>
            </div>
            <p className="text-3xl font-bold">{counts[s.key] ?? "—"}</p>
            <p className="text-xs text-zinc-600">
              {lastRun[s.key] ? `Last run: ${lastRun[s.key]}` : "No runs yet"}
            </p>
          </div>
        ))}
      </div>

      {/* recent listings */}
      <section>
        <h2 className="text-sm font-semibold text-zinc-400 mb-3 flex items-center gap-2">
          <List size={16} /> Recent Listings
        </h2>
        <div className="rounded-xl border border-zinc-800 divide-y divide-zinc-800">
          {recent.length === 0 && (
            <p className="text-sm text-zinc-600 p-4">No listings yet.</p>
          )}
          {recent.map((r) => (
            <a
              key={r.id}
              href={r.link}
              target="_blank"
              rel="noopener noreferrer"
              className="block px-4 py-3 hover:bg-zinc-800/50 transition-colors"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <p className="text-sm font-medium truncate">{r.title}</p>
                  <p className="text-xs text-zinc-500 mt-0.5">
                    {r.category} · {r.author} · {r.date}
                  </p>
                </div>
                <span className="text-xs text-zinc-600 shrink-0">
                  {new Date(r.found_at).toLocaleDateString("zh-CN")}
                </span>
              </div>
            </a>
          ))}
        </div>
      </section>

      {/* activity pulse */}
      <section>
        <h2 className="text-sm font-semibold text-zinc-400 mb-3 flex items-center gap-2">
          <Activity size={16} /> Recent Runs
        </h2>
        <RecentRuns />
      </section>
    </div>
  );
}

function RecentRuns() {
  const [runs, setRuns] = useState<any[]>([]);

  useEffect(() => {
    const db = supabaseOrNull();
    if (!db) return;
    db
      .from("runs")
      .select("*")
      .order("started_at", { ascending: false })
      .limit(10)
      .then(({ data }) => setRuns(data ?? []));
  }, []);

  return (
    <div className="rounded-xl border border-zinc-800 divide-y divide-zinc-800">
      {runs.length === 0 && (
        <p className="text-sm text-zinc-600 p-4">No runs yet.</p>
      )}
      {runs.map((r) => (
        <div key={r.id} className="px-4 py-2.5 flex items-center gap-3 text-sm">
          <span
            className={`w-2 h-2 rounded-full ${
              r.success ? "bg-emerald-500" : "bg-red-500"
            }`}
          />
          <span className="font-mono text-zinc-300 w-24">{r.category}</span>
          <span className="text-zinc-400">
            {r.new_count} new · {r.duration_s}s
          </span>
          <span className="text-zinc-600 ml-auto">
            {new Date(r.started_at).toLocaleString("zh-CN")}
          </span>
        </div>
      ))}
    </div>
  );
}
