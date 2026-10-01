"use client";
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis,
  Tooltip, CartesianGrid, ReferenceArea,
} from "recharts";

const ACCENT = "#5b8cff";
const MUTED = "#9aa3ae";
const grid = "rgba(128,128,128,0.18)";

// Return rates from exit_rule.py, refit on all 30 observed days (2026-08-24),
// partial-harvest and census days pooled -- the mix teardown-04 withdraws.
// Day 10 is omitted deliberately: its denominator is entirely still-open
// absences, so its 0.0% is the window ending, not listings staying gone.
const pooled = [97.3, 93.2, 85.6, 72.5, 60.2, 52.6, 47.8, 38.4, 34.8];

// Census-only refit, 38 observation days to 2026-10-01. Stops at 8: the
// longest closed absence; rows past it have zero observed returns.
const census = [95.4, 91.3, 79.3, 52.6, 25.8, 6.5, 2.4, 1.0];

export default function ReturnCurve({ withCensus = false }: { withCensus?: boolean }) {
  const data = pooled.map((rate, i) => ({ days: i + 1, rate, census: census[i] }));
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
          formatter={(v: number, name: string) => [v + "%", name === "census" ? "census only" : withCensus ? "pooled (withdrawn)" : "still came back"]}
          labelFormatter={(d) => d + " days absent"} />
        <Line type="monotone" dataKey="rate" stroke={withCensus ? MUTED : ACCENT}
          strokeDasharray={withCensus ? "5 4" : undefined} strokeWidth={2.5} dot={{ r: 3 }} />
        {withCensus && (
          <Line type="monotone" dataKey="census" stroke={ACCENT} strokeWidth={2.5} dot={{ r: 3 }} />
        )}
      </LineChart>
    </ResponsiveContainer>
  );
}
