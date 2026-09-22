import React from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { RiskSummary } from "../api/client";

export default function RiskSummaryCard({ summary }: { summary: RiskSummary }) {
  const chartData = summary.top_findings.map((f) => ({
    name: f.resource,
    value_at_risk: f.value_at_risk,
  }));

  return (
    <div className="panel">
      <h2>Top Financial Risk Findings</h2>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={chartData} layout="vertical" margin={{ left: 40 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" tickFormatter={(v) => `$${(v / 1_000_000).toFixed(1)}M`} />
          <YAxis type="category" dataKey="name" width={160} fontSize={12} />
          <Tooltip formatter={(v: number) => `$${v.toLocaleString()}`} />
          <Bar dataKey="value_at_risk" fill="#d7263d" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
