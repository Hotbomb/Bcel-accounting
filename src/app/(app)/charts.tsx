"use client";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatKip } from "@/lib/money";

export function DailyChart({ data }: { data: Array<{ label: string; total: number }> }) {
  return (
    <div className="h-48 w-full" role="img" aria-label="Spending per day this month">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 0, left: 0, bottom: 0 }}>
          <XAxis dataKey="label" tickLine={false} axisLine={false} fontSize={11} interval="preserveStartEnd" stroke="#78716c" />
          <YAxis hide />
          <Tooltip
            cursor={{ fill: "#f5f5f4" }}
            formatter={(v) => [formatKip(Number(v)), "Spent"]}
            labelFormatter={(l) => `Day ${l}`}
            contentStyle={{ borderRadius: 12, border: "1px solid #e7e5e4", fontSize: 13 }}
          />
          <Bar dataKey="total" fill="#0f766e" radius={[4, 4, 0, 0]} maxBarSize={18} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
