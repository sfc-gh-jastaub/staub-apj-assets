# Notes from Raj Patel — Data Platform Lead, SnowBank
*Subject: technical context for the engagement*
*Captured: whiteboard session with consulting team*

---

Quick rundown of where we're at technically so you've got the lay of the land before you start.

**Current stack:**
- Core banking system (T24) — daily extracts to S3, batch only
- Card transactions — separate feed from our processor, also daily
- CRM (Salesforce) for customer/account master data
- Existing data warehouse is a tired on-prem Teradata box — we're mid-migration to Snowflake. Most of the new work is going there.

**What's already in Snowflake:**
- Raw landing zone (`SNOWBANK_RAW`) — landed daily, no transformation
- Some half-done curated tables but no consistent modelling pattern
- No semantic layer, no governance on column-level descriptions, nothing that an analyst can self-serve from

**Pain points I want this engagement to solve:**
1. **Standardise the layers.** Raw → Curated → Analytics. Pick one pattern and stick to it. I don't want six different ways of building gold tables.
2. **Make analytics self-serve.** Risk team is begging us for ad-hoc queries and we can't service them. If we can stand up something where Sarah's team types English and gets SQL back, that's a massive win.
3. **Reusable assets.** Whatever we build I want the engineering team to be able to clone the pattern for next workstream (retail credit, fraud, capital reporting). Don't build a one-off.
4. **Governance and audit trail.** We're a bank. Every query, every model output needs to be auditable. I need to know who asked what, when, and what data they got.

**Constraints:**
- Demo / POC scope only at this stage. Production hardening comes later.
- Use existing warehouse `SNOWBANK_DEMO_WH` — don't spin new compute up.
- Synthetic data is fine for now while privacy clears the real feeds.
- Stick to Snowflake-native services where possible. We don't want a stack of bolt-on vendors.

**Datasets I'd seed for the demo:**
- `CUSTOMERS` (~500) — customer master with segment, state, risk rating, occupation, income
- `ACCOUNTS` (~700) — account types per customer
- `TRANSACTIONS` (~15k) — 12 months of history with amount, channel, merchant, country, status, international flag. Keep the volume modest — we want fast iteration, not realistic warehouse scale.
- `MERCHANTS` (~200) — merchant reference with category and risk classification

That should be enough surface area to demonstrate the pattern. **Generate it with set-based SQL (`GENERATOR` + `UNIFORM` etc.) — no row-by-row inserts, no Python loaders.** I want this loaded in seconds, not minutes.

— Raj
