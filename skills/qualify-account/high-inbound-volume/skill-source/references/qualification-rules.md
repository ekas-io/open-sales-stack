# Qualification Rules

This document defines the qualification framework. There are two layers: a fast industry gate (Gate 0) and 5 research-based signals.

## Gate 0: Industry Pre-Check (Runs BEFORE Research)

The company must operate in the B2B SaaS/tech domain. This gate uses Apollo metadata only (industry, keywords, short_description) — no crawling required.

**PASS examples:** SaaS, software, cybersecurity, cloud infrastructure, developer tools, AI/ML platforms, data analytics, martech, fintech (software), healthtech (software), proptech (software), edtech (software).

**FAIL examples:** Newspapers/media, non-profits, government, restaurants/retail, pure consulting (no software product), venture capital / private equity, hospitals/clinics, law firms, construction, manufacturing (unless selling software).

If Gate 0 fails → **NOT QUALIFIED** immediately. Do not run any research. Save a brief industry disqualification note and add to Not Qualified list.

If Gate 0 passes → proceed to the 5-signal research below.

## Signal Definitions (Research-Based — Only Run If Gate 0 Passes)

| # | Signal | Match Condition |
|---|--------|----------------|
| 1 | Website Intelligence | Match if ANY of the following exist: free trial is offered, self-serve signup exists, OR product launches found on website |
| 2 | SDR/BDR Inbound Signal | Match if the job listing indicates inbound lead handling intent (role type is "purely inbound" or "mixed") |
| 3 | LinkedIn Ads | Match if active ad count > 1 |
| 4 | Recent Funding | Match if funding round found within the last 6 months (rolling window from current date) |
| 5 | Product Launch | Match if a product launch or major press release is found (from website crawl or Apollo) |

## Decision Logic

```
Signal 1 OR Signal 2 OR Signal 3 OR Signal 4 OR Signal 5 = QUALIFIED
```

If ALL five signals are **No Match** → **NOT QUALIFIED**

## Signal States

For each signal, report one of three states:

- **Match** — The signal condition was met based on collected data
- **No Match** — Data was collected and the signal condition was NOT met
- **Inconclusive** — The crawl failed or data was unavailable, so the signal could not be evaluated

Inconclusive signals do NOT count as a match. They should be noted but don't affect the qualification decision.

## Funding Window

The "last 6 months" window is a rolling calculation based on the current date. As of March 2026, this means funding after September 2025. Adjust accordingly when this skill runs at different dates.

## Why These Signals Matter

Understanding the reasoning helps you apply these rules accurately:

- **Signal 1 (Website Intelligence):** Self-serve signup, free trials, and product launches all generate inbound traffic — people signing up, trying the product, requesting demos. This means the company likely has leads to qualify.
- **Signal 2 (SDR Inbound):** If they're hiring SDRs specifically to handle inbound leads, they clearly have inbound volume that needs processing.
- **Signal 3 (LinkedIn Ads):** Active advertising drives traffic to their website, which generates leads. More ads = more inbound activity.
- **Signal 4 (Recent Funding):** Companies that just raised money are typically scaling their go-to-market, which means more hiring, more marketing, and more leads.
- **Signal 5 (Product Launch):** New product announcements drive press, interest, and demo requests — all of which create inbound lead volume.

## Customization Notes

If you need to adjust these rules for your specific use case:

- **Apollo List IDs and Custom Field ID:** These are configured during setup (`setup.sh`) and baked into SKILL.md. To change them, re-run the setup script.
- **Funding Window:** Change the 6-month lookback by modifying the date comparison logic in Step 6 of SKILL.md.
- **LinkedIn Ads Threshold:** Currently set to >1 ad. Adjust in Signal 3's match condition if needed.
- **Adding New Signals:** Add a new section to the research execution, define the match condition here, and update the qualification logic.
