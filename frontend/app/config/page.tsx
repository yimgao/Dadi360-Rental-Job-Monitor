"use client";

import { useEffect, useState } from "react";
import { supabaseOrNull } from "@/lib/supabase";
import { Settings, Save, CheckCircle2 } from "lucide-react";

interface ConfigRow {
  id: number;
  key: string;
  value: string;
}

const FIELDS = [
  { key: "rental_keywords", label: "Rental Keywords", hint: "Comma-separated Chinese terms" },
  { key: "nail_keywords", label: "Nail Job Keywords", hint: "Comma-separated Chinese terms" },
  { key: "restaurant_keywords", label: "Restaurant Keywords", hint: "Comma-separated Chinese terms" },
  { key: "receiver_email", label: "Notification Email", hint: "Gmail address for alerts" },
  { key: "scrape_interval_min", label: "Scrape Interval (min)", hint: "How often the cron job runs" },
];

export default function ConfigPage() {
  const [rows, setRows] = useState<ConfigRow[]>([]);
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    const db = supabaseOrNull();
    if (!db) return;
    db
      .from("config")
      .select("*")
      .then(({ data }) => setRows(data ?? []));
  }, []);

  const getVal = (key: string) => rows.find((r) => r.key === key)?.value ?? "";

  const setVal = (key: string, value: string) => {
    setRows((prev) => {
      const existing = prev.find((r) => r.key === key);
      if (existing) {
        return prev.map((r) => (r.key === key ? { ...r, value } : r));
      }
      return [...prev, { id: 0, key, value }];
    });
    setDirty(true);
    setMsg("");
  };

  const save = async () => {
    const db = supabaseOrNull();
    if (!db) return;
    setSaving(true);
    setMsg("");
    for (const row of rows) {
      if (row.id) {
        await db.from("config").update({ value: row.value }).eq("id", row.id);
      } else {
        await db.from("config").insert({ key: row.key, value: row.value });
      }
    }
    setDirty(false);
    setSaving(false);
    setMsg("Saved");
    setTimeout(() => setMsg(""), 3000);
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center">
              <Settings size={16} className="text-white" />
            </div>
            Config
          </h1>
          <p className="text-sm text-surface-500 mt-1 ml-11">Scraper settings and keywords</p>
        </div>
        <button
          onClick={save}
          disabled={!dirty || saving}
          className={`flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-xl transition-all duration-150 ${
            dirty
              ? "bg-brand-500 hover:bg-brand-400 text-white shadow-lg shadow-brand-500/20"
              : "bg-surface-800 text-surface-500 cursor-not-allowed"
          }`}
        >
          <Save size={14} />
          {saving ? "Saving..." : "Save"}
        </button>
      </div>

      {msg && (
        <div className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-brand-500/10 border border-brand-500/20 text-brand-400 text-sm">
          <CheckCircle2 size={14} />
          {msg}
        </div>
      )}

      <div className="grid gap-4">
        {FIELDS.map((f) => (
          <div
            key={f.key}
            className="rounded-2xl border border-surface-800 bg-surface-900/50 p-5 hover:border-surface-700 transition-colors"
          >
            <label className="block text-sm font-semibold text-surface-300 mb-1.5">{f.label}</label>
            <input
              type="text"
              value={getVal(f.key)}
              onChange={(e) => setVal(f.key, e.target.value)}
              placeholder={f.hint}
              className="w-full px-3.5 py-2 rounded-xl border border-surface-700 bg-surface-950 text-surface-200 text-sm placeholder:text-surface-600 focus:outline-none focus:border-brand-600/50 focus:ring-1 focus:ring-brand-500/20 transition-all"
            />
            <p className="text-xs text-surface-600 mt-1.5">{f.hint}</p>
          </div>
        ))}
      </div>

      <details className="rounded-2xl border border-surface-800 group">
        <summary className="px-5 py-3 text-sm text-surface-500 cursor-pointer hover:text-surface-300 font-medium transition-colors">
          Raw config table
        </summary>
        <pre className="px-5 pb-4 text-xs text-surface-500 overflow-auto max-h-64">
          {JSON.stringify(rows, null, 2)}
        </pre>
      </details>
    </div>
  );
}
