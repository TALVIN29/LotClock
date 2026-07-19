# LotClock — Progress

**Status:** phase 1 — **collecting.** 2,016 rows in Supabase, task scheduled daily.
**Repo:** https://github.com/TALVIN29/LotClock (public, `main` is default)
**Data collection started: 2026-07-19** ← day 0 of the only asset that compounds
**Hours spent:** ~5 / 18
**Last session:** 2026-07-19 — Supabase live, 2,016 rows collected and verified,
scheduled task registered and test-fired, idempotency bug found and fixed.
GitHub Actions remains blocked by Cloudflare (see blocker below).

**Next action (start here):**
1. **Tomorrow after 10am, run the gate query.** A price that moved is the entire
   thesis — nothing downstream exists without it:
   ```sql
   select listing_id, min(price_myr) lo, max(price_myr) hi, count(*) snaps
   from listing_snapshot group by 1 having min(price_myr) <> max(price_myr);
   ```
   Also confirm two distinct dates exist:
   ```sql
   select scraped_at, count(*) from listing_snapshot group by 1 order by 1;
   ```
   Then check healthchecks.io went green off the 10:00 run — that is the
   dead-man's switch doing its actual job for the first time.
2. Email motortrader.com.my requesting Cloudflare allowlisting (draft in chat
   2026-07-19) — best 10 minutes available; unblocks genuinely unattended runs
3. Optional: Oracle always-free VM. **Test with one curl before configuring
   anything** — Oracle is also a datacenter ASN and may get the same 403:
   ```
   curl -s -o /dev/null -w "%{http_code}\n" -A "LotClock/0.1 (+https://github.com/TALVIN29/LotClock)" "https://www.motortrader.com.my/car/index?page=1"
   ```

Scheduled task: `LotClock daily scrape`, daily 10:00 MYT, wakes from sleep,
catches up missed runs. Logs to `logs/scrape.log`.

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
  - [x] Windows scheduled task registered, verified running
  - [ ] Second day's run — proves the time series ← NEXT
  - [ ] 7 days of collection
- [ ] 2. Spec join table + government data (JPJ, fuel, OPR)
- [ ] 3. Entity resolution + credibility scorer
- [ ] 4. Model v0
- [ ] 5. Site, two routes
- [ ] 6. Ship — Vercel, screenshot, README

## Phase 1 exit gates

- [ ] Runs 7 consecutive days unattended, zero manual intervention
- [x] ≥2,000 unique listings captured — 2,016 on day 0
- [ ] **≥1 price change captured for the same `listing_id`** ← the real gate
- [ ] ≥1 delisting captured
- [ ] Dead-man's switch verified by deliberately breaking it — **armed**
      2026-07-19 (healthchecks.io, `HEALTHCHECK_URL` set, ping test-fired
      through `ping_healthcheck()` and returned 200). Still unverified: proving
      it goes *red* requires letting one period + grace lapse with no ping.

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

## Source survey 2026-07-19 — why motortrader, and what else exists

Surveyed every Malaysian used-car site I could find. Motortrader was not a
preference; it was the only one clean on all three axes at once — permitted by
robots, reachable from a script, and server-rendering prices into HTML.

| site | robots.txt | reachable | rendering | verdict |
|---|---|---|---|---|
| **motortrader** | `Allow: /`, `Crawl-delay: 5` | 200 | server-rendered, 34/page | **in use** |
| carsome | permissive | 200 | Nuxt payload, parseable w/o browser | **best 2nd source** |
| carsifu | `Allow: /` | 200 | client-side XHR | needs Playwright |
| carousell | permissive on listings | 200 | heavy JS, 1.6MB pages | low priority |
| mytukar | `Disallow:` (empty) | redirects to carro.co | no listings in sitemap | dead end |
| carlist | permits crawling | **403** | — | Cloudflare blocks scripts |
| **mudah** | **"expressly forbidden to use spiders"** | — | — | **excluded on principle** |
| **carbase** | **`Disallow: /cars-for-sale/`** | — | — | **excluded on principle** |
| **wapcar** | `Allow: /` but **`Content-Signal: ai-train=no`** | — | — | **excluded on principle** |
| oto, carking, carvara, icarsclub | — | DNS fail / timeout | — | dead sites |

