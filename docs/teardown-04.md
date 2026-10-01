# The wall was partly mine, and what is behind it is stranger

*Data collected 2026-08-09 to 2026-10-01, motortrader.com.my. Census era only:
13,589 listings across 38 observation days. Method and limits at the bottom —
read them before quoting anything here.*

[Teardown-02](teardown-02) said the exit event was not in the data: no rule for
"this listing is really gone" survived a refit, so no days-to-sell number could
be published. I promised to refit monthly. This is the refit, and it overturns
teardown-02's central number the same way teardown-02 overturned teardown-01's.

## 1. The 60% return curve was a mixing error

Teardown-02's key table said a listing absent for 5 observed days still came back
**60.2%** of the time. That curve was fitted on *every* day I had collected —
including the first three weeks, when each run only harvested about 15% of the
site. On a 15%-coverage day, almost every listing is "absent", so those days
manufacture long absences that then "come back" when coverage returns.

In August the clean full-census era was only 11 days long, too short to fit on
its own, so I fitted on everything. The method notes say eras must never be
pooled; the fitting script did it anyway, silently. It no longer can.

Census days only, the curve looks completely different:

| Absent for | Reached it | Came back | Return rate |
|---|---|---|---|
| 1 day | 17,791 | 16,974 | 95.4% |
| 3 days | 1,213 | 962 | 79.3% |
| 5 days | 275 | 71 | **25.8%** (pooled said 60.2%) |
| 6 days | 215 | 14 | 6.5% |
| **7 days** | **206** | **5** | **2.4%** |
| 8 days | 203 | 2 | 1.0% |

Single-day absences are still almost all crawl noise. But past a week, absences
stop reversing. And this time the zero beyond 8 days is not the window running
out: **103 listings have now been gone 20+ observation days, 43 of them 30+, and
none came back.**

So there is an exit rule after all: **gone = absent 7 observed days in a row**,
picked from rows with real observed returns, not from an empty tail.

## 2. Under that rule, almost nothing leaves

On 9 August the site carried **12,392** listings. Seven and a half weeks later:

| Day-one listings | |
|---|---|
| Still listed on 1 Oct | **11,759 (94.9%)** |
| Gone under the 7-day rule | **182 (1.5%)** |
| The rest | absent fewer than 7 days, undecided |

Across all 13,589 listings seen in the window, 201 are gone — **98.5% are still
censored**. New stock is just as slow: 1,197 listings appeared after day one.

That is the finding I did not expect. The problem was never that exits are hidden
in noise. It is that there are hardly any exits to find. On this site, an ad
outlasts seven and a half weeks for at least 95 out of 100 cars, and only 1.5 in
100 are clearly gone.

## 3. Two readings, and the data cannot pick between them

**Reading A: these cars really do sit for months.** Plausible for what this site
actually carries. [Teardown-03](teardown-03) matched listings against JPJ's
national registration data: Bentley has 94 listings against 23 registrations
nationwide this year; Perodua, the country's best-selling make, has 300 against
219,559. This is a Klang Valley premium and recond-import channel, and expensive
stock is plausibly slow stock.

**Reading B: sold cars stay listed.** A dealer's ad page is also a shop window.
Nothing forces a sold car's ad down, and an ad that stays up still brings
enquiries.

Listing snapshots alone cannot separate these. Both produce the same thing I
observe: ads that do not go away. What I *can* say is narrower and true:
**at least 95% of the ads live on 9 August were still up 54 calendar days
later** — and they had already been up for an unknown time before I started. That is a
statement about ads, not about sales, and I am keeping the wording that way.

## 4. Price still barely moves

| Census era, through 1 Oct | |
|---|---|
| Listings seen on 2+ days | 13,516 |
| Cut their price | **295 (2.18%)** |
| Raised their price | 20 |
| Median first cut | **RM 5,000 (2.01%)** |
| Median observed days to first cut | 7 |
| Median total discount | 2.61% |

The cut rate roughly doubled from teardown-02's 1.15%. That is not a softening
market — the window is 3.5× longer, so each ad has had more time to be cut. Same
artifact family as last time, labelled the same way.

One small signal worth watching: **listings that left cut their price 6.5% of the
time, against 2.1% for those still listed.** That is 13 cuts in 201 exits —
too few to lean on, but it points the way you would expect if a cut is the last
move before a car goes.

## 5. What this changes

- **Exit rule: N = 7 observed days**, census era only. Teardown-02's "no N exists"
  is withdrawn; it came from pooled data. `exit_rule.py` now refuses to pool.
- **Still no days-to-sell number.** 201 events with 98.5% censoring supports a
  lower bound, not a median. The honest statement is the one in section 3.
- **Sale vs removal is still unlabelled.** Even a clean exit rule measures the ad
  coming down, not the car being sold. A labelled exit (a sold badge on the
  detail page) is still the only thing that turns this into days-to-sell.
- **The Kaggle column `absent_ge_5_obs_days` is now the too-loose rule** (25.8% of
  5-day absences reverse). It gets replaced on the next dataset version.
- **The collector keeps running.** This is the second published number a refit has
  overturned. Monthly refits stay.

## Method, and everything wrong with it

- **Source.** Public listing pages on motortrader.com.my, one pass per day.
  robots.txt `Crawl-delay: 5` honoured, crawler identified with a contact URL, no
  proxy rotation. mudah.my, carbase and wapcar excluded — their terms or signals
  don't permit this.
- **Census era only.** Every figure here uses days from 2026-08-09 that cleared
  10,000 rows. Killed walks and the 2026-09-11..13 database outage are missing
  days, not absences: 38 observation days across 54 calendar days.
- **Observed days, never calendar days**, except where "54 calendar days" is said
  explicitly.
- **The exit rule is bounded.** No closed absence longer than 8 observed days
  exists yet. Beyond that the zero is backed by up to 30+ days of exposure, which
  is evidence, but a listing returning after two months would still surprise this
  rule.
- **Gone is not sold.** Every "exit" is an ad that stopped appearing.
- **Prices are asking prices.** Transaction prices are not public.
- **Figures pinned to observation day 2026-10-01.** Re-running later returns
  different counts. Quote the date with the number.
- **JPJ figures** are teardown-03's, pinned to 2026-09-11: a make-level join reaching 99.7% of listings; registrations
  are 2026 year-to-date, new and used together, so the ratio says *what kind of
  stock this site carries*, not market share.

---
*Numbers reproducible with `exit_rule.py` and `price_moves.py --census` against
the project database (both self-check with `--test`, no network), and
`jpj_join.py` for the JPJ figures.*
