import ChannelRatio from "@/components/ChannelRatio";

export default function Home() {
  return (
    <main>
      <div className="wrap">
        {/* HERO */}
        <section style={{ borderTop: "none" }}>
          <div className="eyebrow">LotClock · Malaysian used cars · teardown 03</div>
          <h1>I spent two months measuring a market I had not identified</h1>
          <p className="lead">
            The last teardown established that listing data cannot say when a car sold.
            This one is about a question I never thought to ask: whose cars are these?
            Malaysia publishes every car registration in the country, free. Put the two
            side by side and the site I have been scraping turns out not to be the
            Malaysian used-car market at all.
          </p>
          <div className="grid cols-3" style={{ marginTop: 24 }}>
            <div className="card metric">
              <span className="big">62.6%</span>
              <span className="label">of registrations are Perodua or Proton</span>
            </div>
            <div className="card metric">
              <span className="big">4.9%</span>
              <span className="label">of the lot is Perodua or Proton</span>
            </div>
            <div className="card metric">
              <span className="big">2,919×</span>
              <span className="label">spread between the most and least over-represented make</span>
            </div>
          </div>
          <p className="caption">
            13,324 listings (census era, all model years) against 566,616 JPJ first
            registrations, 2026-01-01 to 2026-08-31. Figures pinned to 2026-09-11 —
            both sources keep moving, so quote the date with the number.
          </p>
        </section>

        {/* 1 */}
        <section>
          <h2>1. Two months in, I had a numerator and no denominator</h2>
          <p>
            Every number this project produced was a count of listings. 4,166 Toyotas on
            the lot. 1,724 Mercedes. Those are real counts, and on their own they mean
            nothing — busy and stuck look identical from inside the shop window. To read
            a supply figure you need to know what demand looks like, and I had no source
            for it, so I never wrote the comparison down.
          </p>
          <p>
            It turns out JPJ has published it the whole time.{" "}
            <a href="https://data.gov.my/data-catalogue/registration_transactions_car">
              Car registration transactions
            </a>{" "}
            on data.gov.my: every car registered in Malaysia, CC BY 4.0, monthly, 566,616
            rows so far in 2026. No scraping, no permission, no robots.txt to honour. A
            32 MB CSV I should have looked for in July.
          </p>
          <p>
            The join is a CSV merge on manufacturer name. It reaches{" "}
            <strong>99.7% of listings</strong> once five title-truncations are aliased
            (<code>LAND</code> → <code>LAND ROVER</code> and four friends). That is the
            entire technical content of this teardown. The finding is what fell out.
          </p>
        </section>

        {/* 2 */}
        <section>
          <h2>2. The lot is stocked upside down</h2>
          <div className="card chart-box">
            <ChannelRatio />
            <p className="caption">
              Listings per 1,000 first registrations, by make. Log scale — the spread is
              2,919×, and on a linear axis every national make collapses to a stub.
              Orange is Perodua and Proton.
            </p>
          </div>
          <p>
            Perodua is the best-selling make in the country by a wide margin — 219,559
            registrations — and appears <strong>300 times</strong> on the lot. Bentley
            registered 23 cars nationwide all year and appears <strong>94 times</strong>.
            Ninety-four Bentleys for sale, against twenty-three Bentleys entering the
            country.
          </p>
          <div className="card table-box">
            <table>
              <thead>
                <tr><th>Group</th><th>Share of registrations</th><th>Share of the lot</th></tr>
              </thead>
              <tbody>
                <tr><td>Perodua + Proton</td><td>62.6%</td><td>4.9%</td></tr>
                <tr><td>Exotics (Bentley, Ferrari, Lamborghini, Porsche, …)</td><td>0.41%</td><td>13.4%</td></tr>
                <tr><td>Chinese &amp; EV entrants (Chery, BYD, Jetour, …)</td><td>7.5%</td><td>0.36%</td></tr>
              </tbody>
            </table>
          </div>
          <p>
            Two thirds of the market is 5% of the inventory. Four tenths of one percent
            of the market is an eighth of it. Whatever motortrader is, it is not a
            cross-section of Malaysian car ownership.
          </p>
        </section>

        {/* 3 */}
        <section>
          <h2>3. What this ratio is not</h2>
          <p>
            This is the part I would have skipped a month ago, and the previous teardown
            is the reason I did not.
          </p>
          <div className="grid cols-2">
            <div className="card">
              <span className="tag">Stock vs flow</span>
              <p>
                Listings are cars standing for sale <em>now</em>, of every model year.
                Registrations are cars entering the road <em>during 2026</em>. A 2015
                Toyota on the lot was registered in 2015 and is nowhere in the
                denominator. The two are not the same units.
              </p>
            </div>
            <div className="card">
              <span className="tag">Not turnover</span>
              <p>
                Nothing here is a sell-through rate, a days-to-sell, or a liquidity
                measure. Teardown-02 still stands: listing data cannot see when a car
                sold, and adding a second dataset does not change that.
              </p>
            </div>
          </div>
          <p>
            <strong>And I had to check what a &ldquo;registration transaction&rdquo;
            counts.</strong> The catalogue description is ambiguous about whether
            ownership transfers are included — which matters enormously, because
            transfers would make this a used-car denominator instead of a new-car one.
            Rather than trust the blurb I tested it: Naza, Saab, Opel and Rover all show{" "}
            <strong>zero</strong> 2026 rows, and there are plenty of those still on
            Malaysian roads changing hands. Chevrolet shows 15. Meanwhile Chery shows
            21,206. The dataset is first registrations, and the annualised volume
            (~850,000) matches national new-vehicle sales rather than the millions of
            ownership transfers.
          </p>
          <p>
            So the honest reading is narrow: <strong>this is a channel-composition
            comparison.</strong> The mix of makes on the lot versus the mix of makes
            entering the country. It cannot tell you how fast anything sells. It can tell
            you, decisively, that the two mixes are not drawn from the same population —
            and that is the claim I have been implicitly making wrong for two months.
          </p>
        </section>

        {/* 4 */}
        <section>
          <h2>4. The blind spot this exposes</h2>
          <p>
            Malaysia&apos;s new-car market is in the middle of a visible shift. Chinese
            marques and EVs were <strong>7.5% of 2026 registrations</strong> — Chery
            alone 21,206, Jetour 7,503, BYD 7,472. Electric is 8.4% of all registrations
            by fuel type.
          </p>
          <div className="card table-box">
            <table>
              <thead>
                <tr><th>Make</th><th>2026 registrations</th><th>On the lot</th></tr>
              </thead>
              <tbody>
                <tr><td>Chery</td><td>21,206</td><td>16</td></tr>
                <tr><td>Jetour</td><td>7,503</td><td>0</td></tr>
                <tr><td>BYD</td><td>7,472</td><td>5</td></tr>
                <tr><td>Tesla</td><td>3,733</td><td>5</td></tr>
                <tr><td>Leapmotor</td><td>1,512</td><td>0</td></tr>
              </tbody>
            </table>
          </div>
          <p>
            Forty-eight listings in total, 0.36% of the lot, against 7.5% of the
            country&apos;s registrations. Partly that is age — these cars are too new to
            resell in volume yet. But it means any trend I might have claimed to observe
            about &ldquo;the Malaysian used-car market&rdquo; would have been blind to the
            single largest thing happening in it.
          </p>
        </section>

        {/* 5 */}
        <section>
          <h2>5. What this changes</h2>
          <ul>
            <li>
              <strong>The scope claim gets rewritten everywhere.</strong> Not
              &ldquo;Malaysian used-car liquidity&rdquo;. This is a Klang Valley premium
              and recond import channel — which also explains why 52.5% of the rows are
              RECOND and why Kuala Lumpur and Selangor are 98.6% of them. Narrower, and
              for the first time provable against an external source.
            </li>
            <li>
              <strong>A public dataset beat two months of scraping.</strong> The scraper
              was necessary — nobody publishes what sits on the lot. But the single most
              informative number in this project came from a CSV download, and I did not
              go looking for it because I had framed the problem as a collection problem.
            </li>
            <li>
              <strong>Segment before fitting anything.</strong> Recond imports and
              owner-sold used cars are two populations sharing one table. A survival curve
              over the pool would describe neither, and the make mix is now the evidence
              for that rather than a hunch.
            </li>
            <li>
              <strong>The collector keeps running.</strong> Unchanged. The dataset is
              still the asset, and this teardown exists because a free CSV overturned the
              framing of everything built on top of it.
            </li>
          </ul>
        </section>

        {/* METHOD */}
        <section>
          <h2>Method, and everything wrong with it</h2>
          <ul>
            <li>
              <strong>Sources.</strong> Listings: public listing pages on
              motortrader.com.my, one pass per day, <code>Crawl-delay: 5</code> honoured,
              crawler identified with a contact URL, no proxy rotation or evasion.
              Registrations: <code>registration_transactions_car</code> on data.gov.my,
              CC BY 4.0.
            </li>
            <li>
              <strong>No state join.</strong> 87.5% of JPJ rows carry state{" "}
              <code>Rakan Niaga</code> — the trade partner&apos;s registration point, not
              where the car went. Joining on it would look correct and mean nothing, so
              geography is left out of the comparison entirely.
            </li>
            <li>
              <strong>No model-level matching.</strong> Exact model strings would cover
              76.4% of listings, and a similarity threshold invented here is a knob I
              could not defend. Make-level only; the model-level rate is printed, not
              patched.
            </li>
            <li>
              <strong>Makes under 20 listings are omitted from the chart.</strong> Below
              that the ratio swings on single cars. Six makes never matched at all — two
              are title-parse noise (<code>2024</code>, <code>TQ</code>), and Haval
              genuinely registered zero cars in 2026.
            </li>
            <li>
              <strong>The windows do not align and are not made to.</strong> JPJ covers
              2026-01-01 to 2026-08-31 and lags a month; the census era starts 2026-08-09.
              This compares shape across makes, never a rate per unit time.
            </li>
            <li>
              <strong>Recond units register too.</strong> An imported used Bentley is a
              first registration in Malaysia, so it does appear in the denominator. The
              ratio is not measuring &ldquo;new versus used&rdquo;; it is measuring which
              makes this channel carries relative to the whole country.
            </li>
            <li>
              <strong>Everything in teardown-02 still applies.</strong> No exit rule, no
              days-to-sell, no survival model. Nothing here should be read as an estimate
              of how long a Malaysian used car takes to sell.
            </li>
          </ul>
        </section>

        <footer>
          <p>
            Numbers reproducible with <code>jpj_join.py</code>; it self-checks on
            synthetic data with <code>--test</code> and no network, and caches the JPJ CSV
            after one download.{" "}
            <a href="https://github.com/TALVIN29/LotClock">Code on GitHub</a> ·{" "}
            <a href="https://www.kaggle.com/datasets/talvinlee/malaysian-used-car-listings-daily-snapshots">
              Daily snapshots on Kaggle
            </a>{" "}
            · <a href="/teardown-02">Teardown 02: the censoring wall</a> ·{" "}
            <a href="/price-model">Earlier price-model demo</a>
          </p>
        </footer>
      </div>
    </main>
  );
}
