# The listings will not tell you how long a car takes to sell

*Data collected 2026-07-19 to 2026-08-24, motortrader.com.my. Census era only:
13,172 listings across 11 observation days. Method and limits at the bottom —
read them before quoting anything here.*

[The first teardown](teardown-01) ended with a promise: keep collecting, and the
censoring problem shrinks with calendar time. Five weeks later I have six times
the listings and a full census instead of a 15% sample.

The censoring problem did not shrink. It got worse. This article is about why
that happened, and why it is a finding rather than a failure.

## 1. More data made the exit signal weaker, not stronger

The core problem has always been that a listing vanishing from the site does not
mean the car sold. It might have sold; the ad might have expired; the crawl might
simply have missed it. Teardown-01 handled this by fitting a rule: a listing is
gone once it has been absent for N consecutive observed days, with N chosen so
that absences that long almost never reverse.

On three weeks of data, N came out at **5 days** — at which point 11.7% of
absences still came back.

Refitting on everything I now have, here is how often an absence of a given
length still reverses:

| Absent for | Still came back |
|---|---|
| 1 day | **97.3%** |
| 2 days | 93.2% |
| 3 days | 85.6% |
| 4 days | 72.5% |
| 5 days | **60.2%** |
| 7 days | 47.8% |
| 9 days | 34.8% |

Read the 5-day row again. Teardown-01 estimated an 11.7% reversal rate there.
With more data it is **60.2%**. The old threshold was not conservative, it was
wrong — and it was wrong in the direction that flatters the project, because a
loose exit rule manufactures exits and lets you publish a days-to-sell number.

Refitting picked **10 observed days**, at an apparent 0.0% reversal. That number
is not real either, and section 2 is where it falls apart.

## 2. Every rule that fits is either too loose or an artifact

Here is where it stops being a data problem and starts being a structural one.

The census era — the only era where I see the whole site — is 11 observation
days long. The exit rule needs a listing to be absent for 10 of them before it
counts as gone. Those two numbers are almost the same number, and that is fatal:

