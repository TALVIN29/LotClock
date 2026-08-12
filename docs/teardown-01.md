# What three weeks of Malaysian used-car listings actually show

*Data collected 2026-07-19 to 2026-08-08. 2,315 listings, 16 observed days,
motortrader.com.my. Method and limits at the bottom — read them before quoting
anything here.*

Ask how long a used car takes to sell in Malaysia and you get opinions. Dealers
say "two weeks if it's priced right." Forums say a month. Nobody publishes a
number, because nobody is watching the listings day by day.

I started watching. Here is the first honest look — including the part where the
obvious answer turns out to be wrong.

## 1. Almost nobody moves their price

Of 2,288 listings observed on more than one day, **150 cut their price — 6.6%.**
In the same window, **5 listings raised** their asking price. Five, out of
two-thousand-plus.

That is the finding that surprised me most. The folk model of a used-car lot is
constant haggling and shifting stickers. In the visible listing data, the
sticker barely moves. Whatever negotiation happens, happens off-page: the listed
price is a conversation opener that stays put while the conversation happens
somewhere I can't see.

## 2. When the price does move, it moves a little, and late

For the listings that did cut:

| | |
|---|---|
| Median first cut | **RM 4,000** |
| Median first cut, as % of ask | **2.07%** |
| Median observed days before the first cut | **7** |
| Median total discount across the window | **2.21%** |

A 2% haircut after a week of silence. Not a fire sale — a nudge. And the total
discount barely exceeds the first cut, meaning most cutters cut once and then
wait rather than walking the price down in steps.

RM 4,000 sounds like a lot until you see it next to the percentage. These are
mostly cars in the tens of thousands, so the seller is conceding about one
month's payment to restart the clock.

## 3. The part everyone gets wrong: days-to-sell

Here is the number I *could* have published, and why I'm not going to.

Apply a reasonable exit rule — a listing counts as gone once it's been absent
from the site for 5 consecutive observed days — and you get:

- **68 listings exited**
- **2,247 still listed at the end of the window**
- **median days-on-market of the ones that exited: 5 days**

"Malaysian used cars sell in 5 days." It's a great headline. It is also
**wrong**, and the reason is sitting right there in the second row.

**97.1% of the listings never exited during my window.** They were still sitting
there when I stopped looking. Their true days-on-market is *unknown* — I only
know it's longer than the time I watched them. In survival analysis this is
called **right-censoring**, and it is the single most common way a "how long does
X take" statistic gets fabricated.

The 5-day median describes only the 2.9% that left fastest. Cars that sell
quickly exit the sample quickly; cars that rot on the lot stay in the sample
forever, uncounted. Averaging what you can see and calling it the answer means
measuring the fast movers and quietly discarding every slow one. The real median
is longer — possibly much longer — and three weeks of data cannot tell you how
much longer.

This is the whole reason the project exists. Getting a defensible days-to-sell
number requires a **survival model** that treats the 2,247 unfinished listings as
information rather than missing data, and it requires more calendar time than I
have yet. That is the next build, not this article.

## Method, and everything wrong with it

Honesty about limits is the point, so:

- **Source.** Public listing pages on motortrader.com.my, one pass per day.
  robots.txt sets `Crawl-delay: 5` with an empty `Disallow`; I honour the 5
  seconds and identify the crawler with a contact URL. No proxy rotation, no
  evasion. mudah.my is excluded — its terms don't permit this.
- **Append-only.** A price change is a new dated row, never an update. Nothing
  is overwritten, so the history stays reconstructable.
- **Sample size is small.** 2,315 listings over 16 days. Every number here is a
  first look, not an estimate to plan against.
- **The window has gaps.** Five days were missed (07-24, 08-01 to 08-03, 08-06)
  — a single collector machine that was off or interrupted. "Observed days" above
  counts real collection days, never calendar days, and the exit rule counts
  *observed* absences so a gap can't fake a disappearance.
- **Coverage changed, and the eras are not pooled.** Every day through 08-08
  harvested roughly 15% of the site because the crawl hit a cap. From 08-09 the
  run is a full census (~12,400 listings/day). That is a discontinuity, not
  growth, so this article deliberately stops at 08-08 and uses the partial-harvest
  era only. Mixing the two would manufacture thousands of fake "new listings" on
  one day and fake disappearances around it.
- **Disappearing is not selling.** A listing can vanish because the car sold,
  because the ad expired, or because the dealer relisted it. I cannot tell these
  apart from outside. The 5-day exit rule was fitted, not guessed — at 5 days,
  11.7% of absences still came back, which is the error rate baked into the 68.
- **Prices are asking prices.** Transaction prices are not public. Nothing here
  says what anyone actually paid.

## What's next

More days. The censoring problem shrinks with calendar time and with nothing
else, so the collector keeps running while I build the survival model that can
use the unfinished listings properly. When there's enough history for a curve
worth trusting, that becomes the second teardown — and the dataset goes public
so anyone can check the arithmetic.

---
*Numbers reproducible with `price_moves.py` against the project database;
`python price_moves.py --test` self-checks the logic on synthetic data with no
network.*
