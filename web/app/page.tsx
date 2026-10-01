import ReturnCurve from "@/components/ReturnCurve";

export default function Home() {
  return (
    <main>
      <div className="wrap">
        {/* HERO */}
        <section style={{ borderTop: "none" }}>
          <div className="eyebrow">LotClock · Malaysian used cars · teardown 04</div>
          <h1>The wall was partly mine, and what is behind it is stranger</h1>
          <p className="lead">
            Teardown 02 said the listings cannot tell you when a car is gone. I promised
            to refit monthly. The refit says that wall was mostly built by my own
            mixing of data, and that once it is removed, almost nothing on this site
            ever leaves.
          </p>
          <div className="grid cols-3" style={{ marginTop: 24 }}>
            <div className="card metric">
              <span className="big">2.4%</span>
              <span className="label">of 7-day absences come back: an exit rule exists</span>
            </div>
            <div className="card metric">
              <span className="big">94.9%</span>
              <span className="label">of 9 August ads still listed 54 days later</span>
            </div>
            <div className="card metric">
              <span className="big">1.5%</span>
              <span className="label">clearly gone under that rule</span>
            </div>
          </div>
          <p className="caption">
            13,589 listings, census era only, 38 observation days from 2026-08-09 to
            2026-10-01, motortrader.com.my. Figures pinned to 2026-10-01 — the collector
            keeps moving them, so quote the date with the number.
          </p>
        </section>

        {/* 1 */}
        <section>
          <h2>1. The 60% return curve was a mixing error</h2>
          <p>
            Teardown 02&apos;s key number: a listing absent for 5 observed days still came
            back <strong>60.2%</strong> of the time. That curve was fitted on every day I
            had collected — including the first three weeks, when each run only
            harvested about 15% of the site. On a 15%-coverage day almost every listing
            is &ldquo;absent&rdquo;, so those days manufacture long absences that then
            &ldquo;come back&rdquo; when coverage returns.
          </p>
          <p>
            In August the full-census era was only 11 days long, too short to fit on its
            own, so I fitted on everything. My own method notes say eras must never be
            pooled; the fitting script did it anyway, silently. It no longer can.
          </p>
          <div className="card chart-box">
            <ReturnCurve withCensus />
            <p className="caption">
              Share of absences that still came back, by length. Dashed grey: pooled fit
              published in teardown 02 (withdrawn). Blue: census days only. Shaded band:
              under 5%. The census line stops at 8 days, the longest absence ever
              observed to close.
            </p>
          </div>
          <div className="card table-box">
            <table>
              <thead>
                <tr><th>Absent for</th><th>Reached it</th><th>Came back</th><th>Return rate</th></tr>
              </thead>
              <tbody>
                <tr><td>1 day</td><td>17,791</td><td>16,974</td><td>95.4%</td></tr>
                <tr><td>3 days</td><td>1,213</td><td>962</td><td>79.3%</td></tr>
                <tr><td>5 days</td><td>275</td><td>71</td><td>25.8% (pooled: 60.2%)</td></tr>
                <tr><td>6 days</td><td>215</td><td>14</td><td>6.5%</td></tr>
                <tr><td><strong>7 days</strong></td><td>206</td><td>5</td><td><strong>2.4%</strong></td></tr>
                <tr><td>8 days</td><td>203</td><td>2</td><td>1.0%</td></tr>
              </tbody>
            </table>
          </div>
          <p>
            Single-day absences are still almost all crawl noise. Past a week, absences
            stop reversing — and this time the zero beyond 8 days is not the window
            running out: <strong>103 listings have been gone 20+ observation days, 43 of
            them 30+, and none came back.</strong> So there is an exit rule after all:{" "}
            <strong>gone = absent 7 observed days in a row</strong>, picked from rows with
            real observed returns, not from an empty tail.
          </p>
        </section>

        {/* 2 */}
        <section>
          <h2>2. Under that rule, almost nothing leaves</h2>
          <div className="card table-box">
            <table>
              <thead>
                <tr><th>12,392 listings live on 9 August</th><th>Count</th><th>Share</th></tr>
              </thead>
              <tbody>
                <tr><td>Still listed on 1 October</td><td>11,759</td><td>94.9%</td></tr>
                <tr><td>Gone under the 7-day rule</td><td>182</td><td>1.5%</td></tr>
                <tr><td>Absent under 7 days, undecided</td><td>451</td><td>3.6%</td></tr>
              </tbody>
            </table>
          </div>
          <p>
            Across all 13,589 listings seen in the window, 201 are gone — <strong>98.5%
            are still censored</strong>. New stock is just as slow: 1,197 listings
            appeared after day one. The problem was never that exits are hidden in noise.
            It is that there are hardly any exits to find.
          </p>
        </section>

        {/* 3 */}
        <section>
          <h2>3. Two readings, and the data cannot pick between them</h2>
          <div className="grid cols-2">
            <div className="card">
              <span className="tag">Reading A</span>
              <p>
                <strong>These cars really do sit for months.</strong>{" "}
                <a href="/teardown-03">Teardown 03</a> showed this site is a Klang Valley
                premium and recond-import channel: 94 Bentleys listed against 23
                registered nationwide this year. Expensive stock is plausibly slow stock.
              </p>
            </div>
            <div className="card">
              <span className="tag">Reading B</span>
              <p>
                <strong>Sold cars stay listed.</strong> A dealer&apos;s ad page is also a
                shop window. Nothing forces a sold car&apos;s ad down, and an ad that
                stays up still brings enquiries.
              </p>
            </div>
          </div>
          <p>
            Listing snapshots alone cannot separate these; both produce ads that do not go
            away. What I <em>can</em> say is narrower and true:{" "}
            <strong>at least 95% of the ads live on 9 August were still up 54 calendar
            days later</strong> — and they had already been up for an unknown time before
            I started. That is a statement about ads, not about sales.
          </p>
        </section>

        {/* 4 */}
        <section>
          <h2>4. Price still barely moves</h2>
          <div className="card table-box">
            <table>
              <tbody>
                <tr><td>Listings seen on 2+ days</td><td>13,516</td></tr>
                <tr><td>Cut their price</td><td><strong>295 (2.18%)</strong></td></tr>
                <tr><td>Raised their price</td><td>20</td></tr>
                <tr><td>Median first cut</td><td><strong>RM 5,000 (2.01%)</strong></td></tr>
                <tr><td>Median observed days to first cut</td><td>7</td></tr>
                <tr><td>Median total discount</td><td>2.61%</td></tr>
              </tbody>
            </table>
          </div>
          <p>
            The cut rate roughly doubled from teardown 02&apos;s 1.15%. That is not a
            softening market — the window is 3.5× longer, so each ad has had more time to
            be cut. Same artifact family as last time, labelled the same way.
          </p>
          <p>
            One small signal worth watching: <strong>listings that left cut their price
            6.5% of the time, against 2.1% for those still listed.</strong> That is 13 cuts
            in 201 exits — too few to lean on, but it points the way you would expect if a
            cut is the last move before a car goes.
          </p>
        </section>

        {/* 5 */}
        <section>
          <h2>5. What this changes</h2>
          <ul>
            <li>
              <strong>Exit rule: N = 7 observed days</strong>, census era only. Teardown
              02&apos;s &ldquo;no N exists&rdquo; is withdrawn; it came from pooled data.{" "}
              <code>exit_rule.py</code> now refuses to pool.
            </li>
            <li>
              <strong>Still no days-to-sell number.</strong> 201 events with 98.5%
              censoring supports a lower bound, not a median.
            </li>
            <li>
              <strong>Sale vs removal is still unlabelled.</strong> Even a clean exit rule
              measures the ad coming down, not the car being sold. A labelled exit — a
              sold badge on the detail page — is still the only thing that turns this into
              days-to-sell.
            </li>
            <li>
              <strong>The Kaggle dataset now ships the 7-day column.</strong> The old{" "}
              <code>absent_ge_5_obs_days</code> was the too-loose rule (25.8% of 5-day
              absences reverse).
            </li>
            <li>
              <strong>The collector keeps running.</strong> This is the second published
              number a refit has overturned. Monthly refits stay.
            </li>
          </ul>
        </section>

        {/* METHOD */}
        <section>
          <h2>Method, and everything wrong with it</h2>
          <ul>
            <li>
              <strong>Source.</strong> Public listing pages on motortrader.com.my, one pass
              per day. <code>Crawl-delay: 5</code> honoured, crawler identified with a
              contact URL, no proxy rotation. mudah.my, carbase and wapcar excluded —
              their terms or signals don&apos;t permit this.
            </li>
            <li>
              <strong>Census era only.</strong> Every figure uses days from 2026-08-09
              that cleared 10,000 rows. Killed walks and the 2026-09-11..13 database outage
              are missing days, not absences: 38 observation days across 54 calendar days.
            </li>
            <li>
              <strong>Observed days, never calendar days</strong>, except where
              &ldquo;54 calendar days&rdquo; is said explicitly.
            </li>
            <li>
              <strong>The exit rule is bounded.</strong> No closed absence longer than 8
              observed days exists yet. Beyond that the zero is backed by up to 30+ days of
              exposure, which is evidence — but a listing returning after two months would
              still surprise this rule.
            </li>
            <li><strong>Gone is not sold.</strong> Every &ldquo;exit&rdquo; is an ad that stopped appearing.</li>
            <li><strong>Prices are asking prices.</strong> Transaction prices are not public.</li>
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
            · <a href="/teardown-03">Teardown 03: whose cars are these?</a> ·{" "}
            <a href="/teardown-02">Teardown 02: the censoring wall</a> ·{" "}
            <a href="/price-model">Earlier price-model demo</a>
          </p>
        </footer>
      </div>
    </main>
  );
}
