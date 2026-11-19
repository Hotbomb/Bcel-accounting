"use client";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatKip } from "@/lib/money";

export function DailyChart({ data }: { data: Array<{ label: string; total: number }> }) {
  return (
    <div className="h-48 w-full" role="img" aria-label="Spending per day this month">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 0, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="barRed" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#d01b25" />
              <stop offset="100%" stopColor="#b8121c" stopOpacity={0.55} />
            </linearGradient>
          </defs>
          <XAxis dataKey="label" tickLine={false} axisLine={false} fontSize={11} interval="preserveStartEnd" stroke="#8a7172" />
          <YAxis hide />
          <Tooltip
            cursor={{ fill: "rgba(184,18,28,0.06)" }}
            formatter={(v) => [formatKip(Number(v)), "Spent"]}
            labelFormatter={(l) => `Day ${l}`}
            contentStyle={{ borderRadius: 16, border: "1px solid rgba(255,255,255,0.8)", background: "rgba(255,255,255,0.85)", backdropFilter: "blur(12px)", fontSize: 13 }}
          />
          <Bar dataKey="total" fill="url(#barRed)" radius={[6, 6, 2, 2]} maxBarSize={18} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
