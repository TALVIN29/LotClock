# LotClock — Malaysian used-car listings, daily snapshots

**What it is.** Daily snapshots of a Malaysian used-car listing index
(motortrader.com.my), collected since 2026-07-19 and still running. Append-only:
a price change is a new dated row, never an overwrite. That is what makes price
cuts and delistings measurable at all.

**Why it exists.** Malaysian used-car *listing dynamics* — how long cars sit, how
much sellers cut — are not published anywhere. Asking prices are everywhere; what
happens to a listing over time is not.

## Files

### `lotclock_daily_coverage.csv` — read this first
One row per collection day.

| column | meaning |
|---|---|
| `date` | collection date |
| `listings_seen` | rows harvested that day |
| `coverage_era` | `partial_15pct` before 2026-08-09, `full_census` from then on |
| `is_observation_day` | 1 only if it is a census day that completed (≥10,000 rows) |

A listing being absent only means something on a day the site was actually walked
properly. Days flagged 0 are page-capped crawls or runs killed mid-walk — treating
them as light days invents mass disappearances.

### `lotclock_listings.csv`
One row per listing observed on a full-census **observation day**.

| column | meaning |
|---|---|
| `listing_id` | stable site id |
| `make`, `model` | first two tokens after the year in the title (see caveats) |
| `year`, `condition`, `mileage_band`, `location_state` | as listed |
| `is_automatic` | 1 if the card carried an AUTO badge, 0 if it carried none. **Not a gearbox label** — see below |
| `first_price_myr`, `last_price_myr` | first and last asking price observed, MYR |
| `price_cut_myr` | first minus last, 0 if never cut |
| `observed_days_seen` | number of observation days the listing appeared on |
| `duration_obs_days` | first-to-last sighting, inclusive, in **observed** days |
| `absent_ge_5_obs_days` | 1 if not seen for 5 consecutive observation days. **An absence, not an exit** — renamed from `event_exited` in the 2026-08-25 version, see below |
| `listed_before_census` | 1 if already present in the partial era (left-truncated) |

## How to use it honestly

- **`is_automatic` is a badge, not a gearbox.** Motortrader prints `AUTO` on
  automatic listings and prints nothing at all on the rest. Across 12,595 rows on
  2026-09-10 the field held `AUTO` 12,035 times and null 560 times — `MANUAL` never
  once, though the parser has always accepted it. So the old `transmission` column
  was a constant plus a hole, and the routine fix for a hole (fill with the mode)
  would have stamped AUTO onto every non-automatic car in the set.
  Absence leans manual without proving it: 19.3% of null-badge rows say
  MANUAL / MT / x-SPEED in their own title versus 1.65% of AUTO-badged rows, a 12x
  lift — but their other fields are sparser too (mileage present 81.6% vs 99.3%),
  so some absences are thin cards rather than manual cars. Treat `is_automatic = 0`
  as "the site did not claim automatic", nothing stronger.

- **This is a Klang Valley dataset, not a national one.** Kuala Lumpur is 67.0% of
  rows and Selangor 31.6% — 98.6% between them. Nine states appear at all, out of
  16; Penang is 7 listings, Kedah 3. Any state-level comparison outside KL/Selangor
  is built on dozens of rows, and nothing here supports a claim about Malaysia.

- **Two populations share the `condition` column.** RECOND is 52.5% of rows, USED
  46.1%, NEW 1.3%. Recond units are importer stock and turn over on a different
  clock than owner-sold used cars; a single survival curve over the pool describes
  neither. Split before fitting.


- **Do not pool the coverage eras.** Pre-2026-08-09 harvested ~15% of the site.
- **Duration is in observed days, not calendar days.** Collection has gaps.
- **`absent_ge_5_obs_days` is not an event, and not "sold".** This column was
  called `event_exited` in earlier versions and that name was wrong. Refitting
  the exit rule on the full window found that **60.2% of 5-day absences still
  come back**, and that no absence threshold clears a 5% reversal bar on the
  evidence available. Treat this column as "was not seen for a while" and
  nothing more.
- **Do not fit a survival model on this dataset.** The exit event is not in the
  data: listing removal is dominated by expiries, relists and crawl misses, with
  sales unlabelled inside it. More collection days do not separate them — this
  is a structural limit, not a sample-size problem. Full argument:
  <https://lotclock.netlify.app>
- **Coverage is not perfectly stable even within the census era**: 81% of
  single-day absences reverse the next day (the site reorders under the crawl).
  That is why the exit threshold is 5 days, not 1.

## Known caveats

- **Make is a naive title split**, so "LAND ROVER" becomes make `LAND`, model
  `ROVER`. Apply a marque list if you need clean makes.
- **The sample is not the Malaysian market.** It is one dealer-heavy index that
  skews premium and Klang Valley: median asking price ≈ RM 181,000, and Kuala
  Lumpur plus Selangor are ~98% of rows.
- 57 listings have no parsed price.
- `mileage_band` is a band as displayed, not an odometer reading.

## Collection ethics

robots.txt and the published crawl-delay are honoured. No proxy rotation, no IP
rotation, no evasion, no login-walled content. Only the public index is read; no
personal data of any seller is collected or published. Raw HTML is not
redistributed — this release is derived tables only.

## Updates

Collection is ongoing; the release is refreshed as the observation window grows.
The days-on-market question becomes answerable as it does.

Source code: <https://github.com/talvin29/LotClock> · first analysis writeup:
<https://talvin29.github.io/LotClock/teardown-01>
