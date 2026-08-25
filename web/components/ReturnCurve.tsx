"use client";
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis,
  Tooltip, CartesianGrid, ReferenceArea,
} from "recharts";

const ACCENT = "#5b8cff";
const grid = "rgba(128,128,128,0.18)";

// Return rates from exit_rule.py, refit on all 30 observed days (2026-08-24).
// Day 10 is omitted deliberately: its denominator is entirely still-open
// absences, so its 0.0% is the window ending, not listings staying gone.
const data = [
  { days: 1, rate: 97.3 }, { days: 2, rate: 93.2 }, { days: 3, rate: 85.6 },
  { days: 4, rate: 72.5 }, { days: 5, rate: 60.2 }, { days: 6, rate: 52.6 },
  { days: 7, rate: 47.8 }, { days: 8, rate: 38.4 }, { days: 9, rate: 34.8 },
];

export default function ReturnCurve() {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={data} margin={{ top: 8, right: 12, bottom: 4, left: 4 }}>
        <CartesianGrid stroke={grid} vertical={false} />
        <ReferenceArea y1={0} y2={5} fill={ACCENT} fillOpacity={0.12} />
        <XAxis dataKey="days" tick={{ fontSize: 12 }} stroke="var(--muted)"
          label={{ value: "consecutive observed days absent", position: "insideBottom", offset: -2, fontSize: 12, fill: "var(--muted)" }} />
        <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} stroke="var(--muted)"
          tickFormatter={(v) => v + "%"} />
        <Tooltip
          contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 10, color: "var(--text)", fontSize: 13 }}
          formatter={(v: number) => [v + "%", "still came back"]}
          labelFormatter={(d) => d + " days absent"} />
        <Line type="monotone" dataKey="rate" stroke={ACCENT} strokeWidth={2.5} dot={{ r: 3 }} />
      </LineChart>
    </ResponsiveContainer>
  );
}
