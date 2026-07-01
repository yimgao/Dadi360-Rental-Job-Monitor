"use client";

import { useEffect, useMemo, useState } from "react";
import { supabaseOrNull } from "@/lib/supabase";
import { ListOrdered, Search, ExternalLink, ArrowUpDown, ArrowUp, ArrowDown,
  ChevronLeft, ChevronRight, Download, Filter, X, DollarSign } from "lucide-react";
import { extractPrice } from "@/lib/price";

const CATEGORIES = ["rental", "nail_jobs", "restaurant_jobs"] as const;
const CAT_LABELS: Record<string, string> = {
  rental: "租房", nail_jobs: "美甲", restaurant_jobs: "餐馆",
};
const CAT_COLORS: Record<string, string> = {
  rental: "bg-cyan-500/10 text-cyan-400 ring-1 ring-cyan-500/20",
  nail_jobs: "bg-pink-500/10 text-pink-400 ring-1 ring-pink-500/20",
  restaurant_jobs: "bg-amber-500/10 text-amber-400 ring-1 ring-amber-500/20",
};

const SOURCE_CONFIG: Record<string, { label: string; color: string }> = {
  dadi360: { label: "dadi360", color: "bg-emerald-500/10 text-emerald-400 ring-1 ring-emerald-500/20" },
  "168worker": { label: "168worker", color: "bg-violet-500/10 text-violet-400 ring-1 ring-violet-500/20" },
  us168168: { label: "us168", color: "bg-orange-500/10 text-orange-400 ring-1 ring-orange-500/20" },
  moonbbs: { label: "moonbbs", color: "bg-rose-500/10 text-rose-400 ring-1 ring-rose-500/20" },
};

type SortField = "title" | "category" | "author" | "date" | "found_at";
interface Sort { field: SortField; asc: boolean }
const PAGE_SIZE = 25;

function SortIcon({ field, sort }: { field: SortField; sort: Sort }) {
  if (sort.field !== field) return <ArrowUpDown size={12} className="opacity-30" />;
  return sort.asc ? <ArrowUp size={12} /> : <ArrowDown size={12} />;
}

function PageBtn({ n, cur, onClick }: { n: number; cur: number; onClick: (n: number) => void }) {
  return (
    <button onClick={() => onClick(n)}
      className={`w-8 h-8 text-xs font-medium rounded-lg transition-all ${
        n === cur ? "bg-brand-500/10 text-brand-400 ring-1 ring-brand-500/20"
          : "text-surface-500 hover:text-surface-300 hover:bg-surface-800/50"
      }`}>
      {n + 1}
    </button>
  );
}

