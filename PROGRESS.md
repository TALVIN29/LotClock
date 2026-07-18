# LotClock — Progress

**Status:** phase 1 — **collecting.** First 216 rows landed in Supabase.
**Repo:** https://github.com/TALVIN29/LotClock (public, `main` is default)
**Data collection started: 2026-07-19** ← day 0 of the only asset that compounds
**Hours spent:** ~4 / 18
**Last session:** 2026-07-19 — Supabase live, first end-to-end run verified,
GitHub Actions found blocked by Cloudflare (see blocker below)

**Next action (start here):**
1. Register the Windows scheduled task (command in `SETUP.md` §7) so collection
   runs daily without being asked
2. **Tomorrow: run the gate query** — a price that moved is the whole thesis:
   ```sql
   select listing_id, min(price_myr) lo, max(price_myr) hi, count(*) snaps
   from listing_snapshot group by 1 having min(price_myr) <> max(price_myr);
   ```
3. Email motortrader.com.my requesting Cloudflare allowlisting (draft in chat
   2026-07-19) — highest-value 10 minutes available, unblocks unattended runs
4. Optional: Oracle always-free VM. **Test with one curl before configuring
   anything** — Oracle is also a datacenter ASN and may get the same 403

Full walkthrough: `SETUP.md`

> `Next action` is the anti-abandonment field. Update it at the **end** of every
> session, never the start. Future-you reads this first.

## Phases

- [x] 0. `PROGRESS.md`
- [ ] 1. Collector  ← **current**
  - [x] Recon: source selection, robots.txt, rendering check
  - [x] Parser + 5 tests passing on a real saved page
  - [x] Fetcher (5s crawl-delay, honest UA, retry/backoff)
  - [x] Supabase writer (append-only, idempotent)
  - [x] GitHub Actions workflow — **built, but 403'd by Cloudflare**
  - [x] Supabase project created, `schema.sql` run
  - [x] Repo secrets set
  - [x] **First run verified end-to-end — 216 rows in the database**
  - [ ] Windows scheduled task registered
  - [ ] Second day's run — proves the time series
  - [ ] 7 days of collection
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

## ⚠️ Blocker found 2026-07-18: motortrader 403s GitHub Actions IPs

First real workflow run failed: `HTTP 403` on every page, run
[29654172225](https://github.com/TALVIN29/LotClock/actions/runs/29654172225).

Diagnosed as purely IP-range based — identical code, user-agent and timing
returned `200` from a non-cloud IP and `403` from the GitHub runner in the same
minute. GitHub Actions runs on Azure ranges that most WAFs block wholesale.
Their robots.txt still permits crawling at `Crawl-delay: 5`; it is the edge
infrastructure blocking cloud IPs generically, not a policy against us.

**Not doing:** proxy rotation, IP spoofing, CAPTCHA solving. Honouring robots.txt
while routing around the WAF that enforces it would defeat the point of the
project.

**The failure handling worked** — loud exit 1, `under_threshold` logged, no
silent green run over an empty database. That part of the design is validated.

Options under consideration (see chat 2026-07-18):
- A. Windows Task Scheduler on the builder's PC — works today, gaps when off
- B. Oracle Cloud always-free VM — genuinely unattended, non-Azure IP
- C. Email motortrader.com.my requesting access for a student research project
- D. Switch source again — weak: carlist blocks harder, mudah forbids outright

This is Porter's "supplier power: VERY HIGH" materialising on day one, exactly as
predicted. Worth writing up in the README as a finding rather than hiding.

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

## Collection log (append each run)

| date | rows | source | notes |
|------|------|--------|-------|
| 2026-07-19 | 216 | local PC | first verified end-to-end run; GitHub Actions 403 |
