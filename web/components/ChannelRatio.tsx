"use client";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis,
  Tooltip, CartesianGrid, Cell,
} from "recharts";

const ACCENT = "#5b8cff";
const WARM = "#e0793a";
const grid = "rgba(128,128,128,0.18)";

// From jpj_join.py, 2026-09-11. Listings are the census-era Kaggle export
// (13,324, all model years); registrations are JPJ first registrations
// 2026-01-01..2026-08-31. Makes with fewer than 20 listings are omitted --
// below that the ratio swings on single cars.
const data = [
  { make: "Bentley", ratio: 4087.0, listings: 94, regs: 23 },
  { make: "McLaren", ratio: 2857.1, listings: 20, regs: 7 },
  { make: "Rolls Royce", ratio: 1954.5, listings: 86, regs: 44 },
  { make: "Lamborghini", ratio: 1522.1, listings: 172, regs: 113 },
  { make: "Ferrari", ratio: 1294.1, listings: 154, regs: 119 },
  { make: "Porsche", ratio: 642.1, listings: 897, regs: 1397 },
  { make: "Land Rover", ratio: 562.4, listings: 311, regs: 553 },
  { make: "Mercedes Benz", ratio: 346.3, listings: 1724, regs: 4979 },
  { make: "BMW", ratio: 242.4, listings: 967, regs: 3989 },
  { make: "Lexus", ratio: 235.2, listings: 1015, regs: 4315 },
  { make: "Toyota", ratio: 57.1, listings: 4166, regs: 72942 },
  { make: "Honda", ratio: 24.0, listings: 894, regs: 37194 },
  { make: "Mitsubishi", ratio: 11.3, listings: 100, regs: 8824 },
  { make: "Proton", ratio: 2.7, listings: 359, regs: 135169 },
  { make: "Perodua", ratio: 1.4, listings: 300, regs: 219559 },
];

// Log scale: the spread is 2,919x, so a linear axis renders every national
// make as a zero-height stub and hides the entire bottom of the story.
const ticks = [1, 10, 100, 1000, 10000];

export default function ChannelRatio() {
  return (
    <ResponsiveContainer width="100%" height={460}>
      <BarChart data={data} layout="vertical"
        margin={{ top: 8, right: 16, bottom: 18, left: 4 }}>
        <CartesianGrid stroke={grid} horizontal={false} />
        <XAxis type="number" scale="log" domain={[1, 10000]} ticks={ticks}
          tick={{ fontSize: 12 }} stroke="var(--muted)"
          tickFormatter={(v) => (v >= 1000 ? v / 1000 + "k" : String(v))}
          label={{ value: "listings per 1,000 first registrations (log scale)",
                   position: "insideBottom", offset: -8, fontSize: 12, fill: "var(--muted)" }} />
        <YAxis type="category" dataKey="make" width={104}
          tick={{ fontSize: 12 }} stroke="var(--muted)" />
        <Tooltip
          contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)",
                          borderRadius: 10, color: "var(--text)", fontSize: 13 }}
          formatter={(v: number, _n, p) => [
            `${v.toLocaleString()} per 1k · ${p.payload.listings.toLocaleString()} listings vs ${p.payload.regs.toLocaleString()} registrations`,
            "",
          ]}
          labelFormatter={(m) => String(m)} />
        <Bar dataKey="ratio" radius={[0, 4, 4, 0]}>
          {data.map((d) => (
            // Warm = the two national makes, the ones the lot barely carries.
            <Cell key={d.make}
              fill={d.make === "Perodua" || d.make === "Proton" ? WARM : ACCENT} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
