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
| `year`, `condition`, `transmission`, `mileage_band`, `location_state` | as listed |
| `first_price_myr`, `last_price_myr` | first and last asking price observed, MYR |
| `price_cut_myr` | first minus last, 0 if never cut |
| `observed_days_seen` | number of observation days the listing appeared on |
| `duration_obs_days` | first-to-last sighting, inclusive, in **observed** days |
| `event_exited` | 1 if absent for 5 consecutive observation days |
| `listed_before_census` | 1 if already present in the partial era (left-truncated) |

## How to use it honestly

- **Do not pool the coverage eras.** Pre-2026-08-09 harvested ~15% of the site.
- **Duration is in observed days, not calendar days.** Collection has gaps.
- **`event_exited` is not "sold".** A delisting can be a sale, an expiry, or a
  seller giving up. No sale price is ever visible.
- **Right-censoring is severe today** — 99.9% at the current window length, so the
  median days-on-market is *not* estimable yet. Reporting the median of observed
  exits is survivorship bias. See the starter notebook.
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