export default function ListingsPage() {
  const [listings, setListings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState("");
  const [source, setSource] = useState("");
  const [search, setSearch] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [sort, setSort] = useState<Sort>({ field: "found_at", asc: false });
  const [page, setPage] = useState(0);
  const [total, setTotal] = useState(0);
  const [showFilters, setShowFilters] = useState(false);

  const totalPages = Math.ceil(total / PAGE_SIZE);
  const hasAdvanced = source || dateFrom || dateTo;

  useEffect(() => { setPage(0); }, [category, source, dateFrom, dateTo]);

  useEffect(() => {
    const db = supabaseOrNull();
    if (!db) return;
    const load = async () => {
      setLoading(true);
      let countQ = db.from("listings").select("*", { count: "exact", head: true });
      let dataQ = db.from("listings").select("*").order("found_at", { ascending: false });
      if (category) { countQ = countQ.eq("category", category); dataQ = dataQ.eq("category", category); }
      if (source) { countQ = countQ.eq("source", source); dataQ = dataQ.eq("source", source); }
      if (dateFrom) { countQ = countQ.gte("date", dateFrom); dataQ = dataQ.gte("date", dateFrom); }
      if (dateTo) { countQ = countQ.lte("date", dateTo); dataQ = dataQ.lte("date", dateTo); }
      const { count } = await countQ;
      setTotal(count ?? 0);
      const from = page * PAGE_SIZE;
      const { data } = await dataQ.range(from, from + PAGE_SIZE - 1);
      setListings(data ?? []);
      setLoading(false);
    };
    load();
  }, [category, source, dateFrom, dateTo, page]);

  const toggleSort = (field: SortField) => setSort((s) => s.field === field ? { field, asc: !s.asc } : { field, asc: false });

  const filtered = useMemo(() => {
    let items = listings;
    if (search) {
      const q = search.toLowerCase();
      items = items.filter((l) => l.title?.toLowerCase().includes(q) || l.author?.toLowerCase().includes(q));
    }
    return [...items].sort((a, b) => {
      let va = a[sort.field] ?? "", vb = b[sort.field] ?? "";
      if (sort.field === "found_at") return sort.asc ? new Date(va).getTime() - new Date(vb).getTime() : new Date(vb).getTime() - new Date(va).getTime();
      va = String(va).toLowerCase(); vb = String(vb).toLowerCase();
      return sort.asc ? va.localeCompare(vb) : vb.localeCompare(va);
    });
  }, [listings, search, sort]);

  const exportCSV = () => {
    const rows = [["标题", "分类", "来源", "作者/地区", "日期", "链接"]];
    filtered.forEach((l) => rows.push([l.title, CAT_LABELS[l.category]||l.category, l.source||"dadi360", l.author||"", l.date, l.link]));
    const csv = rows.map((r) => r.map((c) => `"${c.replace(/"/g, '""')}"`).join(",")).join("\n");
    const blob = new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8" });
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "jobpulse_export.csv"; a.click();
  };

  const exportJSON = () => {
    const blob = new Blob([JSON.stringify(filtered, null, 2)], { type: "application/json" });
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "jobpulse_export.json"; a.click();
  };

  const thClass = "text-left px-5 py-3 font-semibold text-surface-400 text-xs uppercase tracking-wider cursor-pointer select-none hover:text-surface-200 transition-colors";

  const pages: number[] = [];
  if (totalPages <= 7) { for (let i = 0; i < totalPages; i++) pages.push(i); }
  else {
    let start = Math.max(0, page - 3), end = Math.min(totalPages - 1, start + 6);
    if (end - start < 6) start = Math.max(0, end - 6);
    for (let i = start; i <= end; i++) pages.push(i);
  }

  return (
    <div className="space-y-4 animate-in fade-in duration-500">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center shrink-0">
              <ListOrdered size={16} className="text-white" />
            </div>
            数据列表
          </h1>
          <p className="text-xs sm:text-sm text-surface-500 mt-1 ml-11">
            共 {total} 条 — 第 {page + 1}/{totalPages || 1} 页
          </p>
        </div>
        <div className="flex gap-2 ml-11 sm:ml-0">
          <button onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors ${
              showFilters || hasAdvanced
                ? "border-brand-500/50 bg-brand-500/10 text-brand-400"
                : "border-surface-800 text-surface-400 hover:border-surface-600"
            }`}>
            <Filter size={12} /> 筛选 {hasAdvanced ? "✓" : ""}
          </button>
          <div className="relative group">
            <button className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-lg border border-surface-800 text-surface-400 hover:border-surface-600 transition-colors">
              <Download size={12} /> 导出
            </button>
            <div className="absolute right-0 top-full mt-1 hidden group-hover:block z-10">
              <div className="bg-surface-900 border border-surface-700 rounded-xl p-1 shadow-xl space-y-0.5 min-w-28">
                <button onClick={exportCSV} className="block w-full text-left px-3 py-1.5 text-xs text-surface-300 hover:bg-surface-800 rounded-lg">CSV</button>
                <button onClick={exportJSON} className="block w-full text-left px-3 py-1.5 text-xs text-surface-300 hover:bg-surface-800 rounded-lg">JSON</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Basic filters */}
      <div className="flex gap-2 flex-wrap items-center">
        {[{ key: "", label: "全部" }, ...CATEGORIES.map((c) => ({ key: c, label: CAT_LABELS[c] }))].map((f) => (
          <button key={f.key} onClick={() => setCategory(f.key)}
            className={`px-3 py-1.5 text-xs sm:text-sm font-medium rounded-lg transition-all duration-150 ${
              category === f.key
                ? "bg-brand-500/10 text-brand-400 ring-1 ring-brand-500/20"
                : "text-surface-400 hover:text-surface-200 hover:bg-surface-800/50 ring-1 ring-surface-800"
            }`}>
            {f.label}
          </button>
        ))}
        <div className="relative ml-auto w-full sm:w-auto mt-2 sm:mt-0">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-surface-500" />
          <input type="text" placeholder="搜索标题或作者..." value={search} onChange={(e) => setSearch(e.target.value)}
            className="w-full sm:w-48 pl-9 pr-3 py-1.5 text-sm rounded-lg border border-surface-800 bg-surface-900 text-surface-300 placeholder-surface-600 focus:outline-none focus:border-brand-600/50 focus:ring-1 focus:ring-brand-500/20 transition-all" />
        </div>
      </div>

      {/* Advanced filters */}
      {showFilters && (
        <div className="rounded-2xl border border-surface-800 bg-surface-900/50 p-4 flex flex-wrap gap-4 items-end">
          <div>
            <label className="block text-xs text-surface-500 mb-1">来源</label>
            <select value={source} onChange={(e) => setSource(e.target.value)}
              className="px-3 py-1.5 text-sm rounded-lg border border-surface-700 bg-surface-950 text-surface-300 focus:outline-none focus:border-brand-600/50">
              <option value="">全部</option>
              <option value="dadi360">dadi360</option>
              <option value="168worker">168worker</option>
              <option value="us168168">us168168</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-surface-500 mb-1">起始日期</label>
            <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)}
              className="px-3 py-1.5 text-sm rounded-lg border border-surface-700 bg-surface-950 text-surface-300 focus:outline-none focus:border-brand-600/50" />
          </div>
          <div>
            <label className="block text-xs text-surface-500 mb-1">截止日期</label>
            <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)}
              className="px-3 py-1.5 text-sm rounded-lg border border-surface-700 bg-surface-950 text-surface-300 focus:outline-none focus:border-brand-600/50" />
          </div>
          {hasAdvanced && (
            <button onClick={() => { setSource(""); setDateFrom(""); setDateTo(""); }}
              className="flex items-center gap-1 px-3 py-1.5 text-xs text-surface-400 hover:text-surface-200">
              <X size={12} /> 清除
            </button>
          )}
        </div>
      )}

      {/* Table (desktop) */}
      <div className="hidden sm:block rounded-2xl border border-surface-800 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-surface-800 bg-surface-900/50">
              <th className={thClass} onClick={() => toggleSort("title")}><span className="flex items-center gap-1.5">标题 <SortIcon field="title" sort={sort} /></span></th>
              <th className={thClass + " w-28"} onClick={() => toggleSort("category")}><span className="flex items-center gap-1.5">分类 <SortIcon field="category" sort={sort} /></span></th>
              <th className="text-left px-5 py-3 font-semibold text-surface-400 text-xs uppercase tracking-wider w-22">来源</th>
              <th className={thClass + " w-24"} onClick={() => toggleSort("author")}><span className="flex items-center gap-1.5">作者/地区 <SortIcon field="author" sort={sort} /></span></th>
              <th className="text-left px-5 py-3 font-semibold text-surface-400 text-xs uppercase tracking-wider w-16"><DollarSign size={12} className="inline" /> 价格</th>
              <th className={thClass + " w-28"} onClick={() => toggleSort("date")}><span className="flex items-center gap-1.5">日期 <SortIcon field="date" sort={sort} /></span></th>
              <th className="text-left px-5 py-3 font-semibold text-surface-400 text-xs uppercase tracking-wider w-16">链接</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-800/50">
            {loading && Array.from({ length: 3 }).map((_, i) => (
              <tr key={i}><td colSpan={7} className="px-5 py-4"><div className="h-4 bg-surface-800 rounded animate-pulse w-3/4" /></td></tr>
            ))}
            {!loading && filtered.length === 0 && (
              <tr><td colSpan={7} className="px-5 py-12 text-center text-surface-500">暂无数据。</td></tr>
            )}
            {filtered.map((l) => (
              <tr key={l.id} className="hover:bg-surface-800/20 transition-colors duration-150">
                <td className="px-5 py-3.5"><p className="text-surface-200 truncate max-w-md font-medium">{l.title}</p></td>
                <td className="px-5 py-3.5">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium ${CAT_COLORS[l.category] || "bg-surface-800 text-surface-400"}`}>{CAT_LABELS[l.category] || l.category}</span>
                </td>
                <td className="px-5 py-3.5">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium ${SOURCE_CONFIG[l.source]?.color || "bg-surface-800 text-surface-400"}`}>{SOURCE_CONFIG[l.source]?.label || l.source || "dadi360"}</span>
                </td>
                <td className="px-5 py-3.5 text-surface-400">{l.author || "—"}</td>
                <td className="px-5 py-3.5">
                  {(() => {
                    const p = extractPrice(l.title, l.salary);
                    return p.label ? <span className="text-xs font-mono text-brand-400">{p.label}</span> : <span className="text-xs text-surface-600">—</span>;
                  })()}
                </td>
                <td className="px-5 py-3.5 text-surface-500 font-mono text-xs">{l.date}</td>
                <td className="px-5 py-3.5">
                  <a href={l.link} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-brand-400 hover:text-brand-300 transition-colors text-xs font-medium">打开 <ExternalLink size={11} /></a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Card list (mobile) */}
      <div className="sm:hidden space-y-3">
        {loading && Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="rounded-2xl border border-surface-800 p-4 space-y-2"><div className="h-4 bg-surface-800 rounded animate-pulse w-full" /><div className="h-3 bg-surface-800 rounded animate-pulse w-2/3" /></div>
        ))}
        {!loading && filtered.length === 0 && (
          <p className="text-sm text-surface-500 py-12 text-center">暂无数据。</p>
        )}
        {filtered.map((l) => (
          <a key={l.id} href={l.link} target="_blank" rel="noopener noreferrer"
            className="block rounded-2xl border border-surface-800 bg-surface-900/50 p-4 hover:bg-surface-800/30 transition-colors space-y-1.5">
            <p className="text-sm font-medium text-surface-200 leading-snug">{l.title}</p>
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium ${CAT_COLORS[l.category] || "bg-surface-800 text-surface-400"}`}>{CAT_LABELS[l.category] || l.category}</span>
              <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium ${SOURCE_CONFIG[l.source]?.color || "bg-surface-800 text-surface-400"}`}>{SOURCE_CONFIG[l.source]?.label || l.source || "dadi360"}</span>
              {l.author && <span className="text-surface-500">{l.author}</span>}
              {(() => { const p = extractPrice(l.title); return p.label ? <span className="text-brand-400 font-mono">{p.label}</span> : null; })()}
              <span className="text-surface-600">{l.date}</span>
            </div>
          </a>
        ))}
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-center gap-1.5">
        <button onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0}
          className="w-8 h-8 flex items-center justify-center rounded-lg text-surface-500 hover:text-surface-300 hover:bg-surface-800/50 disabled:opacity-30 disabled:cursor-not-allowed transition-all">
          <ChevronLeft size={16} />
        </button>
        {pages.map((n) => <PageBtn key={n} n={n} cur={page} onClick={setPage} />)}
        <button onClick={() => setPage(Math.min(totalPages - 1, page + 1))} disabled={page >= totalPages - 1}
          className="w-8 h-8 flex items-center justify-center rounded-lg text-surface-500 hover:text-surface-300 hover:bg-surface-800/50 disabled:opacity-30 disabled:cursor-not-allowed transition-all">
          <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
}
