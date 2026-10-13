# Solution Brief — <ENGAGEMENT NAME>

> **Instructions for Coco:** Replace each `<…>` placeholder using only the content of the files in `01_Context/`. Keep this document under two pages. Do not invent requirements that are not implied by the source notes. Skeleton/pseudo-DDL only — this is demo-grade, not prod.

---

## 1. Snapshot

- **Customer:** <customer name>
- **Business sponsor:** <name, role>
- **Technical lead:** <name, role>
- **Demo objective (one sentence):** <…>

## 2. Personas

| Persona | Role | What they need |
|---------|------|----------------|
| <name> | <business persona> | <…> |
| <name> | <technical persona> | <…> |

## 3. Business Objectives (max 3)

1. <…>
2. <…>
3. <…>

## 4. Scope

**In scope (this demo):**
- <…>

**Out of scope:**
- Production data feeds, RLS/masking, CI/CD, monitoring, performance tuning.

## 5. High-Level Solution Flow

> Architecture is fixed: **Raw → Curated → Analytics → Cortex Analyst → Cortex Agent → Snowflake Intelligence**.

- **Raw:** <…>
- **Curated:** <…>
- **Analytics:** <…>
- **Cortex Analyst (semantic view):** <…>
- **Cortex Agent:** <…>
- **Snowflake Intelligence experience:** <…>

## 6. Skeleton Design

### Snowflake account setup
- **Database:** `SNOWBANK_DEMO`
- **Schemas:** `RAW`, `CURATED`, `ANALYTICS`, `ASSETS`
- **Warehouse:** `SNOWBANK_DEMO_WH`

### Raw layer (`SNOWBANK_DEMO.RAW`)
| Table | Approx rows | Notes |
|-------|-------------|-------|
| `CUSTOMERS` | <…> | <…> |
| `ACCOUNTS` | <…> | <…> |
| `TRANSACTIONS` | <…> | <…> |
| `MERCHANTS` | <…> | <…> |

### Curated layer (`SNOWBANK_DEMO.CURATED`)
| Table / view | Grain | Built from |
|--------------|-------|-----------|
| <…> | <…> | <…> |

### Analytics layer (`SNOWBANK_DEMO.ANALYTICS`)
| View | Purpose |
|------|---------|
| `VW_CUSTOMER_TRANSACTION_SUMMARY` | <…> |
| `VW_TRANSACTION_TRENDS` | <…> |

### Semantic view & agent
- **Semantic view:** `SNOWBANK_SEMANTIC_VIEW` over the analytics layer
- **Key dimensions / metrics:** <…>
- **Verified queries to seed:** <…>
- **Agent:** `SNOWBANK_RISK_AGENT`
  - Tools: Cortex Analyst (semantic view), `SEND_REPORT_EMAIL` SP *(activated in Scene 3 from `04_Assets/`)*
  - Skills: `html_report` *(activated in Scene 3 from `04_Assets/`)*

## 7. Success Criteria

- <…>
- <…>
