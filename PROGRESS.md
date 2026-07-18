# LotClock — Progress

**Status:** in progress — phase 1 (collector)
**Data collection started:** _not yet — set this the day the Action first runs_
**Hours spent:** ~3 / 18
**Last session:** 2026-07-19 — recon + scraper built and passing against live site
**Next action:** create the Supabase project, run `schema.sql`, add the two repo
secrets, then trigger `daily-scrape` manually once

> `Next action` is the anti-abandonment field. Update it at the **end** of every
> session, never the start. Future-you reads this first.

## Phases

- [x] 0. `PROGRESS.md`
- [ ] 1. Collector on cloud cron  ← **current**
  - [x] Recon: source selection, robots.txt, rendering check
  - [x] Parser + 5 tests passing on a real saved page
  - [x] Fetcher (5s crawl-delay, honest UA, retry/backoff)
  - [x] Supabase writer (append-only, idempotent)
  - [x] GitHub Actions workflow + dead-man's switch wiring
  - [ ] Supabase project created, `schema.sql` run
  - [ ] Repo secrets set, first manual run green
  - [ ] **7 consecutive unattended days**
- [ ] 2. Spec join table + government data (JPJ, fuel, OPR)
- [ ] 3. Entity resolution + credibility scorer
- [ ] 4. Model v0
- [ ] 5. Site, two routes
- [ ] 6. Ship — Vercel, screenshot, README

## Phase 1 exit gates

- [ ] Runs 7 consecutive days unattended, zero manual intervention
- [ ] ≥2,000 unique listings captured
- [ ] **≥1 price change captured for the same `listing_id`** ← the real gate
- [ ] ≥1 delisting captured
- [ ] Dead-man's switch verified by deliberately breaking it

## Collection log

| date | rows scraped | new listings | delisted | status |
|------|--------------|--------------|----------|--------|

## Decisions made (and why)

- 2026-07-19: **Source = motortrader.com.my**, not Carlist or Mudah.
  Carlist returns 403 to datacenter IPs (so GitHub Actions would fail too);
  Mudah's robots.txt *expressly forbids* automated access. Motortrader's
  robots.txt has an empty `Disallow`, `Allow: /`, and `Crawl-delay: 5` — an
  explicit permission with a stated rate.
- 2026-07-19: **No Scrapy.** This is ~560 sequential GETs, not a concurrent
  crawl needing pipelines. stdlib `urllib` does it with nothing to maintain.
- 2026-07-19: **No supabase-py.** PostgREST takes a plain POST; a dependency
  wrapping `urllib` isn't worth it. Scraper has zero runtime dependencies.
- 2026-07-19: **No n8n.** It needs a machine left on, which defeats the whole
  constraint. GitHub Actions emails on failure natively; healthchecks.io covers
  the "workflow never fired at all" case that nothing else catches.
- 2026-07-19: **Scrape the index pages, not individual listings.** 34 listings
  per request instead of one, and the sitemap turned out to be full of expired
  listings anyway.
- 2026-07-19: **Price and monthly installment parsed by separate patterns.**
  Every card shows both (`RM 170,888` and `RM 2,304 / month`); confusing them is
  the classic bait-price bug. A test asserts they never cross.

## Known limitations (record honestly, do not hide)

- **Mileage is banded at source** (`75k-79k`), not exact. Midpoint imputation
  only.
- Featured listings repeat on every index page (~12/page); deduped by
  `listing_id` and by the DB unique constraint.
- Single source so far. Multi-source is the resilience plan but isn't built.
- Delisted ≠ sold. Resolving that is phase 3 work.

## Blocked / open questions

- Does `HEALTHCHECK_URL` need a paid healthchecks.io tier for daily? (free tier
  should cover one check — verify)
- Full pass is ~563 pages ≈ 47 min. Start capped at 2,000 listings; decide later
  whether the full 12,954 daily is worth the load on their server.
