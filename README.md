# LotClock

**Every car sitting on a dealer's lot has a clock running. Nobody can read it —
including, it turns out, me.**

A daily collector for the Malaysian used-car market, built to measure liquidity:
time on market and price cuts. It has been running since 2026-07-19. Five weeks
in, it produced a finding I did not want: **the exit event is not in the data.**
A listing disappearing means expired, relisted, missed by the crawl, or sold —
unlabelled, and more calendar time does not separate them.

So this repo publishes the wall instead of a number.

> **Status:** collector running daily, 30+ observation days. Dataset public on
> Kaggle, write-up live. Survival model **deferred, not cancelled** — it needs a
> labelled exit event, not a longer window.

**[Read the write-up →](https://lotclock.netlify.app)** ·
**[Daily snapshots on Kaggle →](https://www.kaggle.com/datasets/talvinlee/malaysian-used-car-listings-daily-snapshots)** ·
**[Starter notebook →](https://www.kaggle.com/code/talvinlee/lotclock-starter-the-censoring-wall)**

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

The intended output looked like this:

```
Day  0   RM 42,800   listed
Day 23   RM 40,500   cut 5.4%
Day 51   RM 38,900   cut 4.0%
Day 68   delisted          ← is this a sale?
```

Everything above the last line is real and measurable. The last line is the
problem, and it is the whole story of this project.

## What five weeks of daily collection actually showed

Census era: 13,172 listings over 11 qualifying observation days. Figures pinned
to observation day 2026-08-23.

**The exit rule collapsed.** Call a listing gone once it has been absent for N
consecutive observed days, with N chosen so absences that long rarely reverse.
An early fit said N=5, at an estimated 11.7% reversal rate. Refit on everything:
the 5-day reversal rate is **60.2%**. The old threshold wasn't conservative, it
was wrong — in the direction that flatters the project, because a loose exit rule
manufactures exits and lets you publish a days-to-sell number.

No threshold clears a 5% bar on evidence. The return curve runs 97.3% at 1 day
down to 34.8% at 9 days and the data runs out. Any longer absence reads 0% only
because the window ended — an artifact that got published once and nearly got
published a second time. `exit_rule.py` now refuses to pick a threshold from a
row with zero observed returns.

**Prices barely move.** 151 of 13,108 listings (1.15%) cut their price; 7 raised
it. Median first cut RM 5,000 (1.88%), arriving around day 6. Roughly 20 cutters
per raiser. Whatever negotiation happens in this market does not happen on the
listing.

**What listings do measure:** inventory, asking prices, price-change behaviour,
how long an *ad* stays up. All real, all unpublished for this market.
**What they cannot measure:** when a car sold.

## Why it mattered — the invisible number

The original motivation, kept here because it is still the right question even
though this data cannot answer it.

A dealer optimises the margin they can see and ignores the cost they can't.

*"Bought at RM 47,000, sold at RM 50,000 — made RM 3,000."* On a RM 50,000 car
held 90 days, the costs that don't appear on the invoice:

| invisible cost | amount |
|---|---|
| Floor-plan interest @ 8%/yr | RM 986 |
| Depreciation @ ~1.5%/month | RM 2,250 |
| Opportunity cost — that capital couldn't buy another car | RM 3,000 |
| **Total** | **RM 6,236** |

*Worked illustration, not a measurement — the rates are assumptions (8%/yr
financing, ~1.5%/month depreciation, capital recycled once per holding period).
The point is the shape: holding cost scales with days held.*

Visible profit RM 3,000. Actual result: a **RM 3,236 loss**, booked as a win and
repeated. Independent dealers operate this way because the data to do otherwise
has never existed.

**And it still doesn't** — that is the finding. Days held is exactly the quantity
public listings cannot give you. Anyone selling a days-to-sell figure derived
from listing disappearance is selling ad-expiry policy with a confidence interval
on it.

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
the point. So collection runs on a scheduled task on my own machine, with a
second machine covering the evening slot. Gaps are **modelled as interval
censoring, not chased** — the target is that every gap is known, not that there
are none.

**Append-only is the whole design.** A price change is never an `UPDATE`; it's a
new dated row. That is the only reason anything can be measured over time.

## Data source and ethics

Collecting from **motortrader.com.my**, chosen deliberately:

| site | verdict |
|---|---|
| carlist.my | 403s datacenter IPs — a GitHub Action would be blocked anyway |
| **mudah.my** | robots.txt **expressly forbids** automated access — **excluded** |
| **carbase.my** | disallows the listings path — **excluded** |
| **wapcar.my** | sends `ai-train=no` — **excluded** |
| **motortrader.com.my** | empty `Disallow`, `Allow: /`, `Crawl-delay: 5` — **explicit permission** |

We honour the 5-second crawl delay, identify honestly with a contact URL in the
User-Agent, and read index pages (34 listings per request) rather than hammering
individual listings. No evasion, no rotation, no CAPTCHA solving. If they ever
want to block us they can see exactly who we are.

**No seller data is collected.** The parser writes a fixed field whitelist and
never reads the dealer name or phone number that appear on listing cards.

Raw listing data stays in Supabase and is **not** committed to this repo. Code
and derived aggregates only; the public dataset lives on Kaggle.

## Run it

```bash
git clone https://github.com/TALVIN29/LotClock.git
cd LotClock
pip install -r requirements.txt      # scrapling (parsing) + pytest/model extras
                                     # fetching is still stdlib urllib

python -m pytest tests -q            # 5 checks against a real saved page
python -m scraper.run --dry-run --max 80    # live parse, no writes

python exit_rule.py --test           # self-checks on synthetic data, no network
python price_moves.py --test
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
      collection runs from scheduled tasks on two machines instead
- [x] Exit-rule fit with its own artifact guard (`exit_rule.py`)
- [x] Public dataset + starter notebook on Kaggle
- [x] Public write-up of the censoring wall
- [ ] Labelled exit event from detail pages ← **the actual blocker**, and a
      decision rather than a chore: new scrape surface, new privacy obligations
- [ ] Survival model (time-to-sell, right-censored) — waiting on the line above,
      not on more calendar time
- [ ] Spec join + JPJ / fuel-price / OPR government data
- [ ] Entity resolution + listing credibility scoring

See [`PROGRESS.md`](PROGRESS.md) for the running log and every decision with its
reasoning, and [`docs/teardown-02.md`](docs/teardown-02.md) for the full write-up.

## Honest limitations

- **Delisted ≠ sold, and this is not fixable by waiting.** Removal is dominated
  by housekeeping — expiries, relists, crawl misses — with sales somewhere inside
  it, unlabelled. Extrapolated, a 50%-uncensored sample lands around April 2027
  and would still be mostly housekeeping.
- **No days-to-sell number is published here**, and any that appears elsewhere
  from this kind of data should be read as ad-expiry policy.
- **Mileage is banded at source** (`75k-79k`), never exact.
- **Listing price ≠ transaction price.** Hence measuring negotiation room rather
  than claiming to predict sale price.
- **Eras are not pooled.** Everything to 2026-08-08 is a ~15% partial harvest;
  2026-08-09 onward is a full census. The partial era oversampled long-lived
  listings, which is why its 6.6% cut rate is not comparable to the census 1.15%.
- Single source today. Multi-source resilience is designed, not implemented.
- **Collection depends on my own machines being awake.** A missed day is gone —
  daily history cannot be backfilled — so gaps are recorded and modelled rather
  than hidden.
- **Published numbers are pinned to a date.** The collector keeps running, so
  re-running the scripts later returns slightly different counts. Quote the date
  with the number.
