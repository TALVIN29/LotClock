"""Assemble analysis.ipynb from narrative + code cells, reusing train.py so the
notebook never drifts from the shipped model. Executed afterwards to embed charts.
This builder is scaffolding — the artifact is analysis.ipynb."""
import nbformat as nbf

nb = nbf.v4.new_notebook()
md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
cells = []

cells.append(md(
    "# What Drives a Used Car's Price? — analysis\n\n"
    "A short, honest modelling walk-through. Goal: predict a used car's resale price "
    "from what a buyer actually sees, state the error plainly, and don't cheat.\n\n"
    "The cleaning/feature code lives in `train.py` and is reused here so this notebook "
    "and the shipped model can never disagree."
))

cells.append(code(
    "import numpy as np, pandas as pd\n"
    "import matplotlib.pyplot as plt\n"
    "from sklearn.ensemble import GradientBoostingRegressor\n"
    "from sklearn.model_selection import train_test_split\n"
    "from sklearn.metrics import mean_absolute_error, r2_score\n"
    "import train as T\n"
    "plt.rcParams['figure.figsize'] = (7, 4)\n"
    "df = T.load_clean()\n"
    "print(df.shape)\n"
    "df[['name','year','selling_price','km_driven','fuel','max_power_bhp','brand']].head()"
))

cells.append(md(
    "## The target is heavily right-skewed\n"
    "A few expensive cars stretch the tail. We train on `log(price)` so the model isn't "
    "dominated by them, then invert for reporting."
))
cells.append(code(
    "fig, ax = plt.subplots(1, 2, figsize=(10,3.5))\n"
    "ax[0].hist(df['selling_price']/1e5, bins=40, color='#2f6df0'); ax[0].set_title('price (₹ lakh)')\n"
    "ax[1].hist(np.log1p(df['selling_price']), bins=40, color='#12805c'); ax[1].set_title('log(price)')\n"
    "plt.tight_layout(); plt.show()"
))

cells.append(md("## Cars depreciate fast, then coast\nMedian resale price by age."))
cells.append(code(
    "dep = df[df['car_age'].between(0,18)].groupby('car_age')['selling_price'].median()/1e5\n"
    "dep.plot(marker='o', color='#2f6df0'); plt.ylabel('median price (₹ lakh)')\n"
    "plt.xlabel('car age (years)'); plt.title('Depreciation curve'); plt.grid(alpha=.3); plt.show()"
))

cells.append(md("## Brand sets the baseline\nMedian price for the most common brands."))
cells.append(code(
    "top = df['brand'].value_counts().head(12).index\n"
    "(df[df['brand'].isin(top)].groupby('brand')['selling_price'].median()/1e5)\\\n"
    "  .sort_values().plot.barh(color='#2f6df0'); plt.xlabel('median price (₹ lakh)')\n"
    "plt.title('Resale by brand'); plt.show()"
))

cells.append(md(
    "## Modelling — honestly\n"
    "One-hot the categoricals, hold out 20%, fit gradient boosting on `log(price)`. "
    "The only score that counts is on cars the model never saw, compared to a dumb "
    "median-guess baseline.\n\n"
    "**The decision:** we do *not* feed in ex-showroom price (a near-answer proxy). "
    "The model earns its accuracy from age, km, brand, power, fuel, owners."
))
cells.append(code(
    "y = np.log1p(df['selling_price'].to_numpy(float))\n"
    "X, names, _ = T.build_matrix(df, None)\n"
    "Xtr,Xte,ytr,yte = train_test_split(X, y, test_size=0.2, random_state=42)\n"
    "m = GradientBoostingRegressor(**T.GBR_KW).fit(Xtr, ytr)\n"
    "pred, true = np.expm1(m.predict(Xte)), np.expm1(yte)\n"
    "base = np.full_like(true, np.median(np.expm1(ytr)))\n"
    "mae, bmae = mean_absolute_error(true,pred), mean_absolute_error(true,base)\n"
    "print(f'model MAE    : ₹{mae:,.0f}')\n"
    "print(f'baseline MAE : ₹{bmae:,.0f}')\n"
    "print(f'improvement  : {100*(bmae-mae)/bmae:.1f}%')\n"
    "print(f'R^2          : {r2_score(true,pred):.3f}')"
))

cells.append(md(
    "## What the model leans on\n"
    "Importances aggregated from one-hot columns back to the original field. "
    "Power, age and brand dominate — the same things a person weighs."
))
cells.append(code(
    "agg = {}\n"
    "for n,v in zip(names, m.feature_importances_):\n"
    "    agg[n.split('=')[0]] = agg.get(n.split('=')[0],0)+v\n"
    "imp = pd.Series(agg).sort_values()\n"
    "imp.plot.barh(color=['#12805c' if i==len(imp)-1 else '#2f6df0' for i in range(len(imp))])\n"
    "plt.xlabel('importance'); plt.title('What drives the prediction'); plt.show()"
))

cells.append(md(
    "## Limits (stated, not hidden)\n"
    "Indian listings, ~2020 vintage. **Listing** prices, not final sale. Mileage mixes "
    "`kmpl`/`km per kg`. Rare brands bucketed as `Other`. This is a ballpark with a known "
    "±₹80k typical error — the same model, exported to JSON, runs live in the browser demo."
))

nb["cells"] = cells
nbf.write(nb, "analysis.ipynb")
print("wrote analysis.ipynb")
