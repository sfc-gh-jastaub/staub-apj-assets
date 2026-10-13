# SnowBank Demo — Presenter Narrative
## Cortex Code · Live · 30 minutes

> **Format:** Stage directions in *italics*. Things you say in **bold quotes**. Prompts in code blocks — type or paste exactly.

---

## 0 · Cold open (~30 sec)

*Stand. Single slide on screen: the one-pager.*

> **"Thirty minutes. One person. One platform. We're going to take two sets of stakeholder notes from a customer called SnowBank — and ship a working, governed analytics platform with a chat interface and a report in your inbox. No SQL written by hand. No tool-jumping. Let's go."**

*Switch to your IDE / Snowsight tab. Cortex Code panel open. The `Demo/` folder visible in the tree.*

---

## Scene 1 · Build solution design from discovery notes (~4 min)

*Open `Demo/01_Context/`. Show the two files briefly.*

> **"Two stakeholders gave us their input. Sarah, Head of Risk — she's drowning in false positives and can't get clean answers fast. And Raj, Data Platform Lead — mid-migration to Snowflake, wants a reusable pattern. That's it. That's our brief."**

*Open `Demo/02_Design/solution_brief_template.md`. Scroll the placeholders.*

> **"On a real project this is a week of meetings and three drafts. Watch."**

**Prompt 1** *(paste into Cortex Code):*
```
Read everything in Demo/01_Context/. Using the template at
Demo/02_Design/solution_brief_template.md, produce
Demo/02_Design/solution_brief.md — persona, objective, scope, high-level
flow, and skeleton design (pseudo-DDL only). Demo-grade.
```

*Coco produces the brief. Open it on screen. Scroll the personas, the scope, the skeleton tables.*

> **"That's the first morning of every new technology project — done in one prompt. Notice it pulled the customer counts from Raj's notes, the persona language from Sarah's. It didn't invent anything."**

---

## Scene 2 · Build the data layer (~8 min)

*Toggle Cortex Code into **Plan mode**. Point to the toggle as you do it.*

> **"This next bit actually changes the world — it creates tables, loads data. So we switch into Plan mode. Coco shows me what it's going to do *before* it does it. I approve. That's auditability."**

**Prompt 2** *(paste, Plan mode on):*
```
Using Demo/02_Design/solution_brief.md, build the data layer in Snowflake.
Use the sql-author skill to validate columns and table shape before
writing each new script.

Execute these in order:
  1. Demo/03_Build/01_database_setup.sql  (already exists — run as-is)
  2. Demo/03_Build/02_raw.sql             (already exists — run as-is,
     it generates all four raw tables in one set-based pass)
  3. Demo/03_Build/03_curated.sql         (you write this — conformed,
     cleansed entities derived from raw)
  4. Demo/03_Build/04_analytics.sql       (you write this — aggregations
     and behavioural views ready for Cortex Analyst)

For 03 and 04: write set-based SQL only. No row-by-row INSERTs. No
Python. If a script fails, debug and re-run.
```

*Plan appears. **Pause physically. Let it sit on screen for 2 seconds.***

> **"This is the gate. Nothing has touched the database yet. Coco's told me exactly what it intends to do — run the prebuilt setup and raw seed, then write the curated and analytics layers from scratch. If I don't like it, I change it. If I do, I approve. That's auditable AI."**

*Click **Approve** with intent. Coco starts executing. Raw layer drops in seconds; curated and analytics SQL files appear in `03_Build/` in real time.*

> **"While this runs — the trick with set-based SQL is it's done in seconds, not minutes. We're generating 15,000 transactions in a single statement."**

*When all four files are written and executed, ask a quick question:*

**Prompt 3:**
```
Quick question — using the analytics views you just built, show me the
headline trends in SnowBank's transactions over the last 6 months. One
short answer.
```

*Coco answers fast. Volumes are stable, segments are normal-looking.*

> **"OK — few odd things there. I can see why Sarah might be losing sleep. Let me push harder."**

**Prompt 4:**
```
Quick question — zoom in on the last 90 days. Are there any customer
segments whose transaction *behaviour* has shifted versus their
historical baseline? Be specific.
```

*Coco surfaces the structuring band, international spike, decline-rate skew. **This is the discovery moment.***

