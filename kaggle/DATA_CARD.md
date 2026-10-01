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
| `absent_ge_7_obs_days` | 1 if not seen for 7 consecutive observation days: **the ad is gone, not "sold"**. Replaces `absent_ge_5_obs_days` from the 2026-10-01 version, see below |
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
  Pooling them is exactly what produced the withdrawn 60.2% figure below.
- **Duration is in observed days, not calendar days.** Collection has gaps.
- **`absent_ge_7_obs_days` means the ad is gone, not that the car sold.** The
  census-only refit (2026-10-01) found **2.4% of 7-day absences come back**, and
  103 listings gone 20+ observation days with zero returns, so 7 days is a
  defensible "ad removed" rule. Earlier versions shipped `absent_ge_5_obs_days`
  (before that `event_exited`) with a 60.2% return rate — that rate came from
  pooling partial-harvest days and is withdrawn; census-only, 5 days reverses 25.8%.
- **Survival here is ad lifetime, not days-to-sell.** Removal still mixes
  expiries, relists and sales, unlabelled. And 98.5% of listings are censored
  (only ~1.5% of the 2026-08-09 stock was gone by 2026-10-01), so expect a lower
  bound, not a median. Split RECOND / USED before fitting. Full argument:
  <https://lotclock.netlify.app>
- **Coverage is not perfectly stable even within the census era**: 95% of
  single-day absences reverse (the site reorders under the crawl). That is why
  the threshold is 7 days, not 1.

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
Days-to-sell does not become answerable with time: that needs a labelled sale.

Source code: <https://github.com/talvin29/LotClock> · write-ups:
<https://lotclock.netlify.app>
