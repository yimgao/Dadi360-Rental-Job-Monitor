"use client";

import { useEffect, useState } from "react";
import { supabaseOrNull } from "@/lib/supabase";
import { Settings, Save } from "lucide-react";

interface ConfigRow {
  id: number;
  key: string;
  value: string;
}

const FIELDS = [
  { key: "rental_keywords", label: "Rental Keywords", hint: "comma separated" },
  { key: "nail_keywords", label: "Nail Job Keywords", hint: "comma separated" },
  { key: "restaurant_keywords", label: "Restaurant Keywords", hint: "comma separated" },
  { key: "receiver_email", label: "Notification Email", hint: "email address" },
  { key: "scrape_interval_min", label: "Scrape Interval (min)", hint: "number" },
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
    setMsg("Saved ✓");
    setTimeout(() => setMsg(""), 2500);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold flex items-center gap-2">
          <Settings size={20} className="text-emerald-400" />
          Config
        </h1>
        <button
          onClick={save}
          disabled={!dirty || saving}
          className={`flex items-center gap-1.5 px-4 py-1.5 text-sm rounded-lg transition-colors ${
            dirty
              ? "bg-emerald-600 hover:bg-emerald-500 text-white"
              : "bg-zinc-800 text-zinc-500 cursor-not-allowed"
          }`}
        >
          <Save size={14} />
          {saving ? "Saving…" : "Save"}
        </button>
      </div>

      {msg && (
        <div className="px-4 py-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-sm">
          {msg}
        </div>
      )}

      <div className="space-y-4">
        {FIELDS.map((f) => (
          <div key={f.key} className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
            <label className="block text-sm font-medium text-zinc-300 mb-1.5">{f.label}</label>
            <input
              type="text"
              value={getVal(f.key)}
              onChange={(e) => setVal(f.key, e.target.value)}
              placeholder={f.hint}
              className="w-full px-3 py-2 rounded-lg border border-zinc-700 bg-zinc-950 text-zinc-200 text-sm placeholder:text-zinc-600 focus:outline-none focus:border-zinc-500"
            />
            <p className="text-xs text-zinc-600 mt-1">{f.hint}</p>
          </div>
        ))}
      </div>

      <details className="rounded-xl border border-zinc-800">
        <summary className="px-4 py-3 text-sm text-zinc-400 cursor-pointer hover:text-zinc-200 font-medium">
          Raw config table
        </summary>
        <pre className="px-4 pb-4 text-xs text-zinc-500 overflow-auto max-h-64">
          {JSON.stringify(rows, null, 2)}
        </pre>
      </details>
    </div>
  );
}
