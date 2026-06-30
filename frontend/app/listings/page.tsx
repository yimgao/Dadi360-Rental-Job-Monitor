"use client";

import { useEffect, useState } from "react";
import { supabaseOrNull } from "@/lib/supabase";
import { List, Search } from "lucide-react";

const CATEGORIES = ["rental", "nail_jobs", "restaurant_jobs"] as const;
const CAT_LABELS: Record<string, string> = {
  rental: "Rental",
  nail_jobs: "Nail Jobs",
  restaurant_jobs: "Restaurant",
};

export default function ListingsPage() {
  const [listings, setListings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState("");
  const [search, setSearch] = useState("");

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

  const filtered = search
    ? listings.filter(
        (l) =>
          l.title?.includes(search) || l.author?.includes(search)
      )
    : listings;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold flex items-center gap-2">
          <List size={20} className="text-emerald-400" />
          Listings
        </h1>
        <p className="text-sm text-zinc-500">{filtered.length} results</p>
      </div>

      {/* filters */}
      <div className="flex gap-3 flex-wrap">
        <button
          onClick={() => setCategory("")}
          className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${
            !category
              ? "border-emerald-500/50 bg-emerald-500/10 text-emerald-400"
              : "border-zinc-800 text-zinc-400 hover:border-zinc-600"
          }`}
        >
          All
        </button>
        {CATEGORIES.map((c) => (
          <button
            key={c}
            onClick={() => setCategory(c)}
            className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${
              category === c
                ? "border-emerald-500/50 bg-emerald-500/10 text-emerald-400"
                : "border-zinc-800 text-zinc-400 hover:border-zinc-600"
            }`}
          >
            {CAT_LABELS[c]}
          </button>
        ))}

        <div className="relative ml-auto">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-600" />
          <input
            type="text"
            placeholder="Filter title / author…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-8 pr-3 py-1.5 text-sm rounded-lg border border-zinc-800 bg-zinc-900 text-zinc-300 focus:outline-none focus:border-zinc-600 w-56"
          />
        </div>
      </div>

      {/* table */}
      <div className="rounded-xl border border-zinc-800 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-800 bg-zinc-900/50">
              <th className="text-left px-4 py-2.5 font-medium text-zinc-400">Title</th>
              <th className="text-left px-4 py-2.5 font-medium text-zinc-400 w-28">Category</th>
              <th className="text-left px-4 py-2.5 font-medium text-zinc-400 w-28">Author</th>
              <th className="text-left px-4 py-2.5 font-medium text-zinc-400 w-24">Date</th>
              <th className="text-left px-4 py-2.5 font-medium text-zinc-400 w-8"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800">
            {loading && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-zinc-600">
                  Loading…
                </td>
              </tr>
            )}
            {!loading && filtered.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-zinc-600">
                  No results.
                </td>
              </tr>
            )}
            {filtered.map((l) => (
              <tr key={l.id} className="hover:bg-zinc-800/30 transition-colors">
                <td className="px-4 py-3">
                  <p className="truncate max-w-md">{l.title}</p>
                </td>
                <td className="px-4 py-3 text-zinc-400">{CAT_LABELS[l.category] ?? l.category}</td>
                <td className="px-4 py-3 text-zinc-400">{l.author || "—"}</td>
                <td className="px-4 py-3 text-zinc-500 font-mono text-xs">{l.date}</td>
                <td className="px-4 py-3">
                  <a
                    href={l.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-emerald-400 hover:text-emerald-300 text-xs"
                  >
                    Open
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
