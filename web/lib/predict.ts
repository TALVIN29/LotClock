// Pure client-side inference. Mirrors train.py::eval_bundle exactly — the parity
// is asserted in test_train.py::test_bundle_matches_sklearn, so these numbers
// match sklearn to within JSON rounding. No ONNX, no server, no LLM.

export type Tree = { f: number[]; t: number[]; l: number[]; r: number[]; v: number[] };
export type Bundle = { base: number; lr: number; trees: Tree[] };

export type Meta = {
  numeric: { name: string; min: number; max: number; default: number }[];
  categorical: Record<string, string[]>;
  feature_names: string[];
  importance: { feature: string; importance: number }[];
  target_transform: string;
  ref_year: number;
  metrics: {
    n_rows: number; n_features: number; mae_inr: number;
    baseline_mae_inr: number; improvement_pct: number; r2: number;
  };
};

export type Inputs = Record<string, number | string>;

/** Build the model's feature vector in the exact column order it was trained on. */
export function buildVector(meta: Meta, inputs: Inputs): number[] {
  return meta.feature_names.map((name) => {
    if (name.includes("=")) {
      const [field, level] = name.split("=");
      return inputs[field] === level ? 1 : 0;
    }
    return Number(inputs[name]);
  });
}

function evalTree(tree: Tree, x: number[]): number {
  let node = 0;
  while (tree.f[node] !== -2) {
    node = x[tree.f[node]] <= tree.t[node] ? tree.l[node] : tree.r[node];
  }
  return tree.v[node];
}

/** Returns the predicted price in INR. */
export function predict(bundle: Bundle, x: number[]): number {
  let total = bundle.base;
  for (const tree of bundle.trees) total += bundle.lr * evalTree(tree, x);
  return Math.expm1(total);
}

export const fmtINR = (n: number): string =>
  "₹" + Math.round(n).toLocaleString("en-IN");
