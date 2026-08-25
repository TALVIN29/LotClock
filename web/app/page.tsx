import ReturnCurve from "@/components/ReturnCurve";

export default function Home() {
  return (
    <main>
      <div className="wrap">
        {/* HERO */}
        <section style={{ borderTop: "none" }}>
          <div className="eyebrow">LotClock · Malaysian used cars</div>
          <h1>The listings will not tell you how long a car takes to sell</h1>
          <p className="lead">
            I scraped every used-car listing on motortrader.com.my once a day for five
            weeks to measure liquidity — days-to-sell, price cuts. The days-to-sell
            number is not in the data, and more data made that worse, not better. This
            is the write-up of why.
          </p>
          <div className="grid cols-3" style={{ marginTop: 24 }}>
            <div className="card metric">
              <span className="big">13,172</span>
              <span className="label">listings, census era</span>
            </div>
            <div className="card metric">
              <span className="big">11</span>
              <span className="label">observation days that count</span>
            </div>
            <div className="card metric">
              <span className="big">100.0%</span>
              <span className="label">censored under the fitted exit rule</span>
            </div>
          </div>
          <p className="caption">
            Data 2026-07-19 to 2026-08-24. Figures below are pinned to observation day
            2026-08-23 — the collector keeps running, so quote the date with the number.
          </p>
        </section>

        {/* 1 */}
        <section>
          <h2>1. More data made the exit signal weaker</h2>
          <p>
            A listing vanishing does not mean the car sold. It might have sold, the ad
            might have expired, the crawl might have missed it. The first teardown
            handled that with a rule: a listing is gone once it has been absent for N
            consecutive observed days, N chosen so absences that long almost never
            reverse. On three weeks of data N came out at <strong>5 days</strong>, at an
            estimated 11.7% reversal rate.
          </p>
          <p>
            Refit on everything I now have, the 5-day reversal rate is{" "}
            <strong>60.2%</strong>. The old threshold was not conservative, it was wrong
            — and wrong in the direction that flatters the project, because a loose exit
            rule manufactures exits and lets you publish a days-to-sell number.
          </p>
          <div className="card chart-box">
            <ReturnCurve />
            <p className="caption">
              Share of absences of a given length that still came back. The shaded band is
              the 5% bar an exit rule has to clear. The curve never reaches it.
            </p>
          </div>
        </section>

        {/* 2 */}
        <section>
          <h2>2. Every rule that fits is either too loose or an artifact</h2>
          <p>
            The census era — the only era where I see the whole site — is 11 observation
            days. The refit picked a 10-day absence rule. Those are nearly the same
            number, and that is fatal:
          </p>
          <div className="card table-box">
            <table>
              <thead>
                <tr><th>Exit rule</th><th>Exited</th><th>Censored</th></tr>
              </thead>
              <tbody>
                <tr><td>N = 3 (too loose)</td><td>95</td><td>99.3%</td></tr>
                <tr><td>N = 5 (teardown-01&apos;s rule)</td><td>48</td><td>99.6%</td></tr>
                <tr><td>N = 10 (the refit&apos;s pick)</td><td>1</td><td>100.0%</td></tr>
              </tbody>
            </table>
          </div>
          <p>One exit out of 13,172 listings. Not a small sample — no sample.</p>
          <p>
            <strong>And N = 10 is not defensible either.</strong> The longest absence
            anywhere in the data observed to <em>close</em> is 9 days; past that every
            remaining absence is still open, so it cannot come back inside the window. Its
            0.0% is the window ending, not listings staying gone — the same trap that
            produced N = 6 a month earlier. <code>exit_rule.py</code> now refuses to pick a
            threshold from a row with zero observed returns, so it cannot be published a
            third time.
          </p>
        </section>

        {/* 3 */}
        <section>
          <h2>3. Price barely moves — but be careful what you conclude</h2>
          <div className="card table-box">
            <table>
              <tbody>
                <tr><td>Cut their price</td><td><strong>151 (1.15%)</strong></td></tr>
                <tr><td>Raised their price</td><td>7</td></tr>
                <tr><td>Median first cut</td><td><strong>RM 5,000 (1.88%)</strong></td></tr>
                <tr><td>Median observed days to first cut</td><td>6</td></tr>
              </tbody>
            </table>
            <p className="caption">
              Census era, 13,108 listings seen on more than one day.
            </p>
          </div>
          <p>
            Teardown-01 reported a 6.6% cut rate; this says 1.15%.{" "}
            <strong>That is a sampling artifact, not sellers turning stubborn.</strong> The
            old 15% partial harvest could only show me a listing twice if it hung around
            long enough to be caught twice, so it oversampled long-lived listings — exactly
            the ones with time to cut.
          </p>
          <p>
            The claim that survives both eras: <strong>the sticker price is close to
            inert.</strong> Roughly 20 cutters per raiser, about 2% off, arriving in week
            one. Whatever negotiation happens in this market does not happen on the
            listing.
          </p>
        </section>

        {/* 4 */}
        <section>
          <h2>4. What is actually broken</h2>
          <p>
            The premise was that daily snapshots make liquidity observable. Half of that is
            wrong, and it is worth being precise about which half.
          </p>
          <div className="grid cols-2">
            <div className="card">
              <span className="tag">Listings do measure</span>
              <p>
                Inventory, asking prices, price-change behaviour, how long an <em>ad</em>{" "}
                stays up. All real, all unpublished for this market.
              </p>
            </div>
            <div className="card">
              <span className="tag">Listings cannot measure</span>
              <p>
                When a car sold. What I observe is listing <em>removal</em>, dominated by
                expiries, relists and crawl misses, with sales somewhere inside it,
                unlabelled.
              </p>
            </div>
          </div>
          <p>
            No amount of extra calendar time separates them — time adds more of the same
            ambiguous signal. Extrapolated, a 50%-uncensored sample lands around{" "}
            <strong>April 2027</strong>, and would still be half housekeeping. Waiting was
            the wrong plan.
          </p>
        </section>

        {/* 5 */}
        <section>
          <h2>5. What this changes</h2>
          <ul>
            <li>
              <strong>The survival model is deferred, not cancelled.</strong> It needs a
              labelled exit event, not a longer window. Built on listing-removal it would
              produce a confident curve describing ad expiry policy.
            </li>
            <li>
              <strong>The product is retargeted</strong> at what the data supports —
              inventory, asking-price behaviour, time-on-site for the ad — each named as
              what it is, never as &ldquo;days to sell&rdquo;.
            </li>
            <li>
              <strong>The collector keeps running.</strong> It costs nothing, the dataset is
              the asset, and the exit rule is refit monthly. This article exists because a
              refit overturned a published number.
            </li>
            <li>
              <strong>The unlock is a labelled exit</strong> — a sold badge or status field
              on the detail page. Different scrape surface, its own privacy obligations. A
              decision, not a formality.
            </li>
          </ul>
        </section>

        {/* METHOD */}
        <section>
          <h2>Method, and everything wrong with it</h2>
          <ul>
            <li>
              <strong>Source.</strong> Public listing pages on motortrader.com.my, one pass
              per day. robots.txt sets <code>Crawl-delay: 5</code> with an empty Disallow; I
              honour the 5 seconds and identify the crawler with a contact URL. No proxy
              rotation, no evasion. mudah.my, carbase and wapcar are excluded — their terms
              or signals don&apos;t permit this.
            </li>
            <li>
              <strong>Append-only.</strong> A price change is a new dated row, never an
              update.
            </li>
            <li>
              <strong>Eras are not pooled.</strong> Every day to 2026-08-08 is a ~15% partial
              harvest; 2026-08-09 onward is a full census. All figures above are census era.
            </li>
            <li>
              <strong>Killed walks are excluded.</strong> Three census runs were killed
              mid-crawl and would fake a mass disappearance. A day counts only if it cleared
              10,000 rows — leaving 11 observation days, not 16 calendar days.
            </li>
            <li>
              <strong>Observed days, never calendar days.</strong> A listing cannot be seen
              on a day nobody looked.
            </li>
            <li>
              <strong>The small event count is the point.</strong> With no defensible exit
              rule, no median, no curve and no model is estimable here. Nothing above should
              be read as an estimate of how long Malaysian used cars take to sell.
            </li>
            <li>
              <strong>Prices are asking prices.</strong> Transaction prices are not public.
            </li>
            <li>
              <strong>The exit-rule fit is bounded by its own window.</strong> Any row
              showing 0 returns is the window ending, not evidence.
            </li>
          </ul>
        </section>

        <footer>
          <p>
            Numbers reproducible with <code>exit_rule.py</code> and{" "}
            <code>price_moves.py --census</code>; both self-check on synthetic data with{" "}
            <code>--test</code> and no network.{" "}
            <a href="https://github.com/TALVIN29/LotClock">Code on GitHub</a> ·{" "}
            <a href="https://www.kaggle.com/datasets/talvinlee/malaysian-used-car-listings-daily-snapshots">
              Daily snapshots on Kaggle
            </a>{" "}
            · <a href="/price-model">Earlier price-model demo</a>
          </p>
        </footer>
      </div>
    </main>
  );
}
