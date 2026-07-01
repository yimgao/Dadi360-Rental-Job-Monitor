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
      // Supabase doesn't support GROUP BY in JS client easily
      const days = 14;
      const cutoff = new Date();
      cutoff.setDate(cutoff.getDate() - days);

      const { data: rows } = await db
        .from("listings")
        .select("found_at, category")
        .gte("found_at", cutoff.toISOString());

      if (!rows) { setLoading(false); return; }

      // Build date + category matrix
      const dateMap: Record<string, any> = {};
      const cats = ["rental", "nail_jobs", "restaurant_jobs"];

      for (const row of rows) {
        const d = new Date(row.found_at).toISOString().slice(0, 10);
        if (!dateMap[d]) {
          dateMap[d] = { date: d, rental: 0, nail_jobs: 0, restaurant_jobs: 0 };
        }
        if (cats.includes(row.category)) {
          dateMap[d][row.category] += 1;
        }
      }

      // Fill missing dates with 0
      const result: any[] = [];
      for (let i = days - 1; i >= 0; i--) {
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
