"""Runnable checks behind the three claims that matter (verification step 1).

  1. the model genuinely beats a dumb baseline (the metric means something)
  2. the target never leaks into the features (honest setup)
  3. the JSON tree bundle reproduces sklearn exactly -> the browser port is trustworthy

Run: .venv\\Scripts\\python.exe -m pytest test_train.py -q
"""
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split

import train as T


def _data():
    df = T.load_clean()
    y = np.log1p(df["selling_price"].to_numpy(dtype=float))
    X, names, _ = T.build_matrix(df, None)
    return df, X, y, names


def test_beats_baseline():
    _, X, y, _ = _data()
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=0)
    model = GradientBoostingRegressor(**T.GBR_KW).fit(Xtr, ytr)
    pred = np.expm1(model.predict(Xte))
    true = np.expm1(yte)
    base = np.full_like(true, np.median(np.expm1(ytr)))
    assert mean_absolute_error(true, pred) < 0.5 * mean_absolute_error(true, base)


def test_target_not_in_features():
    # the price column must never appear as an input feature
    _, _, _, names = _data()
    assert not any("selling_price" in n or "price" in n.lower() for n in names)


def test_shuffled_target_kills_signal():
    # sanity: if we destroy the X<->y link, the model must collapse toward baseline.
    # catches accidental leakage that would let a shuffled model still score well.
    _, X, y, _ = _data()
    rng = np.random.default_rng(0)
    y_shuf = rng.permutation(y)
    Xtr, Xte, ytr, yte = train_test_split(X, y_shuf, test_size=0.2, random_state=0)
    model = GradientBoostingRegressor(**T.GBR_KW).fit(Xtr, ytr)
    pred = np.expm1(model.predict(Xte))
    true = np.expm1(yte)
    base = np.full_like(true, np.median(np.expm1(ytr)))
    # with the signal shuffled out, the model can't meaningfully beat the baseline
    assert mean_absolute_error(true, pred) > 0.9 * mean_absolute_error(true, base)


def test_bundle_matches_sklearn():
    # the JSON we ship must predict the SAME numbers as sklearn, row by row.
    _, X, y, _ = _data()
    model = GradientBoostingRegressor(**T.GBR_KW).fit(X, y)
    bundle = T.bundle_from_model(model)
    sk = np.expm1(model.predict(X[:200]))
    js = np.array([T.eval_bundle(bundle, X[i]) for i in range(200)])
    assert np.allclose(sk, js, rtol=1e-4, atol=1.0)  # atol ₹1: JSON rounding only