| Exit rule | Exited | Censored |
|---|---|---|
| N = 3 (too loose) | 95 | 99.3% |
| N = 5 (teardown-01's rule) | 48 | 99.6% |
| N = 10 (the refit's pick) | 1 | 100.0% |

The refit's own rule yields **one** exit out of 13,172 listings. Not a small
sample — no sample.

**And N = 10 is not defensible either.** It is the same artifact one rung up. The
longest absence anywhere in the data that is observed to *close* is 9 observed
days; past that, every remaining absence is still open, so it cannot come back
inside the window:

| Absent for | Reached it | Came back | Return rate |
|---|---|---|---|
| 8 days | 73 | 28 | 38.4% |
| 9 days | 69 | 24 | 34.8% |
| **10 days** | **41** | **0** | **0.0% — by construction** |

The 0.0% is the window ending, not listings staying gone. Teardown-01's notes
already caught this once and rejected N=6 for reading "0% but window-limited";
the refit walked into it again at N=10. The real curve is 60.2% → 52.6% → 47.8%
→ 38.4% → 34.8%, still falling gently where the data runs out. **No N clears the
5% bar on evidence at all** — and `exit_rule.py` now refuses to pick one from a
row with zero observed returns, so this cannot be published a third time.

The 41 exits also pool both coverage eras, which this project's own method notes
forbid. Inside the clean era the count is 1.

## 3. Price barely moves either, but be careful what you conclude

Census era, 13,108 listings seen on more than one day:

| | |
|---|---|
| Cut their price | **151 (1.15%)** |
| Raised their price | 7 |
| Median first cut | **RM 5,000 (1.88%)** |
| Median observed days to first cut | 6 |
| Median total discount | 1.88% |

Teardown-01 reported a 6.6% cut rate. This one says 1.15%. **That is not sellers
becoming more stubborn — it is a sampling artifact, and I would be lying if I let
it stand as a trend.** The old 15% partial harvest could only show me a listing
twice if it hung around long enough to be caught twice, so it oversampled
long-lived listings, which are exactly the ones with time to cut. The census sees
every ad, including thousands that are days old and have not considered cutting
anything yet.

The one claim that survives both eras: **the sticker price is close to inert.**
Roughly 20 cutters for every raiser, and a cut of about 2% arriving in week one.
Whatever negotiation happens in this market, it does not happen on the listing.

## 4. So what is actually broken

The project's premise was that daily listing snapshots make liquidity
observable. That premise is half wrong, and it is worth being precise about
which half.

**What listings genuinely measure:** inventory, asking prices, price-change
behaviour, how long an *ad* stays up. All real, all unpublished for this market,
all defensible.

**What listings cannot measure:** when a car sold. The exit event I need is not
in the data. What I observe is *listing removal*, and removal is dominated by
housekeeping — expiries, relists, crawl misses — with sales somewhere inside it,
unlabelled. No amount of additional calendar time separates them, because time
adds more of the same ambiguous signal. Waiting was the wrong plan.

Extrapolating the observed exit rate, a 50%-uncensored sample arrives somewhere
around **April 2027** — and it would still be 50% housekeeping.

## 5. What this changes

I am not shipping a days-to-sell number, and I am not going to keep waiting for
one. Concretely:

- **The survival model is deferred, not cancelled.** It needs a labelled exit
  event, not a longer window. Building it on listing-removal would produce a
  confident curve describing ad expiry policy.
- **The measurable product is retargeted** at what the data does support:
  inventory levels, asking-price behaviour, and time-on-site for the ad itself —
  each named as what it is, never as "days to sell".
- **The collector keeps running.** It costs nothing, the dataset is the asset,
  and the exit rule should be refitted monthly — this article exists because a
  refit overturned a published number.
- **The one thing that would unlock the original goal** is a labelled exit: a
  sold badge or status field on the detail page. That is a different scrape
  surface with its own privacy obligations, and it is a decision, not a
  formality.

## Method, and everything wrong with it

- **Source.** Public listing pages on motortrader.com.my, one pass per day.
  robots.txt sets `Crawl-delay: 5` with an empty `Disallow`; I honour the 5
  seconds and identify the crawler with a contact URL. No proxy rotation, no
  evasion. mudah.my, carbase and wapcar are excluded — their terms or signals
  don't permit this.
- **Append-only.** A price change is a new dated row, never an update.
- **Eras are not pooled.** Every day to 2026-08-08 is a ~15% partial harvest;
  2026-08-09 onward is a full census. All section 3 and 4 figures are census era
  only. The one pooled figure (41 exits) is labelled as pooled where it appears.
- **Killed walks are excluded.** Three census runs (08-11, 08-15, 08-21) were
  killed mid-crawl and would fake a mass disappearance. A day counts as an
  observation day only if it cleared 10,000 rows. That leaves **11 observation
  days**, not 16 calendar days.
- **Observed days, never calendar days.** A listing cannot be seen on a day
  nobody looked.
- **Small event count is the whole point.** With no defensible exit rule at all —
  and 1 exit even under the rule this article rejects — no median, no curve and
  no model is estimable here. Nothing in this article should be
  read as an estimate of how long Malaysian used cars take to sell.
- **Prices are asking prices.** Transaction prices are not public.
- **Figures pinned to a window.** Sections 3 and 4 were computed through
  observation day **2026-08-23**. The collector keeps running, so re-running
  `price_moves.py --census` on a later date returns slightly different counts —
  the 2026-08-24 run alone moved 151 cutters to 154. Quote the date with the
  number.
- **The exit-rule fit is bounded by its own window.** Return rates for absences
  longer than the longest *closed* gap (9 observed days here) are not estimates;
  the denominator is entirely still-open absences. Any row showing 0 returns is
  the window ending. This is the trap that produced both N=6 and N=10.
- **Teardown-01's 5-day exit rule is superseded.** Its price-move findings stand
  for its own era; its exit-rule section is now known to be too loose.

---
*Numbers reproducible with `exit_rule.py` and `price_moves.py --census` against
the project database; both self-check on synthetic data with `--test` and no
network. Census-era figures use the observation-day filter from
`kaggle_export.py`.*
