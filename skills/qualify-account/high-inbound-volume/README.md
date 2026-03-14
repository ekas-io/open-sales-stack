# Qualify High Inbound Volume

A Claude skill that qualifies sales accounts based on whether they show signals of high inbound lead volume. It researches each account across 5 dimensions, applies qualification rules, saves a structured research report to Apollo, and sorts the account into a Qualified or Not Qualified list.

![Qualify Demo](../../assets/qualify-demo.gif)

## Setup

### Prerequisites

1. **Apollo account with API access**
   - Get your API key at [Apollo Settings > Integrations > API](https://app.apollo.io/#/settings/integrations/api)

2. **Apollo MCP installed in Claude**
   - The Apollo MCP from [apollo.io](https://apollo.io) must be configured in your Claude Code or Claude Desktop

3. **Open Sales Stack MCPs installed**
   - This skill uses website-intel, hiring-intel, and ad-intel MCPs for research
   - If you haven't set them up yet:
     ```bash
     bash scripts/setup.sh
     bash scripts/add-to-claude.sh --all
     ```

4. **Claude Code or Claude Desktop**
   - At least one must be installed

### Quick Start

```bash
# 1. Clone the repo (if you haven't already)
git clone https://github.com/ekas-io/open-sales-stack.git
cd open-sales-stack

# 2. Set up MCPs (if you haven't already)
bash scripts/setup.sh
bash scripts/add-to-claude.sh --all

# 3. Set up the skill
bash skills/qualify-account/high-inbound-volume/setup.sh
```

The setup script will:
- Ask for your Apollo API key (if not already in `.env`)
- Ask if you have existing Qualified/Not Qualified lists or want new ones created
- Create a "Research Notes" custom field in Apollo (if it doesn't exist)
- Install the skill to Claude

## Usage

In Claude Code or Claude Desktop, type:

```
/qualify-high-inbound-volume Datadog
/qualify-high-inbound-volume acme.com
/qualify-high-inbound-volume 6518c6184f20350001a0b9c0
/qualify-high-inbound-volume linkedin.com/company/acme
```

You can also qualify multiple accounts at once:

```
/qualify-high-inbound-volume Datadog, Freshworks, HubSpot
```

Or use natural language — the skill also triggers on phrases like "qualify this account", "is this account qualified", "research and qualify", etc.

## Why These 5 Signals?

The goal is to identify companies that are generating (or are about to generate) a high volume of inbound leads. Each signal is a proxy for inbound activity:

| # | Signal | Why It Matters |
|---|--------|----------------|
| 1 | **Website Intelligence** (free trial, self-serve signup, product launches) | Self-serve signup and free trials generate inbound traffic — people signing up, trying the product, requesting demos. Product launches drive interest and demo requests. |
| 2 | **SDR/BDR Inbound Signal** (hiring for inbound lead handling) | If a company is hiring SDRs specifically to handle inbound leads, they clearly have inbound volume that needs processing. |
| 3 | **LinkedIn Ads** (>1 active ad in last 30 days) | Active advertising drives traffic to the company's website, which generates leads. More ads = more likely to have inbound activity. |
| 4 | **Recent Funding** (funding round within last 6 months) | Companies that just raised money are typically scaling their go-to-market — more hiring, more marketing, and more leads. |
| 5 | **Product Launch** (new product or major feature release) | New product announcements drive press, interest, and demo requests — all of which create inbound lead volume. |

**Qualification rule:** If ANY one of these 5 signals is a positive match, the account is **Qualified**. If all 5 are negative, it's **Not Qualified**.

## How It Works

Here's the step-by-step flow when you run `/qualify-high-inbound-volume <account>`:

1. **Identifier resolution** — The skill takes whatever you give it (company name, domain, Apollo ID, LinkedIn URL) and resolves it to an Apollo Account.

2. **Industry gate (Gate 0)** — Before spending time on research, it checks if the company is in the B2B SaaS/tech space. Non-tech companies (consulting firms, media, non-profits, etc.) are immediately disqualified with a note explaining why.

3. **Research across 5 signals:**
   - **Website crawl** — Scrapes the company's homepage, pricing page, and signup page to check for free trials, self-serve signup, and product launches
   - **Job postings** — Searches Apollo and job boards for SDR/BDR roles, then analyzes the job description for inbound lead handling intent
   - **LinkedIn ads** — Queries the LinkedIn Ad Library for active ads in the last 30 days
   - **Funding data** — Extracts the most recent funding round from Apollo data
   - **Product launches** — Cross-references website crawl data with Apollo news/press data

4. **Qualification decision** — Evaluates all 5 signals. Any match = Qualified.

5. **Apollo update** — Saves a formatted research report to the account's "Research Notes" custom field and adds the account to the appropriate list (Qualified or Not Qualified).

6. **Summary** — Presents a table showing the account, result, matching signals, and any errors.

## What the Setup Creates in Apollo

| Resource | Type | Purpose |
|----------|------|---------|
| Research Notes | Custom field (account, textarea) | Stores the full research report for each account |
| Qualified | List (or your custom name) | Accounts that passed qualification |
| Not Qualified | List (or your custom name) | Accounts that failed qualification |

## Customization

To adjust the qualification rules (signal thresholds, decision logic, etc.), edit the files in `skill-source/` and re-run the setup script:

- **Signal definitions and thresholds** — `skill-source/references/qualification-rules.md`
- **Research prompts and schemas** — `skill-source/references/crawler-prompts.md`
- **Report format** — `skill-source/assets/research-report-template.md`
- **Example outputs** — `skill-source/examples/`

After editing, re-run `setup.sh` to rebuild and reinstall the skill.

## Required MCPs

This skill uses the following MCP tools during research:

| MCP | Tools Used | Purpose |
|-----|-----------|---------|
| Apollo | `view_account`, `search_accounts`, `organization_job_postings`, `update_account` | Account lookup, job postings, saving results |
| website-intel | `website_intel_extract` | Crawling company websites for pricing, trials, signups |
| hiring-intel | `search_jobs`, `extract_job_description` | Finding and analyzing SDR/BDR job postings |
| ad-intel | `ad_intel_linkedin_search` | LinkedIn advertising activity lookup |
