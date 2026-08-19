"""Assemble kaggle/lotclock_starter.ipynb. Scaffolding -- the artifact is the .ipynb."""
import nbformat as nbf

nb = nbf.v4.new_notebook()
md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
cells = []

cells.append(md(
    "# LotClock — Malaysian used-car listings, and why \"days to sell\" isn't in here yet\n\n"
    "Daily snapshots of a Malaysian used-car index, collected since 2026-07-19.\n"
    "Two files:\n\n"
    "- `lotclock_daily_coverage.csv` — one row per collection day: how much of the site\n"
    "  was actually harvested. Read this **before** the listings file.\n"
    "- `lotclock_listings.csv` — one row per listing in the full-census era, with\n"
    "  `duration_obs_days` / `event_exited` for survival analysis.\n\n"
    "This notebook does three things: shows the coverage honestly, measures price cuts,\n"
    "and then demonstrates why the days-on-market question is **not answerable yet** —\n"
    "99.9% right-censoring. That last part is the useful bit; most public analyses of\n"
    "listing data quietly report the median of the sold-and-observed cars and call it\n"
    "\"time to sell\", which is survivorship bias with a number attached."
))

cells.append(code(
    "import pandas as pd, numpy as np\n"
    "import matplotlib.pyplot as plt\n"
    "plt.rcParams['figure.figsize'] = (8, 4)\n"
    "from pathlib import Path\n"
    "# runs on Kaggle and locally: the input mount if it exists, else this folder\n"
    "D = Path('/kaggle/input/malaysian-used-car-listings-daily-snapshots')\n"
    "if not D.exists():\n"
    "    D = Path('.')\n"
    "cov = pd.read_csv(D / 'lotclock_daily_coverage.csv', parse_dates=['date'])\n"
    "df  = pd.read_csv(D / 'lotclock_listings.csv')\n"
    "print(cov.shape, df.shape)\n"
    "cov.tail(12)"
))

cells.append(md(
    "## 1. Coverage first\n\n"
    "The crawl hit its page cap until 2026-08-09, harvesting ~15% of the site. From\n"
    "2026-08-09 it walks to exhaustion (~12,400 listings). Those are two different\n"
    "sampling regimes and pooling them would invent thousands of fake disappearances.\n"
    "A few census runs were also killed mid-walk; they are flagged\n"
    "`is_observation_day = 0` and must be dropped, not treated as light days."
))

cells.append(code(
    "ax = cov.plot.bar(x='date', y='listings_seen', legend=False,\n"
    "                  color=np.where(cov.is_observation_day == 1, '#2b7', '#c55'))\n"
    "ax.set_xticklabels([d.strftime('%m-%d') for d in cov.date], rotation=90)\n"
    "ax.set_ylabel('listings seen'); ax.set_title('red = not an observation day')\n"
    "plt.tight_layout(); plt.show()\n"
    "cov.groupby('coverage_era').listings_seen.agg(['count', 'median'])"
))

cells.append(md(
    "## 2. What this sample actually is\n\n"
    "Not \"the Malaysian used-car market\". It is one dealer-heavy index, and it skews\n"
    "premium and Klang-Valley. Say so before quoting any median."
))

cells.append(code(
    "print('median asking price: RM {:,.0f}'.format(df.first_price_myr.median()))\n"
    "fig, axes = plt.subplots(1, 2)\n"
    "df.make.value_counts().head(10).plot.barh(ax=axes[0], title='make (naive title split)')\n"
    "df.location_state.value_counts().head(6).plot.barh(ax=axes[1], title='state')\n"
    "for a in axes: a.invert_yaxis()\n"
    "plt.tight_layout(); plt.show()"
))

cells.append(md(
    "Note `LAND` in the make chart: makes are the second token of the title, so\n"
    "\"LAND ROVER\" splits. Fix it with a marque list if you need clean makes."
))

cells.append(md(
    "## 3. Price cuts\n\n"
    "Append-only snapshots mean a price change is a new dated row, so cuts are directly\n"
    "observable — this is the part of the dataset that works today."
))

cells.append(code(
    "multi = df[df.observed_days_seen > 1]\n"
    "cut = multi[multi.price_cut_myr > 0]\n"
    "print(f'{len(cut):,} of {len(multi):,} listings cut price ({len(cut)/len(multi):.1%}) '\n"
    "      f'over {int(cov.is_observation_day.sum())} observation days')\n"
    "print('median cut: RM {:,.0f}'.format(cut.price_cut_myr.median()))\n"
    "(cut.price_cut_myr / cut.first_price_myr * 100).plot.hist(bins=40,\n"
    "    title='first-to-last discount, % of asking price')\n"
    "plt.xlabel('% off'); plt.tight_layout(); plt.show()"
))

cells.append(md(
    "## 4. Survival — and the censoring wall\n\n"
    "`event_exited = 1` means the listing was absent for 5 consecutive observation days,\n"
    "the threshold at which absences stop reversing. A listing vanishing for one day\n"
    "usually comes back: the site reorders under the crawl. Kaplan–Meier, hand-rolled\n"
    "so there is no dependency to argue with:"
))

cells.append(code(
    "def km(duration, event):\n"
    "    t = np.sort(np.unique(duration[event == 1]))\n"
    "    s, out = 1.0, []\n"
    "    for ti in t:\n"
    "        at_risk = (duration >= ti).sum()\n"
    "        d = ((duration == ti) & (event == 1)).sum()\n"
    "        s *= 1 - d / at_risk\n"
    "        out.append((ti, s, at_risk, d))\n"
    "    return pd.DataFrame(out, columns=['t_obs_days', 'survival', 'at_risk', 'events'])\n"
    "\n"
    "curve = km(df.duration_obs_days.values, df.event_exited.values)\n"
    "print('events:', int(df.event_exited.sum()), ' censored: '\n"
    "      f'{1 - df.event_exited.mean():.1%}')\n"
    "curve"
))

cells.append(code(
    "plt.step(np.r_[0, curve.t_obs_days], np.r_[1, curve.survival], where='post')\n"
    "plt.ylim(0.9, 1.005); plt.xlabel('observed days listed'); plt.ylabel('P(still listed)')\n"
    "plt.title('Kaplan-Meier — flat because almost nothing has exited yet')\n"
    "plt.tight_layout(); plt.show()"
))

cells.append(md(
    "**The honest conclusion.** With 7 observation days and a 5-day exit rule, only a\n"
    "listing last seen on day 1 or 2 can register as exited. 99.9% of rows are\n"
    "right-censored, so the median days-on-market is not estimable — any number you\n"
    "compute from the observed exits is a survivorship artefact.\n\n"
    "What is estimable today: coverage, the asking-price distribution, and price-cut\n"
    "behaviour. Days-on-market becomes answerable as the observation window grows;\n"
    "the dataset is updated as collection continues.\n\n"
    "**If you fork this:** don't pool the two coverage eras, don't drop\n"
    "`is_observation_day = 0` rows into the duration maths, and don't read\n"
    "`event_exited = 1` as \"sold\" — a delisting can be a sale, an expiry, or a seller\n"
    "giving up."
))

nb["cells"] = cells
nbf.write(nb, "kaggle_notebook/lotclock_starter.ipynb")
print("wrote kaggle_notebook/lotclock_starter.ipynb")
