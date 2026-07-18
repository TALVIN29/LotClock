-- LotClock schema, phase 1.
-- Run this in the Supabase SQL editor (Dashboard -> SQL Editor -> New query).
--
-- Two tables only. The full star schema (dim_seller, dim_vehicle, entity
-- resolution) comes once there are rows to normalise -- building dimensions
-- before there is data to put in them is how projects die before shipping.

-- One row per listing per day. APPEND-ONLY: a price change is a new row, never
-- an UPDATE. That is the whole basis for measuring anything over time.
create table if not exists listing_snapshot (
    id          bigserial primary key,
    listing_id  text        not null,
    scraped_at  date        not null default current_date,
    source      text        not null,
    price_myr   numeric,
    url         text,
    title       text,
    raw         jsonb       not null,     -- unknown/new fields land here safely
    inserted_at timestamptz not null default now(),
    unique (listing_id, scraped_at)       -- makes re-runs idempotent
);

create index if not exists listing_snapshot_listing_idx on listing_snapshot (listing_id);
create index if not exists listing_snapshot_date_idx    on listing_snapshot (scraped_at);

-- Operational log: lets a silently-dying scraper be noticed from the data side.
create table if not exists scrape_run (
    id          bigserial primary key,
    started_at  timestamptz not null default now(),
    source      text,
    rows_ok     int,
    rows_failed int,
    status      text
);

-- Row Level Security. The service key used by the GitHub Action bypasses RLS,
-- so writes still work; this exists so that if the anon key is ever exposed in
-- a browser later, it grants nothing by default.
alter table listing_snapshot enable row level security;
alter table scrape_run       enable row level security;


-- ---------------------------------------------------------------------------
-- Verification queries -- run these after two consecutive daily runs.
-- ---------------------------------------------------------------------------

-- 1. Rows landing at all?
-- select scraped_at, count(*) from listing_snapshot group by 1 order by 1 desc;

-- 2. THE gate: same listing captured on two different days.
-- select listing_id, count(distinct scraped_at) d
-- from listing_snapshot group by 1 having count(distinct scraped_at) > 1 limit 10;

-- 3. THE payoff: a price actually changing over time. This is the entire thesis.
-- select listing_id, min(price_myr) lo, max(price_myr) hi, count(*) snaps
-- from listing_snapshot group by 1 having min(price_myr) <> max(price_myr);

-- 4. Delistings: seen before, absent today.
-- select listing_id, max(scraped_at) last_seen from listing_snapshot
-- group by 1 having max(scraped_at) < current_date - 1 limit 20;
