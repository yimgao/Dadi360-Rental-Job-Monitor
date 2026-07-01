"use client";

import { useEffect, useState } from "react";
import { supabaseOrNull } from "@/lib/supabase";
import { ScrollText, AlertCircle, CheckCircle2 } from "lucide-react";

export default function LogsPage() {
  const [runs, setRuns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const db = supabaseOrNull();
    if (!db) return;
    db
      .from("runs")
      .select("*")
      .order("started_at", { ascending: false })
      .limit(50)
      .then(({ data }) => {
        setRuns(data ?? []);
        setLoading(false);
      });
  }, []);

  const successCount = runs.filter((r) => r.success).length;
  const errorCount = runs.filter((r) => !r.success).length;

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center">
              <ScrollText size={16} className="text-white" />
            </div>
            运行日志
          </h1>
          <p className="text-sm text-surface-500 mt-1 ml-11">抓取历史与错误记录</p>
        </div>
        <div className="flex gap-3 text-sm">
          <span className="flex items-center gap-1.5 text-brand-400">
            <CheckCircle2 size={14} />
            {successCount} 次成功
          </span>
          {errorCount > 0 && (
            <span className="flex items-center gap-1.5 text-red-400">
              <AlertCircle size={14} />
              {errorCount} 次失败
            </span>
          )}
        </div>
      </div>

      <div className="rounded-2xl border border-surface-800 divide-y divide-surface-800/50 overflow-hidden">
        {loading &&
          Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="px-5 py-4 flex items-center gap-3">
              <div className="w-2 h-2 rounded-full bg-surface-700 animate-pulse" />
              <div className="h-3 bg-surface-800 rounded animate-pulse w-20" />
              <div className="h-3 bg-surface-800 rounded animate-pulse w-32" />
            </div>
          ))}
        {!loading && runs.length === 0 && (
          <p className="text-sm text-surface-500 p-10 text-center">暂无运行日志。</p>
        )}
        {runs.map((r) => (
          <div key={r.id} className="px-5 py-3.5 flex items-start gap-3 hover:bg-surface-800/20 transition-colors">
            {r.success ? (
              <CheckCircle2 size={16} className="text-brand-500 mt-0.5 shrink-0" />
            ) : (
              <AlertCircle size={16} className="text-red-500 mt-0.5 shrink-0" />
            )}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 text-sm">
                <span className="font-mono text-xs text-surface-200 font-medium">{r.category}</span>
                <span className="text-surface-500 text-xs">
                  {r.new_count} 条 · {r.duration_s}秒
                </span>
                {r.error && (
                  <span className="text-red-400 text-xs truncate max-w-xs">{r.error}</span>
                )}
              </div>
              <p className="text-xs text-surface-600 mt-0.5">
                {new Date(r.started_at).toLocaleString("zh-CN")}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
