# LotClock

**Every car sitting on a dealer's lot has a clock running. We tell you what it costs.**

A daily collector that measures something nobody in the Malaysian used-car market
publishes: **how long a car actually takes to sell, and how far its price falls
getting there.**

> Status: phase 1 of 6 — the collector. No model, no site yet, on purpose.
> Daily history cannot be backfilled, so the scraper had to come first.

---

## Why this isn't another car-price predictor

There are hundreds of used-car price models on GitHub. They all predict the same
thing from the same static CSVs.

Price is the wrong target here. In Malaysia the final number is negotiated
privately, so a listing price is an **anchor, not a transaction** — you can model
it, but you can never validate it. And Carsome already does it better with real
sale data nobody else has.

What nobody collects is **liquidity**: scrape the same listing every day and you
see the price cuts, the time on market, and the disappearance.

```
Day  0   RM 42,800   listed
Day 23   RM 40,500   cut 5.4%
Day 51   RM 38,900   cut 4.0%
Day 68   delisted
```

That listing had 9.1% of negotiation room and took 68 days. That number does not
exist anywhere in this market today.

## Why it matters — the invisible number

A dealer optimises the margin they can see and ignores the cost they can't.

*"Bought at RM 47,000, sold at RM 50,000 — made RM 3,000."* On a RM 50,000 car
held 90 days, the costs that don't appear on the invoice:

| invisible cost | amount |
|---|---|
| Floor-plan interest @ 8%/yr | RM 986 |
| Depreciation @ ~1.5%/month | RM 2,250 |
| Opportunity cost — that capital couldn't buy another car | RM 3,000 |
| **Total** | **RM 6,236** |

Visible profit RM 3,000. Actual result: a **RM 3,236 loss**, booked as a win and
repeated. Around 5,000 independent dealers — **62.5% of a USD 18.7B market** —
operate this way, because the data to do otherwise has never existed.

The metric that matters is **capital velocity, not per-unit margin.** Everything
here exists to make that one number visible.

## How it works

```
Windows Task Scheduler (daily 10:00)  →  scraper  →  Supabase Postgres (append-only)
healthchecks.io                       →  dead-man's switch
```

No server, every layer a free tier — but note the scheduler, because the
intended design was different and it's worth saying why.

The collector was built to run on **GitHub Actions**, and that workflow is in
this repo. It doesn't run. Motortrader's edge returns `403` to Azure IP ranges,
so identical code that returns `200` from a home connection is refused from a
runner. This isn't a policy against this project — their robots.txt still
permits crawling at `Crawl-delay: 5` — it's a WAF blocking datacenter ranges
generically.

The available fixes were proxy rotation or IP spoofing. Both were rejected:
honouring robots.txt while evading the infrastructure that enforces it defeats
the point. So collection runs on a scheduled task on my own machine, which is
honest but has a real cost — **gaps when the machine is off**, in a dataset
whose whole value is daily continuity. The dead-man's switch exists to make
those gaps visible instead of silent.

**Append-only is the whole design.** A price change is never an `UPDATE`; it's a
new dated row. That is the only reason anything can be measured over time.

## Data source and ethics

Collecting from **motortrader.com.my**, chosen deliberately:

| site | verdict |
|---|---|
| carlist.my | 403s datacenter IPs — a GitHub Action would be blocked anyway |
| **mudah.my** | robots.txt **expressly forbids** automated access — **excluded** |
| **motortrader.com.my** | empty `Disallow`, `Allow: /`, `Crawl-delay: 5` — **explicit permission** |

We honour the 5-second crawl delay, identify honestly with a contact URL in the
User-Agent, and read index pages (34 listings per request) rather than hammering
individual listings. No evasion, no rotation, no CAPTCHA solving. If they ever
want to block us they can see exactly who we are.

Raw listing data stays in Supabase and is **not** committed to this repo. Code
and derived aggregates only.

## Run it

```bash
git clone https://github.com/TALVIN29/LotClock.git
cd LotClock
pip install -r requirements.txt      # pytest only — the scraper is stdlib-only

python -m pytest tests -q            # 5 checks against a real saved page
python -m scraper.run --dry-run --max 80    # live parse, no writes
```

Full setup (Supabase + Actions) is in [`SETUP.md`](SETUP.md).

## What's built

- [x] Source selection with robots.txt compliance documented
- [x] Parser + 5 tests, including one asserting the asking price is never
      confused with the monthly loan installment
- [x] Polite fetcher — 5s delay, honest UA, backoff on 429/5xx
- [x] Append-only Supabase writer, idempotent on re-runs
- [x] Dead-man's switch (healthchecks.io)
- [x] Daily GitHub Action — **written, but blocked by a WAF on cloud IPs**;
      collection currently runs from a scheduled task instead
- [ ] 7 consecutive unattended days ← current gate
- [ ] Spec join + JPJ / fuel-price / OPR government data
- [ ] Entity resolution + listing credibility scoring
- [ ] Survival model (time-to-sell, right-censored)
- [ ] Public site

See [`PROGRESS.md`](PROGRESS.md) for the running log and every decision with its
reasoning.

## Honest limitations

- **Mileage is banded at source** (`75k-79k`), never exact.
- **Delisted ≠ sold.** A car may have been withdrawn. Resolving this from
  relisting behaviour is planned, not built.
- **Listing price ≠ transaction price.** Hence measuring negotiation room rather
  than claiming to predict sale price.
- Single source today. Multi-source resilience is designed, not implemented.
- **Collection depends on one machine being awake.** Running from a scheduled
  task rather than a cloud cron means a day missed is a day gone — daily
  history cannot be backfilled.
- The liquidity model needs ~90 days of collection to be meaningful. At day 30
  most cars are still unsold, so estimates will be heavily right-censored — and
  will be published saying so.
