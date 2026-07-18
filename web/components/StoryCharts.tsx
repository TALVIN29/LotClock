"use client";
import {
  ResponsiveContainer, LineChart, Line, BarChart, Bar,
  XAxis, YAxis, Tooltip, CartesianGrid, Cell,
} from "recharts";
import type { Meta } from "@/lib/predict";

const ACCENT = "#5b8cff";
const lakh = (n: number) => "₹" + (n / 1e5).toFixed(1) + "L";
const grid = "rgba(128,128,128,0.18)";

type Charts = {
  depreciation: { age: number; price: number }[];
  brand: { brand: string; price: number; count: number }[];
  fuel: { fuel: string; price: number }[];
};

const tip = {
  contentStyle: {
    background: "var(--surface)", border: "1px solid var(--border)",
    borderRadius: 10, color: "var(--text)", fontSize: 13,
  },
  formatter: (v: number) => ["₹" + Math.round(v).toLocaleString("en-IN"), "median"],
};

export function Depreciation({ data }: { data: Charts["depreciation"] }) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <LineChart data={data} margin={{ top: 8, right: 12, bottom: 4, left: 4 }}>
        <CartesianGrid stroke={grid} vertical={false} />
        <XAxis dataKey="age" tick={{ fontSize: 12, fill: "var(--muted)" }}
          label={{ value: "car age (years)", position: "insideBottom", offset: -2, fontSize: 11, fill: "var(--muted)" }} />
        <YAxis tickFormatter={lakh} tick={{ fontSize: 12, fill: "var(--muted)" }} width={48} />
        <Tooltip {...tip} />
        <Line type="monotone" dataKey="price" stroke={ACCENT} strokeWidth={2.5} dot={{ r: 2.5 }} />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function ByBrand({ data }: { data: Charts["brand"] }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 16, bottom: 4, left: 8 }}>
        <CartesianGrid stroke={grid} horizontal={false} />
        <XAxis type="number" tickFormatter={lakh} tick={{ fontSize: 12, fill: "var(--muted)" }} />
        <YAxis type="category" dataKey="brand" width={78} tick={{ fontSize: 12, fill: "var(--muted)" }} />
        <Tooltip {...tip} />
        <Bar dataKey="price" fill={ACCENT} radius={[0, 4, 4, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function Importance({ meta }: { meta: Meta }) {
  const data = meta.importance.slice(0, 8).map((d) => ({
    feature: d.feature.replace(/_/g, " "),
    pct: Math.round(d.importance * 100),
  }));
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 24, bottom: 4, left: 8 }}>
        <CartesianGrid stroke={grid} horizontal={false} />
        <XAxis type="number" unit="%" tick={{ fontSize: 12, fill: "var(--muted)" }} />
        <YAxis type="category" dataKey="feature" width={96} tick={{ fontSize: 12, fill: "var(--muted)" }} />
        <Tooltip {...tip} formatter={(v: number) => [v + "%", "importance"]} />
        <Bar dataKey="pct" radius={[0, 4, 4, 0]}>
          {data.map((_, i) => (
            <Cell key={i} fill={i === 0 ? "#35c493" : ACCENT} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
