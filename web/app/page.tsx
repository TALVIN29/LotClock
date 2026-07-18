"use client";
import { useEffect, useState } from "react";
import type { Bundle, Meta } from "@/lib/predict";
import Predictor from "@/components/Predictor";
import { Depreciation, ByBrand, Importance } from "@/components/StoryCharts";

type Charts = {
  depreciation: { age: number; price: number }[];
  brand: { brand: string; price: number; count: number }[];
  fuel: { fuel: string; price: number }[];
};

export default function Home() {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [bundle, setBundle] = useState<Bundle | null>(null);
  const [charts, setCharts] = useState<Charts | null>(null);

  useEffect(() => {
    Promise.all([
      fetch("./feature_meta.json").then((r) => r.json()),
      fetch("./model_trees.json").then((r) => r.json()),
      fetch("./chart_data.json").then((r) => r.json()),
    ]).then(([m, b, c]) => { setMeta(m); setBundle(b); setCharts(c); });
  }, []);

  if (!meta || !bundle || !charts) {
    return <main className="wrap"><section><p>Loading model…</p></section></main>;
  }
  const m = meta.metrics;

  return (
    <main>
      <div className="wrap">
        {/* HERO */}
        <section style={{ borderTop: "none" }}>
          <div className="eyebrow">Used-car resale · India</div>
          <h1>What actually drives a used car&apos;s price?</h1>
          <p className="lead">
            A gradient-boosted model trained on <strong>{m.n_rows.toLocaleString()}</strong> real
            listings, running <strong>100% in your browser</strong> — no server, no API, no LLM.
            Move the sliders below and watch it think.
          </p>
          <div className="grid cols-3" style={{ marginTop: 24 }}>
            <div className="card metric">
              <span className="big good">−{m.improvement_pct}%</span>
              <span className="label">error vs a naïve median guess</span>
            </div>
            <div className="card metric">
              <span className="big">±₹{Math.round(m.mae_inr / 1000)}k</span>
              <span className="label">typical prediction error (MAE)</span>
            </div>
            <div className="card metric">
              <span className="big">{m.r2}</span>
              <span className="label">R² on held-out cars</span>
            </div>
          </div>
        </section>

        {/* PREDICTOR */}
        <section>
          <span className="tag">Live model</span>
          <h2 style={{ marginTop: 10 }}>Price a car yourself</h2>
          <p>Every change re-runs the full 500-tree model client-side. The number matches
            the Python model exactly — a parity test asserts it.</p>
          <div className="card" style={{ marginTop: 16 }}>
            <Predictor meta={meta} bundle={bundle} />
          </div>
        </section>

        {/* STORY */}
        <section>
          <div className="eyebrow">The story in the data</div>
          <h2>1. Cars fall off a cliff, then coast</h2>
          <p>Median resale price by age. The steepest drop is in the first few years —
            classic depreciation — then it flattens as cars approach scrap value.</p>
          <div className="card chart-box"><Depreciation data={charts.depreciation} /></div>

          <h2 style={{ marginTop: 40 }}>2. Brand sets the baseline</h2>
          <p>Median price by brand. Luxury badges (BMW, Audi) hold far higher resale than
            mass-market makes — before mileage or age enter the picture.</p>
          <div className="card chart-box"><ByBrand data={charts.brand} /></div>

          <h2 style={{ marginTop: 40 }}>3. What the model leans on</h2>
          <p>Feature importance from the trained model. Engine power, age and brand carry
            the most signal — which is exactly what a human buyer weighs.</p>
          <div className="card chart-box"><Importance meta={meta} /></div>
        </section>

        {/* HONEST LIMITS */}
        <section>
          <div className="eyebrow">The honest part</div>
          <h2>One decision, and what I did not do</h2>
          <p>
            The dataset ships an <code>ex-showroom price</code> column in some versions. Feeding
            that in would push R² near 1.0 — but it is a near-answer proxy a real seller rarely
            knows, so it is <strong>excluded on purpose</strong>. The model predicts from things a
            buyer actually sees: age, kilometres, brand, power, fuel, owners.
          </p>
          <p>
            Every score here is on a <strong>held-out 20% test split</strong>, compared against a
            dumb median baseline so the numbers mean something. Limits: Indian listings, ~2020
            vintage, listing prices (not final sale), <code>kmpl</code>/<code>km/kg</code> mileage
            units mixed. It estimates a ballpark, not a valuation.
          </p>
        </section>

        <footer>
          Built with scikit-learn (gradient boosting) → tree bundle exported to JSON →
          evaluated in ~20 lines of TypeScript. Charts: Recharts. Data: public CarDekho
          listings ({m.n_rows.toLocaleString()} rows). No backend, no tracking.
        </footer>
      </div>
    </main>
  );
}
