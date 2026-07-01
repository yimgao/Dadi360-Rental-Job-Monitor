"use client";

import { useEffect, useState } from "react";
import { supabaseOrNull } from "@/lib/supabase";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend,
} from "recharts";

const CAT_COLORS: Record<string, string> = {
  rental: "#22d3ee",
  nail_jobs: "#f472b6",
  restaurant_jobs: "#fbbf24",
};
const CAT_LABELS: Record<string, string> = {
  rental: "租房",
  nail_jobs: "美甲",
  restaurant_jobs: "餐馆",
};

export function TrendChart() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const db = supabaseOrNull();
    if (!db) return;

    const load = async () => {
      // Get all listings, group by date + category on client side
      const { data: rows } = await db
        .from("listings")
        .select("date, category")
        .not("date", "is", "null")
        .neq("date", "");

      if (!rows) { setLoading(false); return; }

      // Build date + category matrix
      const dateMap: Record<string, any> = {};
      const cats = ["rental", "nail_jobs", "restaurant_jobs"];

      for (const row of rows) {
        // Parse various date formats into YYYY-MM-DD
        let d = (row.date || "").trim();
        if (!d) continue;
        // "2026-6-29" → pad to "2026-06-29"
        // "6/29/2026" → "2026-06-29"
        // "昨天" / "今天" → skip (can't determine exact date)
        // full ISO → extract date part
        let dateKey = "";
        if (/^\d{4}-\d{1,2}-\d{1,2}$/.test(d)) {
          const parts = d.split("-");
          dateKey = `${parts[0]}-${parts[1].padStart(2,"0")}-${parts[2].padStart(2,"0")}`;
        } else if (/^\d{1,2}\/\d{1,2}\/\d{4}$/.test(d)) {
          const parts = d.split("/");
          dateKey = `${parts[2]}-${parts[0].padStart(2,"0")}-${parts[1].padStart(2,"0")}`;
        } else if (/^\d{4}\/\d{1,2}\/\d{1,2}$/.test(d)) {
          const parts = d.split("/");
          dateKey = `${parts[0]}-${parts[1].padStart(2,"0")}-${parts[2].padStart(2,"0")}`;
        } else {
          continue; // skip unparseable
        }

        // Only include last 60 days
        const dt = new Date(dateKey);
        if (isNaN(dt.getTime())) continue;
        const now = new Date();
        const diffDays = (now.getTime() - dt.getTime()) / 86400000;
        if (diffDays < 0 || diffDays > 60) continue;

        if (!dateMap[dateKey]) {
          dateMap[dateKey] = { date: dateKey, rental: 0, nail_jobs: 0, restaurant_jobs: 0 };
        }
        if (cats.includes(row.category)) {
          dateMap[dateKey][row.category] += 1;
        }
      }

      // Find actual date range
      const sortedKeys = Object.keys(dateMap).sort();
      const firstDate = sortedKeys[0];
      const lastDate = sortedKeys[sortedKeys.length - 1];
      if (!firstDate || !lastDate) { setLoading(false); return; }

      // Calculate days to show (between first and last, max 14, min 7)
      const rangeDays = Math.max(7, Math.min(14,
        Math.ceil((new Date(lastDate).getTime() - new Date(firstDate).getTime()) / 86400000) + 3
      ));

      // Fill missing dates with 0
      const result: any[] = [];
      for (let i = rangeDays - 1; i >= 0; i--) {
        const d = new Date();
        d.setDate(d.getDate() - i);
        const key = d.toISOString().slice(0, 10);
        result.push(dateMap[key] || { date: key, rental: 0, nail_jobs: 0, restaurant_jobs: 0 });
      }

      setData(result);
      setLoading(false);
    };
    load();
  }, []);

  if (loading) {
    return <div className="h-48 rounded-2xl border border-surface-800 bg-surface-900/50 flex items-center justify-center text-sm text-surface-500">加载中...</div>;
  }

  if (data.length === 0) {
    return <div className="h-48 rounded-2xl border border-surface-800 bg-surface-900/50 flex items-center justify-center text-sm text-surface-500">暂无数据</div>;
  }

  return (
    <div className="rounded-2xl border border-surface-800 bg-surface-900/50 p-5">
      <h2 className="text-sm font-semibold text-surface-300 mb-4">近 14 天趋势</h2>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={data} barGap={2} barCategoryGap="12%">
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
          <XAxis
            dataKey="date"
            tick={{ fill: "#71717a", fontSize: 11 }}
            tickFormatter={(v: string) => v.slice(5)}
            axisLine={{ stroke: "#27272a" }}
            tickLine={false}
          />
          <YAxis tick={{ fill: "#71717a", fontSize: 11 }} axisLine={false} tickLine={false} />
          <Tooltip
            contentStyle={{
              background: "#18181b",
              border: "1px solid #27272a",
              borderRadius: "12px",
              fontSize: "12px",
            }}
            labelFormatter={(v: any) => String(v)}
          />
          <Legend
            formatter={(value: string) => {
              const labels: Record<string, string> = { rental: "租房", nail_jobs: "美甲", restaurant_jobs: "餐馆" };
              return <span className="text-xs text-surface-400">{labels[value] || value}</span>;
            }}
          />
          {(["rental", "nail_jobs", "restaurant_jobs"] as const).map((cat) => (
            <Bar
              key={cat}
              dataKey={cat}
              name={cat}
              fill={CAT_COLORS[cat]}
              radius={[3, 3, 0, 0]}
              stackId="a"
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
