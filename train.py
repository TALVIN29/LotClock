"""Train a used-car resale-price model and export it to run in the browser.

Pipeline: clean the raw cardekho CSV -> engineer features -> hold-out split ->
HistGradientBoosting on log(price) -> honest eval vs a baseline -> export the
model to ONNX plus feature_meta.json so the web app can rebuild the exact same
feature vector in JS (no ColumnTransformer in ONNX = far fewer export headaches).

The ONE modelling decision worth telling (README): we predict resale price from
things a buyer actually knows up front (age, km, brand, power, fuel, ...). We do
NOT feed the model the original ex-showroom price — that is a near-answer proxy
that would inflate the score while teaching the model nothing useful.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

# GradientBoosting (not Hist): its trees expose .tree_ arrays we can dump to JSON
# and re-evaluate in ~30 lines of JS — no ONNX runtime, no skl2onnx converter bug.
GBR_KW = dict(n_estimators=500, learning_rate=0.05, max_depth=3,
              min_samples_leaf=15, subsample=0.9, random_state=42)

HERE = Path(__file__).parent
CSV = HERE / "car_data.csv"
REF_YEAR = 2020  # dataset collection era; car_age = REF_YEAR - year

OWNER_ORDER = {
    "First Owner": 1, "Second Owner": 2, "Third Owner": 3,
    "Fourth & Above Owner": 4, "Test Drive Car": 0,
}


def _num(series: pd.Series) -> pd.Series:
    """Pull the first number out of strings like '23.4 kmpl', '1248 CC', '74 bhp'."""
    return pd.to_numeric(
        series.astype(str).str.extract(r"([-+]?\d*\.?\d+)")[0], errors="coerce"
    )


def load_clean() -> pd.DataFrame:
    df = pd.read_csv(CSV)
    df["brand"] = df["name"].str.split().str[0].str.title()
    df["mileage_kmpl"] = _num(df["mileage"])       # note: kmpl vs km/kg mixed; fine as proxy
    df["engine_cc"] = _num(df["engine"])
    df["max_power_bhp"] = _num(df["max_power"])
    df["car_age"] = REF_YEAR - df["year"]
    df["owner_rank"] = df["owner"].map(OWNER_ORDER)
    # keep only brands with enough support so one-hot stays sane
    common = df["brand"].value_counts()
    df["brand"] = df["brand"].where(df["brand"].isin(common[common >= 30].index), "Other")
    df = df.dropna(subset=[
        "selling_price", "km_driven", "mileage_kmpl", "engine_cc",
        "max_power_bhp", "seats", "car_age", "owner_rank",
    ])
    # drop obvious data-entry garbage
    df = df[(df["selling_price"] > 20000) & (df["selling_price"] < 1e7)]
    df = df[(df["km_driven"] > 0) & (df["km_driven"] < 1e6)]
    return df.reset_index(drop=True)


NUMERIC = ["car_age", "km_driven", "mileage_kmpl", "engine_cc", "max_power_bhp",
           "seats", "owner_rank"]
CATEGORICAL = ["brand", "fuel", "seller_type", "transmission"]


def build_matrix(df: pd.DataFrame, cat_levels: dict[str, list[str]] | None):
    """Return (X float matrix, feature_names, cat_levels). Deterministic one-hot
    so JS can reproduce it from feature_meta.json."""
    if cat_levels is None:
        cat_levels = {c: sorted(df[c].dropna().unique().tolist()) for c in CATEGORICAL}
    cols, names = [], []
    for c in NUMERIC:
        cols.append(df[c].to_numpy(dtype=float).reshape(-1, 1))
        names.append(c)
    for c in CATEGORICAL:
        for lvl in cat_levels[c]:
            cols.append((df[c] == lvl).to_numpy(dtype=float).reshape(-1, 1))
            names.append(f"{c}={lvl}")
    return np.hstack(cols), names, cat_levels


def main() -> dict:
    df = load_clean()
    y = np.log1p(df["selling_price"].to_numpy(dtype=float))  # log target: price is right-skewed
    X, names, cat_levels = build_matrix(df, None)

    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
    model = GradientBoostingRegressor(**GBR_KW)
    model.fit(Xtr, ytr)

    pred = np.expm1(model.predict(Xte))
    true = np.expm1(yte)
    # baseline: predict the median training price for everything (dumb but honest)
    base_pred = np.full_like(true, np.median(np.expm1(ytr)))
    mae = mean_absolute_error(true, pred)
    base_mae = mean_absolute_error(true, base_pred)
    r2 = r2_score(true, pred)

    metrics = {
        "n_rows": int(len(df)),
        "n_features": len(names),
        "mae_inr": round(float(mae)),
        "baseline_mae_inr": round(float(base_mae)),
        "improvement_pct": round(100 * (base_mae - mae) / base_mae, 1),
        "r2": round(float(r2), 3),
    }

    # retrain on ALL data for the shipped model
    final = GradientBoostingRegressor(**GBR_KW)
    final.fit(X, y)
    _export_trees(final)

    # aggregate one-hot importances back to the original field for storytelling
    imp = final.feature_importances_
    agg: dict[str, float] = {}
    for name, v in zip(names, imp):
        key = name.split("=")[0]
        agg[key] = agg.get(key, 0.0) + float(v)
    importance = sorted(({"feature": k, "importance": round(v, 4)}
                         for k, v in agg.items()),
                        key=lambda d: d["importance"], reverse=True)

    meta = {
        "numeric": [
            {"name": c,
             "min": float(df[c].quantile(0.01)),
             "max": float(df[c].quantile(0.99)),
             "default": float(df[c].median())}
            for c in NUMERIC
        ],
        "categorical": {c: cat_levels[c] for c in CATEGORICAL},
        "feature_names": names,
        "importance": importance,
        "target_transform": "log1p",   # JS: price = expm1(model_output)
        "ref_year": REF_YEAR,
        "metrics": metrics,
    }
    (HERE / "feature_meta.json").write_text(json.dumps(meta, indent=2))
    (HERE / "web" / "public").mkdir(parents=True, exist_ok=True)
    (HERE / "web" / "public" / "feature_meta.json").write_text(json.dumps(meta, indent=2))

    _export_charts(df)
    print(json.dumps(metrics, indent=2))
    return metrics


def _export_charts(df: pd.DataFrame) -> None:
    """Small pre-aggregated data for the story charts (keeps the CSV off the client)."""
    inr = lambda s: round(float(s))
    dep = (df[df["car_age"].between(0, 18)].groupby("car_age")["selling_price"]
           .median().reset_index())
    depreciation = [{"age": int(a), "price": inr(p)} for a, p in dep.values]

    top = df["brand"].value_counts().head(12).index
    bybrand = (df[df["brand"].isin(top)].groupby("brand")["selling_price"]
               .agg(["median", "size"]).reset_index()
               .sort_values("median", ascending=False))
    brand = [{"brand": b, "price": inr(m), "count": int(n)} for b, m, n in bybrand.values]

    byfuel = df.groupby("fuel")["selling_price"].median().sort_values(ascending=False)
    fuel = [{"fuel": f, "price": inr(p)} for f, p in byfuel.items()]

    charts = {"depreciation": depreciation, "brand": brand, "fuel": fuel}
    (HERE / "web" / "public" / "chart_data.json").write_text(json.dumps(charts))


def bundle_from_model(model: GradientBoostingRegressor) -> dict:
    """Serialize a boosted-tree model to plain arrays. Prediction reproduced as:
    price = expm1(base + lr * sum_over_trees(eval_tree(x))). Same math in JS."""
    trees = []
    for stage in model.estimators_.ravel():
        t = stage.tree_
        trees.append({
            "f": t.feature.astype(int).tolist(),          # -2 at leaves
            "t": [round(float(x), 6) for x in t.threshold],
            "l": t.children_left.astype(int).tolist(),
            "r": t.children_right.astype(int).tolist(),
            "v": [round(float(x), 6) for x in t.value.ravel()],
        })
    return {
        "base": float(np.ravel(model.init_.constant_)[0]),
        "lr": float(model.learning_rate),
        "trees": trees,
    }


def eval_bundle(bundle: dict, x) -> float:
    """Reference impl of the JS evaluator — kept in sync with Predictor.tsx."""
    total = bundle["base"]
    for tree in bundle["trees"]:
        node = 0
        while tree["f"][node] != -2:
            node = tree["l"][node] if x[tree["f"][node]] <= tree["t"][node] else tree["r"][node]
        total += bundle["lr"] * tree["v"][node]
    return float(np.expm1(total))


def _export_trees(model: GradientBoostingRegressor) -> None:
    bundle = json.dumps(bundle_from_model(model), separators=(",", ":"))
    (HERE / "web" / "public").mkdir(parents=True, exist_ok=True)
    (HERE / "web" / "public" / "model_trees.json").write_text(bundle)
    (HERE / "model_trees.json").write_text(bundle)


if __name__ == "__main__":
    main()
