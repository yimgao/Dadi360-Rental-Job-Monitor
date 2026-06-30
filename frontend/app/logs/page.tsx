"use client";

import { useEffect, useState } from "react";
import { supabaseOrNull } from "@/lib/supabase";
import { ScrollText, AlertCircle, CheckCircle2 } from "lucide-react";

export default function LogsPage() {
  const [runs, setRuns] = useState<any[]>([]);

  useEffect(() => {
    const db = supabaseOrNull();
    if (!db) return;
    db
      .from("runs")
      .select("*")
      .order("started_at", { ascending: false })
      .limit(50)
      .then(({ data }) => setRuns(data ?? []));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold flex items-center gap-2">
          <ScrollText size={20} className="text-emerald-400" />
          Logs
        </h1>
        <p className="text-sm text-zinc-500 mt-1">Run history and errors</p>
      </div>

      <div className="rounded-xl border border-zinc-800 divide-y divide-zinc-800">
        {runs.length === 0 && (
          <p className="text-sm text-zinc-600 p-6 text-center">No run logs yet.</p>
        )}
        {runs.map((r) => (
          <div key={r.id} className="px-4 py-3 flex items-start gap-3">
            {r.success ? (
              <CheckCircle2 size={16} className="text-emerald-500 mt-0.5 shrink-0" />
            ) : (
              <AlertCircle size={16} className="text-red-500 mt-0.5 shrink-0" />
            )}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 text-sm">
                <span className="font-mono text-zinc-200">{r.category}</span>
                <span className="text-zinc-500">
                  {r.new_count} new · {r.duration_s}s
                </span>
                {r.error && (
                  <span className="text-red-400 text-xs truncate">{r.error}</span>
                )}
              </div>
              <p className="text-xs text-zinc-600 mt-0.5">
                {new Date(r.started_at).toLocaleString("zh-CN")}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
