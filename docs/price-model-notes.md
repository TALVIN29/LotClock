# What Drives a Used Car's Price?

A small, honest machine-learning case study shipped as an interactive product.
Train a gradient-boosted model on **7,903 real used-car listings**, then serve it
**100% in the browser** — no server, no API, no LLM. Move the sliders, watch the
model re-price the car in real time.

**Live demo:** _<add Vercel/Netlify URL after deploy>_

![screenshot](docs/screenshot.png) <!-- add after first deploy -->

---

## The problem

A used-car buyer or seller has one question: *is this price fair?* The signals are
obvious individually (age, mileage, brand, engine) but hard to combine by gut. A
model can — **if** it's trained honestly and its errors are stated plainly. Most
"price predictor" demos quietly cheat; the interesting part here is not cheating.

## The one decision that matters

Some versions of this dataset ship an **ex-showroom price** column. Feeding it in
pushes R² close to 1.0 and makes a beautiful-looking demo — because it's a
near-answer proxy the model just copies. A real seller rarely knows it. So it's
**excluded on purpose.** The model predicts from what a buyer actually sees:

`age · kilometres · brand · engine size · max power · fuel · transmission · owners`

Every score below is on a **held-out 20% test split**, benchmarked against a dumb
"just guess the median price" baseline so the numbers mean something.

## Results

| metric | value |
|---|---|
| Test MAE | **₹79,789** |
| Baseline MAE (median guess) | ₹413,905 |
| Improvement over baseline | **−80.7% error** |
| R² (held-out) | **0.974** |
| Rows after cleaning | 7,903 |

Feature importance says engine power, age and brand carry the most signal — which
is exactly what a human buyer weighs. Good sign the model learned the real thing.

## How it's built (and why it has no backend)

```
raw CarDekho CSV
  → clean (parse "23.4 kmpl" / "1248 CC", derive brand + age)   train.py
  → GradientBoostingRegressor on log(price), 20% hold-out       train.py
  → export every tree to a 168 KB JSON bundle                   train.py
  → evaluate the bundle in ~20 lines of TypeScript              web/lib/predict.ts
  → static Next.js site, deploys anywhere                       web/
```

The usual path is ONNX. `skl2onnx` hit a converter bug against scikit-learn 1.9,
so I export the boosted trees to plain JSON and walk them in TypeScript instead —
smaller asset, zero runtime dependency, and I can **prove it matches**: a test
asserts the JSON bundle predicts the same numbers as scikit-learn, row for row.

## Reproduce

```bash
# 1. model (Python)
python -m venv .venv && .venv/Scripts/activate        # Windows
pip install -r requirements.txt
python train.py                                        # writes model + metrics + chart data
python -m pytest test_train.py -q                      # 4 checks, incl. sklearn↔JSON parity

# 2. site (Node)
cd web && npm install && npm run build                 # static export in web/out
npm run dev                                            # local preview
```

## Honest limits

Indian listings, ~2020 vintage. Prices are **listing** prices, not final sale.
Mileage mixes `kmpl` and `km/kg` units (treated as one proxy). Brands seen fewer
than 30 times are bucketed as `Other`. This estimates a **ballpark**, not a
valuation — and it tells you its typical error (±₹80k) instead of hiding it.

## Data

Public CarDekho used-car listings (`car_data.csv`, 8,128 rows). Not redistributed
here beyond the copy used for training.
