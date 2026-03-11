# Open Sales Stack

**Open source MCP servers for B2B sales research — built by [Ekas](https://ekas.io)**

Give Claude the ability to research companies and prospects using public web data.

<a href="https://glama.ai/mcp/servers/ekas-io/open-sales-stack">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/ekas-io/open-sales-stack/badge" alt="open-sales-stack MCP server" />
</a>

> **Platform:** macOS only for now. Windows and Linux support coming soon.

---

## What's in here

| MCP Server | What you get | Status |
|---|---|---|
| **[website-intel](packages/website-intel/)** | Product info, pricing, team pages, company details — extracted as structured data from any website | ✅ Ready |
| **[techstack-intel](packages/techstack-intel/)** | CRM, marketing automation, analytics, chat, support tools — detected from page source | ✅ Ready |
| **[social-intel](packages/social-intel/)** | LinkedIn company profiles, people profiles, company posts | ✅ Ready |
| **[hiring-intel](packages/hiring-intel/)** | Open roles across Indeed, LinkedIn, Glassdoor, Google Jobs, ZipRecruiter, and direct careers pages | ✅ Ready |
| **[ad-intel](packages/ad-intel/)** | Active campaigns, ad creatives, targeting signals — from LinkedIn Ad Library and Meta Ad Library | ✅ Ready |
| **[review-intel](packages/review-intel/)** | Star ratings, review counts, pros/cons themes — from G2, Capterra, and Glassdoor | 🔄 In Progress |
| **[funding-intel](packages/funding-intel/)** | Funding rounds, investors, total raised, valuations — from Crunchbase and public filings | 🔄 In Progress |
| **[news-intel](packages/news-intel/)** | Recent press coverage, product launches, leadership changes, M&A activity | 🔄 In Progress |
| **[financial-reporting-intel](packages/financial-reporting-intel/)** | 10-K/10-Q filings, revenue, growth rate, operating margins, guidance — for public companies | 🔄 In Progress |
| **[firmographic-intel](packages/firmographic-intel/)** | Employee count, headcount growth, HQ location, founding year, industry, SIC/NAICS codes, legal entity name — all from public sources | 🔄 In Progress |
| **[github-intel](packages/github-intel/)** | Public repos, stars, contributors, commit activity, open issues, tech stack signals — from GitHub public API | 🔄 In Progress |

An API key from **OpenAI, Anthropic, or Google Gemini** is required for LLM-based extraction. Beyond that, no additional API keys are needed.
Each MCP runs locally on your machine. Your IP, your requests — no proxy infrastructure, no rate limiting concerns.

---

## Setup

You'll need two things installed before starting:

- **Python 3.10+** — download from [python.org](https://python.org) or install via `brew install python@3.12`
- **An LLM API key** — from [OpenAI](https://platform.openai.com), [Anthropic](https://console.anthropic.com), or [Google AI Studio](https://aistudio.google.com)

Then run these commands in your terminal:

```bash
# 1. Clone the repo
git clone https://github.com/ekas-io/open-sales-stack.git
cd open-sales-stack

# 2. Run setup (installs everything and prompts you to choose your LLM provider)
bash scripts/setup.sh

# 3. Verify your setup
bash scripts/verify.sh

# 4. Add all MCPs to Claude
bash scripts/add-to-claude.sh --all
```

By default, the script adds MCPs to **Claude Code** if the `claude` CLI is available, otherwise to **Claude Desktop**. You can override this:

```bash
bash scripts/add-to-claude.sh --all --desktop   # force Claude Desktop
bash scripts/add-to-claude.sh --all --code      # force Claude Code
```

The setup script will ask you to choose between OpenAI, Anthropic, or Gemini and prompt for your API key. It configures everything in `.env` automatically.

If you want to change the default model later, edit the `LLM_PROVIDER` value in your `.env` file. See `.env.example` for supported format.

During setup, you'll also be asked how you'd like to authenticate with LinkedIn (for social-intel):

1. **Skip** (default) — configure later; company scraping works without login
2. **Browser login** — a browser window opens, you log in manually
3. **Credentials** — provide your email + password, saved locally for headless login

See the [social-intel README](packages/social-intel/) for more details.

If you only want specific MCPs:

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
Claude calls: social-intel     → finds their VP Sales on LinkedIn, pulls bio and recent posts
Claude calls: review-intel     → pulls G2 rating (4.2/5, 47 reviews), Glassdoor sentiment
Claude calls: ad-intel         → 12 active LinkedIn ad campaigns, 5 on Meta
Claude calls: funding-intel    → Series B, $24M raised, led by Accel
Claude calls: firmographic-intel → 320 employees, 40% headcount growth YoY
Claude calls: news-intel       → 3 recent press mentions, product launch last month

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