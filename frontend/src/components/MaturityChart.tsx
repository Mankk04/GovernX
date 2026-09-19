import React from "react";
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer,
} from "recharts";
import { MaturityScore } from "../api/client";

export default function MaturityChart({ scores }: { scores: MaturityScore[] }) {
  const data = scores.map((s) => ({
    function: s.function_id,
    tier: s.tier_level,
    fullMark: 4,
  }));

  return (
    <ResponsiveContainer width="100%" height={320}>
      <RadarChart data={data} outerRadius={110}>
        <PolarGrid />
        <PolarAngleAxis dataKey="function" />
        <PolarRadiusAxis angle={30} domain={[0, 4]} tickCount={5} />
        <Radar name="Maturity Tier" dataKey="tier" stroke="#1a3d7c" fill="#1a3d7c" fillOpacity={0.45} />
      </RadarChart>
    </ResponsiveContainer>
  );
}
