# Open Sales Stack

**Open source MCP servers for B2B sales research — built by [Ekas](https://ekas.io)**

Give Claude the ability to research companies and prospects using public web data.

> **Platform:** macOS only for now. Windows and Linux support coming soon.

---

## What's in here

| MCP Server | Source | What you get |
|---|---|---|
| **[website-intel](packages/website-intel/)** | Any website | Product info, pricing, team pages, company details — extracted as structured data |
| **[techstack-intel](packages/techstack-intel/)** | Company websites | CRM, marketing automation, analytics, chat, support tools — detected from page source |
| **[social-intel](packages/social-intel/)** | LinkedIn — Profile scrape | Name, headline, location, about, work experiences, education, skills |
| | LinkedIn — Company scrape | Company name, industry, size, headquarters, founded year, specialties, overview |
| | LinkedIn — Company posts | Recent posts with text, reaction counts, comment counts, repost counts, dates |
| **[hiring-intel](packages/hiring-intel/)** | Indeed | Job search across 60+ countries — best reliability, no rate limiting |
| | LinkedIn | Global job search (rate-limits apply, proxies recommended for volume) |
| | Glassdoor | Job search for select countries |
| | Google Jobs | Job search via Google search syntax |
| | ZipRecruiter | US & Canada job search |
| | Bayt | International job search |
| | Any careers page | Full job description extraction via crawl4ai (Greenhouse, Lever, Ashby, Workday, etc.) |
| **[review-intel](packages/review-intel/)** | G2 | Star rating, review count, category ranking, pros/cons themes |
| | Capterra | Star rating, review count, reviewer breakdown |
| | Glassdoor | Company rating, employee sentiment, CEO approval |
| **[ad-intel](packages/ad-intel/)** | LinkedIn Ad Library | Active campaigns, ad creatives, targeting signals |
| | Meta Ad Library | Active campaigns across Facebook and Instagram |

Requires an **OpenAI API key** for LLM-based extraction. Beyond that, no additional API keys are needed.
Each MCP runs locally on your machine. Your IP, your requests — no proxy infrastructure, no rate limiting concerns.

---

## Setup

You'll need two things installed before starting:

- **Python 3.10+** — download from [python.org](https://python.org) or install via `brew install python@3.12`
- **An OpenAI API key** — get one at [platform.openai.com](https://platform.openai.com)

Then run these commands in your terminal:

```bash
# 1. Clone the repo
git clone https://github.com/ekas-io/open-sales-stack.git
cd open-sales-stack

# 2. Run setup (installs everything you need)
bash scripts/setup.sh

# 3. Add your OpenAI API key
nano .env
# Set OPENAI_API_KEY=sk-...

# 4. Check that everything's working
bash scripts/verify.sh

# 5. Add all MCPs to Claude
bash scripts/add-to-claude.sh --all
```

During setup, you'll be asked how you'd like to authenticate with LinkedIn (for social-intel):

1. **Skip** (default) — configure later; company scraping works without login
2. **Browser login** — a browser window opens, you log in manually
3. **Credentials** — provide your email + password, saved locally for headless login

See the [social-intel README](packages/social-intel/) for more details.

That's it. If you only want specific MCPs, pick the ones you need:

```bash
bash scripts/add-to-claude.sh --website-intel --social-intel --hiring-intel
```

### Verify in Claude

Once added, ask Claude:

> "What MCP tools do you have access to?"

You should see your installed tools listed.

---

## How the MCPs work together

Each MCP is independent — use one or use all. But they're designed to chain naturally in Claude. Here's what a typical company research flow looks like:

```
You: "Research Acme Corp for me"

Claude calls: website-intel    → scrapes acmecorp.com, extracts product info, pricing, team
Claude calls: techstack-intel  → detects they use HubSpot, Drift, Segment
Claude calls: hiring-intel     → finds 3 open SDR roles on their Greenhouse page
Claude calls: social-intel     → scrapes their VP Sales LinkedIn profile, pulls bio, experience, and recent posts
Claude calls: review-intel     → pulls G2 rating (4.2/5, 47 reviews), Glassdoor sentiment
Claude calls: ad-intel         → 12 active LinkedIn ad campaigns, 5 on Meta

Claude: "Here's what I found about Acme Corp..."
```

You don't need to orchestrate this. Claude reads the tool descriptions and decides which to call based on your request.

---

## Skills

Skills are instruction files that teach Claude *how* to use research data for sales workflows. Drop them into your Claude project knowledge or reference them in prompts.

| Skill | What it teaches Claude |
|---|---|
| [Lead Qualification](skills/lead-qualification.md) | Evaluate whether a company matches your ICP based on research signals |
| [Prospect Research](skills/prospect-research.md) | Full account + contact level research methodology |
| [LinkedIn Recon](skills/linkedin-recon.md) | Read a prospect's LinkedIn profile and posts for outreach signals |
| [Cold Email Personalization](skills/cold-email-personalization.md) | Turn research into personalized outreach copy |

MCPs get the data. Skills tell Claude what to do with it.

---

## Each MCP in detail

Every package has its own README with tool descriptions, input/output schemas, and usage examples. Browse the [packages/](packages/) directory, or see detailed use cases on our website: **[ekas.io/open-sales-stack](https://ekas.io/open-sales-stack)**

---

## Contributing

Found a bug? Want to add a new research MCP? PRs welcome. See the [packages/](packages/) directory for the existing pattern.

---

## Custom sales automation

These tools cover common research workflows. If you need AI automation built for your team's specific sales stack — CRM integration, lead routing, qualification scoring, automated outreach — we build that.

**[ekas.io](https://ekas.io)** — AI engineering for B2B sales teams.

---

## License

MIT