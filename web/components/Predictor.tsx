"use client";
import { useMemo, useState } from "react";
import { buildVector, predict, fmtINR, type Bundle, type Meta, type Inputs } from "@/lib/predict";

const LABELS: Record<string, string> = {
  car_age: "Age (years)", km_driven: "Kilometres driven", mileage_kmpl: "Mileage (kmpl)",
  engine_cc: "Engine (CC)", max_power_bhp: "Max power (bhp)", seats: "Seats", owner_rank: "Owners (1=first)",
};

function initInputs(meta: Meta): Inputs {
  const v: Inputs = {};
  for (const n of meta.numeric) v[n.name] = n.default;
  for (const [field, levels] of Object.entries(meta.categorical)) v[field] = levels[0];
  return v;
}

export default function Predictor({ meta, bundle }: { meta: Meta; bundle: Bundle }) {
  const [inputs, setInputs] = useState<Inputs>(() => initInputs(meta));
  const price = useMemo(() => predict(bundle, buildVector(meta, inputs)), [meta, bundle, inputs]);
  const set = (k: string, val: number | string) => setInputs((p) => ({ ...p, [k]: val }));

  return (
    <div>
      <div className="controls">
        {meta.numeric.map((n) => (
          <div key={n.name}>
            <label>
              {LABELS[n.name] ?? n.name}
              <span className="val">{Math.round(Number(inputs[n.name])).toLocaleString("en-IN")}</span>
            </label>
            <input
              type="range" min={n.min} max={n.max}
              step={n.name === "mileage_kmpl" ? 0.1 : 1}
              value={Number(inputs[n.name])}
              onChange={(e) => set(n.name, Number(e.target.value))}
            />
          </div>
        ))}
        {Object.entries(meta.categorical).map(([field, levels]) => (
          <div key={field}>
            <label>{field.replace(/_/g, " ")}</label>
            <select value={String(inputs[field])} onChange={(e) => set(field, e.target.value)}>
              {levels.map((l) => <option key={l} value={l}>{l}</option>)}
            </select>
          </div>
        ))}
      </div>

      <div className="price-out">
        <div className="amount">{fmtINR(price)}</div>
        <div className="sub">
          estimated resale price · typical error ±{fmtINR(meta.metrics.mae_inr)}
        </div>
      </div>
    </div>
  );
}