**Three exclusions are ethical, not technical** — all three are reachable. Wapcar
is the notable one: its robots.txt says `Allow: /`, so a robots-only check passes
it. The `Content-Signal: ai-train=no` header is what refuses it, and this project
trains a model on what it collects. Scraping it would be technically compliant
and substantively dishonest. Worth stating in the README.

Next source when redundancy is wanted: **carsome** — Nuxt embeds its data in the
page, so it parses with stdlib and needs no browser, consistent with the current
zero-dependency design. Not now though: one working source collecting daily beats
two half-built ones.

## Known limitations (record honestly, do not hide)

- **Mileage is banded at source** (`75k-79k`), not exact. Midpoint imputation
  only.
- Featured listings repeat on every index page (~12/page); deduped by
  `listing_id` and by the DB unique constraint.
- Single source so far. Multi-source is the resilience plan but isn't built.
- Delisted ≠ sold. Resolving that is phase 3 work.

## Blocked / open questions

- ~~Does `HEALTHCHECK_URL` need a paid healthchecks.io tier for daily?~~
  Answered 2026-07-19: free tier covers it. One check, configured and pinging.
- Full pass is ~563 pages ≈ 47 min. Start capped at 2,000 listings; decide later
  whether the full 12,954 daily is worth the load on their server.

## Collection log (append each run)

| date | rows | source | notes |
|------|------|--------|-------|
| 2026-07-19 | 216 | local PC | first verified end-to-end run; GitHub Actions 403 |
| 2026-07-19 | 2,012 | scheduled task | **2,016 total.** Price range RM 4,800 – RM 6,888,000 |

## Bug found and fixed 2026-07-19: re-runs were not idempotent

The scheduled task collected 2,006 listings then died with `HTTP 409 Conflict`
on write. `Prefer: resolution=ignore-duplicates` is not sufficient on its own —
PostgREST resolves conflicts against the **primary key**, which here is the
surrogate `id`. The constraint that matters is the composite
`(listing_id, scraped_at)`, so it must be named explicitly:
`?on_conflict=listing_id,scraped_at`.

The earlier commit claiming re-runs were idempotent was simply wrong. Verified
properly this time: re-inserting an existing row leaves the count unchanged and
returns no error.

Worth noting *why* this surfaced now rather than on day 30 — running the same
day twice is exactly what `-StartWhenAvailable` will do after a missed run.

## Bug found and fixed 2026-07-19: scheduled task pointed at the old folder path

Renaming `E:\Portfolio\price-story` to `E:\Portfolio\LotClock` broke the task.
Its registered action still read `E:\Portfolio\price-story\run_daily.cmd`, a
path that no longer exists. The 12:51 run returned `LastTaskResult = 1` and the
next run was scheduled to fail the same way.

Fixed by re-running `install_task.ps1` from the new folder — it builds the
action from `$PSScriptRoot`, so it re-registers with the correct path by
construction. Verified: the task's `Execute` now reads
`E:\Portfolio\LotClock\run_daily.cmd`.

**The failure mode matters more than the bug.** `run_daily.cmd` is what writes
`logs/scrape.log`, so a task that never starts it produces *no* log line at all
— not an error, just nothing. A missing day looks identical to a day the
scraper was never scheduled for. The only signal is the gap itself, and gaps
are exactly what a days-to-sell model has to reason about. Two guards worth
having before day 30:

- an external dead-man's switch (the already-planned `HEALTHCHECK_URL` — it
  fires on *absence* of a ping, which is precisely this case)
- a `collection_days` table, or a query over `distinct scraped_at`, so an
  observed day is a recorded fact rather than an inference from listing rows

Neither is built yet. Until one is, verify the task after any folder move:
`(Get-ScheduledTask -TaskName "LotClock daily scrape").Actions.Execute`
