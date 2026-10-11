export default function Home() {
  return (
    <main>
      <div className="wrap">
        {/* HERO */}
        <section style={{ borderTop: "none" }}>
          <div className="eyebrow">LotClock · Malaysian used cars · final note</div>
          <h1>I stopped the collector. Here is what 85 days of scraping can and cannot tell you</h1>
          <p className="lead">
            LotClock set out to measure how fast used cars sell in Malaysia. The data
            answered a different question first: on this site, almost nothing leaves.
            Collection ended on 2026-10-11. The dataset and every teardown stay up as the
            finished piece.
          </p>
          <div className="grid cols-3" style={{ marginTop: 24 }}>
            <div className="card metric">
              <span className="big">13,683</span>
              <span className="label">listings tracked through the census era</span>
            </div>
            <div className="card metric">
              <span className="big">48</span>
              <span className="label">full-census observation days, out of 67 collection days</span>
            </div>
            <div className="card metric">
              <span className="big">1.6%</span>
              <span className="label">of ads clearly gone (7-day rule). 98.4% never show an ending</span>
            </div>
          </div>
          <p className="caption">
            Final Kaggle export, pinned to 2026-10-11. Collection ran 2026-07-19 to
            2026-10-11 on motortrader.com.my; census era (full-site walks) from
            2026-08-09. Earlier figures below keep their own dates.
          </p>
        </section>

        {/* 1 */}
        <section>
          <h2>1. Why I stopped</h2>
          <p>
            The question was days-to-sell. Teardown 04 found that once my own data-mixing
            error is removed, <strong>94.9%</strong> of the ads listed on 9 August were
            still up 54 days later (pinned 2026-10-01). The final export says the same
            thing with more days: 224 of 13,683 ads came down, and even those are ads
            coming down, not cars being sold.
          </p>
          <p>
            More days would add more &ldquo;still listed&rdquo; rows, not an answer. With
            98.4% of listings censored, the most this source can support is a lower bound
            on how long an ad stays up. Days-to-sell needs a labelled outcome, and these
            pages never carry one.
          </p>
        </section>

        {/* 2 */}
        <section>
          <h2>2. What the data can tell you</h2>
          <ul>
            <li>
              <strong>What this lot holds.</strong> A dealer-heavy, premium, Klang Valley
              inventory. Perodua and Proton are 62.6% of Malaysian registrations but 4.9%
              of these listings (teardown 03, pinned 2026-09-11).
            </li>
            <li>
              <strong>How long an ad stays up</strong>, honestly right-censored, on census
              days only.
            </li>
            <li>
              <strong>Asking-price behaviour:</strong> when and how much sellers cut, as
              dated rows in an append-only table.
            </li>
            <li>
              <strong>When an ad is really gone.</strong> A 7-observed-day absence comes
              back only 2.4% of the time (teardown 04, pinned 2026-10-01).
            </li>
          </ul>
        </section>

        {/* 3 */}
        <section>
          <h2>3. What it cannot tell you</h2>
          <ul>
            <li><strong>Days-to-sell.</strong> Gone is not sold.</li>
            <li><strong>Transaction prices.</strong> Every price here is an asking price.</li>
            <li>
              <strong>The Malaysian used-car market.</strong> This is one site&apos;s
              stock, and teardown 03 shows how far it sits from what the country registers.
            </li>
          </ul>
        </section>

        {/* 4 */}
        <section>
          <h2>4. What I would do first, next time</h2>
          <ul>
            <li>
              <strong>Identify the market before collecting it.</strong> The JPJ
              registration join took one script and would have reframed the project on
              day one.
            </li>
            <li>
              <strong>Find a labelled outcome before building a clock.</strong> A sold
              badge, a transfer record, anything that says &ldquo;sold&rdquo; rather than
              &ldquo;gone&rdquo;.
            </li>
            <li>
              <strong>Never pool coverage eras.</strong> Refits overturned two published
              numbers here; the bigger one, teardown 02&apos;s 60.2% return rate, came from
              mixing partial and full days.
            </li>
          </ul>
        </section>

        <footer>
          <p>
            Collected honouring robots.txt and the published crawl-delay, no proxy
            rotation, no personal data.{" "}
            <a href="https://github.com/TALVIN29/LotClock">Code on GitHub</a> ·{" "}
            <a href="https://www.kaggle.com/datasets/talvinlee/malaysian-used-car-listings-daily-snapshots">
              Final dataset on Kaggle
            </a>{" "}
            · <a href="/teardown-04">Teardown 04: the wall was partly mine</a> ·{" "}
            <a href="/teardown-03">Teardown 03: whose cars are these?</a> ·{" "}
            <a href="/teardown-02">Teardown 02: the censoring wall</a> ·{" "}
            <a href="/price-model">Earlier price-model demo</a>
          </p>
        </footer>
      </div>
    </main>
  );
}