> **"There it is. Behaviour shift in private wealth and premium segments — transactions clustering right under the ten-thousand-dollar reporting threshold, international spikes from accounts that have never moved money offshore. That's the signal Sarah's been chasing for two years and couldn't get out of her current tools. Two questions. No SQL."**

---

### Bridge · Kick off the intelligence build, then show the data layer

*This is the time-killer. The intelligence build is the slowest live step. Start it now, then go for a tour while it runs.*

**Prompt 5** *(no need for Plan mode this time — say so):*
```
Use the semantic-view skill to build a Cortex Analyst semantic view
called SNOWBANK_SEMANTIC_VIEW over the analytics layer.

Then use the cortex-agent skill to create a Cortex Agent called
SNOWBANK_RISK_AGENT that uses the semantic view. Make sure the agent is
registered and active in Snowflake Intelligence.
```

*As soon as Coco starts working, switch tab to Snowsight.*

> **"That's going to take 60–90 seconds. Don't sit and watch a progress bar — let me show you what just got built."**

*In Snowsight, navigate to:*
- `SNOWBANK_DEMO` → `RAW` → expand tables (CUSTOMERS, ACCOUNTS, MERCHANTS, TRANSACTIONS) → click TRANSACTIONS, hit "Data Preview"
- `SNOWBANK_DEMO` → `CURATED` → show the conformed views
- `SNOWBANK_DEMO` → `ANALYTICS` → click `VW_CUSTOMER_TRANSACTION_SUMMARY` → preview

> **"This is real. Real schemas, real data, real Snowflake objects. Ten minutes ago none of this existed. Now it's a governed three-layer warehouse — and an analyst could open this account right now, type a query, and use it."**

*Now flip back to Cortex Code. Intelligence layer should be done or finishing.*

---

## Scene 3 · Build the intelligence layer (~9 min)

*Confirm semantic view + agent are built. Open Snowflake Intelligence in a new tab. Pick the SNOWBANK_RISK_AGENT.*

> **"Same agent we just built. Available right here in Snowflake Intelligence. Sarah's team can use this Monday morning."**

