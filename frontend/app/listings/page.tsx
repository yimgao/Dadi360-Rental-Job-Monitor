"use client";

import { useEffect, useMemo, useState } from "react";
import { supabaseOrNull } from "@/lib/supabase";
import { ListOrdered, Search, ExternalLink, ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react";

const CATEGORIES = ["rental", "nail_jobs", "restaurant_jobs"] as const;
const CAT_CONFIG: Record<string, { label: string; color: string }> = {
  rental: { label: "Rental", color: "bg-cyan-500/10 text-cyan-400 ring-1 ring-cyan-500/20" },
  nail_jobs: { label: "Nail Jobs", color: "bg-pink-500/10 text-pink-400 ring-1 ring-pink-500/20" },
  restaurant_jobs: { label: "Restaurant", color: "bg-amber-500/10 text-amber-400 ring-1 ring-amber-500/20" },
};

type SortField = "title" | "category" | "author" | "date" | "found_at";
interface Sort { field: SortField; asc: boolean }

function SortIcon({ field, sort }: { field: SortField; sort: Sort }) {
  if (sort.field !== field) return <ArrowUpDown size={12} className="opacity-30" />;
  return sort.asc ? <ArrowUp size={12} /> : <ArrowDown size={12} />;
}

export default function ListingsPage() {
  const [listings, setListings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState("");
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<Sort>({ field: "found_at", asc: false });

  useEffect(() => {
    const db = supabaseOrNull();
    if (!db) return;
    const load = async () => {
      setLoading(true);
      let q = db.from("listings").select("*").order("found_at", { ascending: false });
      if (category) q = q.eq("category", category);
      const { data } = await q.limit(100);
      setListings(data ?? []);
      setLoading(false);
    };
    load();
  }, [category]);

  const toggleSort = (field: SortField) => {
    setSort((s) => s.field === field ? { field, asc: !s.asc } : { field, asc: false });
  };

  const filtered = useMemo(() => {
    let items = listings;
    if (search) {
      const q = search.toLowerCase();
      items = items.filter((l) => l.title?.toLowerCase().includes(q) || l.author?.toLowerCase().includes(q));
    }
    return [...items].sort((a, b) => {
      let va = a[sort.field] ?? "";
      let vb = b[sort.field] ?? "";
      if (sort.field === "found_at") {
        return sort.asc
          ? new Date(va).getTime() - new Date(vb).getTime()
          : new Date(vb).getTime() - new Date(va).getTime();
      }
      va = String(va).toLowerCase();
      vb = String(vb).toLowerCase();
      return sort.asc ? va.localeCompare(vb) : vb.localeCompare(va);
    });
  }, [listings, search, sort]);

  const thClass = "text-left px-5 py-3 font-semibold text-surface-400 text-xs uppercase tracking-wider cursor-pointer select-none hover:text-surface-200 transition-colors";

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center">
              <ListOrdered size={16} className="text-white" />
            </div>
            Listings
          </h1>
          <p className="text-sm text-surface-500 mt-1 ml-11">
            {filtered.length} result{filtered.length !== 1 ? "s" : ""}
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-2 flex-wrap items-center">
        {[{ key: "", label: "All" }, ...CATEGORIES.map((c) => ({ key: c, label: CAT_CONFIG[c].label }))].map(
          (f) => (
            <button
              key={f.key}
              onClick={() => setCategory(f.key)}
              className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-all duration-150 ${
                category === f.key
                  ? "bg-brand-500/10 text-brand-400 ring-1 ring-brand-500/20"
                  : "text-surface-400 hover:text-surface-200 hover:bg-surface-800/50 ring-1 ring-surface-800"
              }`}
            >
              {f.label}
            </button>
          )
        )}
        <div className="relative ml-auto">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-surface-500" />
          <input
            type="text"
            placeholder="Search title or author..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 pr-3 py-1.5 text-sm rounded-lg border border-surface-800 bg-surface-900 text-surface-300 placeholder-surface-600 focus:outline-none focus:border-brand-600/50 focus:ring-1 focus:ring-brand-500/20 transition-all w-56"
          />
        </div>
      </div>

      {/* Table */}
      <div className="rounded-2xl border border-surface-800 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-surface-800 bg-surface-900/50">
              <th className={thClass} onClick={() => toggleSort("title")}>
                <span className="flex items-center gap-1.5">
                  Title <SortIcon field="title" sort={sort} />
                </span>
              </th>
              <th className={thClass + " w-28"} onClick={() => toggleSort("category")}>
                <span className="flex items-center gap-1.5">
                  Category <SortIcon field="category" sort={sort} />
                </span>
              </th>
              <th className={thClass + " w-24"} onClick={() => toggleSort("author")}>
                <span className="flex items-center gap-1.5">
                  Author <SortIcon field="author" sort={sort} />
                </span>
              </th>
              <th className={thClass + " w-28"} onClick={() => toggleSort("date")}>
                <span className="flex items-center gap-1.5">
                  Date <SortIcon field="date" sort={sort} />
                </span>
              </th>
              <th className={"text-left px-5 py-3 font-semibold text-surface-400 text-xs uppercase tracking-wider w-16"}>
                Link
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-800/50">
            {loading &&
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i}>
                  <td colSpan={5} className="px-5 py-4">
                    <div className="h-4 bg-surface-800 rounded animate-pulse w-3/4" />
                  </td>
                </tr>
              ))}
            {!loading && filtered.length === 0 && (
              <tr>
                <td colSpan={5} className="px-5 py-12 text-center text-surface-500">
                  No results found.
                </td>
              </tr>
            )}
            {filtered.map((l) => (
              <tr key={l.id} className="hover:bg-surface-800/20 transition-colors duration-150">
                <td className="px-5 py-3.5">
                  <p className="text-surface-200 truncate max-w-md font-medium">{l.title}</p>
                </td>
                <td className="px-5 py-3.5">
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium ${
                      CAT_CONFIG[l.category]?.color || "bg-surface-800 text-surface-400"
                    }`}
                  >
                    {CAT_CONFIG[l.category]?.label || l.category}
                  </span>
                </td>
                <td className="px-5 py-3.5 text-surface-400">{l.author || "—"}</td>
                <td className="px-5 py-3.5 text-surface-500 font-mono text-xs">{l.date}</td>
                <td className="px-5 py-3.5">
                  <a
                    href={l.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-brand-400 hover:text-brand-300 transition-colors text-xs font-medium"
                  >
                    Open <ExternalLink size={11} />
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