**SI Question 1** *(re-ask Scene 2's discovery question — same answer, now in the chat tool the broader team can use):*
```
Which customer segments show the most unusual transaction behaviour in
the last 90 days?
```

*Answer comes back fast.*

> **"See that? Verified query. Same question I asked Coco a moment ago — but now it's blessed, audited, and instant. That's how you scale trust."**

**SI Question 2** *(should produce a chart):*
```
Show me the monthly trend of international transfer volume by customer
segment for the last 12 months.
```

*Chart appears. Save as artefact.*

> **"Save this as an artefact. Now it lives — anyone with access to this agent can pick it up, paste it in a deck, send it on."**

**SI Question 3** *(triggers deep research / swarm):*
```
Investigate the structuring patterns we're seeing. Profile the customers
involved, characterise the transactions, and recommend three immediate
actions for the Risk team. Be thorough.
```

*Deep research / swarm kicks off. Don't wait — talk over it.*

> 🔔 **Presenter note:** As soon as deep research starts running, quickly flip to Cortex Code and fire **Prompt 6** (skill + email-tool activation — it's a few sections down). Submit it and leave it running. *Don't narrate this — just do it.* By the time deep research returns, the agent will already have the new skill + tool live and Scene 4 lands in seconds.

*Flip back to Snowflake Intelligence. Use the wait time to talk about the artefact pane and what just happened.*

> **"While that runs — let me show you what we just built. Look at the artefact panel. That chart from a moment ago? It's not screenshot, it's not a paste — it's a live, queryable artefact. The data behind it refreshes when the underlying tables update. The agent can recall it. Anyone in Sarah's team with access to this agent can pull it up, drop it into a deck, embed it in a report. The artefact is the new unit of analytical work."**

*Wait for the output. When it lands, scroll through the headline finding.*

> **"That's a piece of work my analyst would have spent half a day on. Done in two minutes."**

---

## Scene 4 · Reporting & documentation (~8 min)

*Pivot the energy. Stay in Snowflake Intelligence for one beat.*

> **"Great analysis. Sarah's not going to read this in a chat window though — she wants something she can send to the CRO."**

*Flip back to Cortex Code.*

**Prompt 6:**
```
Use the cortex-agent skill to extend SNOWBANK_RISK_AGENT.

1. Activate the prebuilt HTML report skill at
   Demo/04_Assets/skills/html_report/ — upload it to the agent's stage
   and add it via the Skills tab.

2. Run Demo/04_Assets/tools/send_email_tool.sql to create the email
   notification integration and SEND_REPORT_EMAIL stored procedure, then
   attach that procedure as a generic tool on the agent.

Confirm both are live in Snowflake Intelligence.
```

*Coco does both. Show the agent's Tools tab and Skills tab populating.*

> **"Two prebuilt assets — a skill and a tool — activated on a live agent. No redeploy. No restart. Sarah doesn't even need to refresh."**

*Back to Snowflake Intelligence. Same chat thread.*

**SI Question 4:**
```
Summarise that analysis, use the html_report skill to format it into a
concise report, and email it to me at your.email@example.com.
```

*Skill formats the report inline. Email tool fires. Report lands in inbox.*

> **"Question, answer, action. One sentence — summarise, format, deliver. Sarah just went from 'tell me about my data' to 'here's the report I'm forwarding to the CRO' — and she never left her chat window."**

*Back to Cortex Code. One more prompt.*

**Prompt 7:**
```
Document the engagement. Update Demo/02_Design/solution_brief.md with
what was actually deployed (data layers, semantic view, agent, tools,
skills). Then generate a runbook in
Demo/02_Design/runbook.md covering how the SnowBank team operates and
extends this. Save the email HTML output into Demo/02_Design/artefacts/.
```

*Coco produces the docs. Open the runbook briefly.*

> **"Project closed. Brief updated, runbook delivered, artefacts archived. The next person who picks this up can do so cold."**

---

## Closing beat (~30 sec)

*Stand. Slide back to the one-pager. Glance at your watch / the clock.*

> **"I told you 30 minutes. Look at the clock.**
>
> **Thirty minutes ago we had two markdown files. We now have a governed Snowflake account, a semantic view, a Cortex Agent live in Snowflake Intelligence, a chart artefact, a deep-research investigation, a polished HTML report, an email in my inbox, and a documented handover.**
>
> **Three things to take away:**
>
> **One — folder-driven projects. Cortex Code mirrors how delivery teams already work.**
>
> **Two — Plan mode means auditable AI. Nothing happens you didn't approve.**
>
> **Three — skills compound. Every demo we do leaves reusable IP behind for the next one.**
>
> **Now imagine this on every new technology project, every week. Questions?"**

---

## Presenter cheat-sheet

| Beat | If it stalls… |
|------|---------------|
| Scene 2 SQL build stalls | `02_raw.sql` is prebuilt — worst case Coco only needs to write `03_curated.sql` + `04_analytics.sql`. If even those stall, ask Coco to skip curated and build analytics directly off raw |
| Bridge tour drags | Skip Curated, jump to ANALYTICS preview |
| Semantic view / agent build slow | Talk through Snowsight, take Q&A on architecture |
| Verified query doesn't trigger | Re-ask, point out the speed difference |
| Deep research takes forever | Have a recorded output ready in a side tab |
| Email doesn't arrive | Show the rendered HTML directly in SI; *"the email pipeline's a notification integration — works end-to-end in your tenant"* |
| Documentation prompt slow | Cut to closing beat — the deck and the runbook can land off-camera |

---

## Pre-flight checklist (10 min before going live)

- [ ] **Use ACCOUNTADMIN throughout the demo** — avoids role / privilege issues for notification integrations and stages
- [ ] `01_database_setup.sql` already executed (DB / schemas / WH exist, idempotent)
- [ ] `02_raw.sql` reviewed and ready to run as-is in Scene 2
- [ ] Cortex Code session **fresh** (no leftover context)
- [ ] Snowsight tab open on `SNOWBANK_DEMO` database, signed in
- [ ] Snowflake Intelligence tab open and signed in
- [ ] Email client open on the address listed in `04_Assets/tools/send_email_tool.sql`
- [ ] Send-email notification integration smoke-tested
- [ ] One-pager slide ready as the cold-open visual
- [ ] Phone on silent. Slack closed. Notifications muted.
