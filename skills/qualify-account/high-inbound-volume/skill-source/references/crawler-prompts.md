# Research Tool Prompts and Schemas

This file contains the exact prompts, schemas, and tool usage instructions for each research dimension. Each section specifies which MCP tool to use and how to call it.

- **Section 1 (Website Intelligence):** Uses `website_intel_extract` (website-intel MCP) — crawls the company website
- **Section 2 (SDR Job Analysis):** Uses `extract_job_description` and `search_jobs` (hiring-intel MCP) — retrieves and analyzes job postings
- **Section 3 (LinkedIn Ads):** Uses `ad_intel_linkedin_search` (ad-intel MCP) — queries the LinkedIn Ad Library

Use the prompts and schemas verbatim. Do not modify them or write your own — consistency matters for reliable signal extraction.

---

## Section 1: Website Intelligence

**Tool:** `website_intel_extract` (website-intel MCP)

Website intelligence is gathered through **multiple targeted single-page scrapes** instead of one large crawl. This is faster and more reliable. The flow is:

1. **Call 1A: Homepage Scan** — scrape the homepage to discover CTAs, product launch banners, and URLs to key pages
2. **Call 1B: Pricing & Trial Page** — scrape the pricing page URL discovered in Call 1A (skip if no pricing URL found)
3. **Call 1C: Signup Validation** — scrape the signup/get-started page URL discovered in Call 1A to verify it's truly self-serve (skip if no signup URL found)

### Call 1A: Homepage Scan

**Purpose:** Discover what the company offers and find URLs for deeper investigation.

```
website_intel_extract(
  url: "<company_homepage_url>",
  mode: "scrape",
  prompt: "<prompt below>",
  schema: <schema below>
)
```

**Prompt:**
```
Extract the following from this homepage:

1. CTA BUTTONS: List every distinct call-to-action button or link visible on the page. For each one, extract the exact button/link text AND the URL it points to. Examples of CTA text: "Book a Demo", "Contact Us", "Sign Up", "Start Free Trial", "Request Pricing", "Talk to Sales", "Get Started", "See Plans", "Try for Free". Only include actionable buttons/links, not navigation menu items like "About" or "Blog" (unless the blog link is relevant to a product announcement).

2. KEY PAGE URLS: From the CTAs and navigation, identify the URLs for these specific pages if they exist:
   - Pricing page (contains pricing tiers, plan comparisons, or "See Plans"/"Pricing" links)
   - Signup/registration page (contains "Sign Up", "Create Account", "Get Started Free", "Start Trial" links)
   - Blog or newsroom page (for product announcements)

3. PRODUCT LAUNCH BANNERS: Are there any banners, hero sections, or prominent announcements on the homepage about new product launches, major feature releases, or recent announcements? If yes, extract the product/feature name, a brief description, and the date if shown. Look for things like "Introducing...", "Now available...", "New:", "Just launched:", announcement bars at the top of the page, etc.

4. INITIAL SELF-SERVE IMPRESSION: Based solely on the homepage CTAs, does it APPEAR that the company offers self-serve signup? (This will be validated in a follow-up call.) Look for CTAs like "Sign Up Free", "Start Free Trial", "Create Account", "Get Started" that suggest a user can sign up without talking to sales. Note: CTAs like "Book a Demo", "Contact Sales", "Request a Quote" suggest sales-led, NOT self-serve.
```

**Schema:**
```json
{
  "type": "object",
  "properties": {
    "ctas": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "text": { "type": "string", "description": "Exact text of the CTA button or link" },
          "url": { "type": "string", "description": "The URL the CTA points to (absolute or relative)" }
        }
      },
      "description": "All distinct CTA buttons/links found on the homepage"
    },
    "key_page_urls": {
      "type": "object",
      "properties": {
        "pricing_url": { "type": "string", "description": "URL of the pricing page, or null if not found" },
        "signup_url": { "type": "string", "description": "URL of the signup/registration/get-started page, or null if not found" },
        "blog_or_newsroom_url": { "type": "string", "description": "URL of the blog or newsroom, or null if not found" }
      }
    },
    "product_launch_banners": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string", "description": "Product or feature name" },
          "description": { "type": "string", "description": "Brief description of the announcement" },
          "date": { "type": "string", "description": "Date if shown, otherwise 'Date not specified'" }
        }
      },
      "description": "Product launch banners or announcements on the homepage. Empty array if none."
    },
    "appears_self_serve": {
      "type": "boolean",
      "description": "True if homepage CTAs suggest self-serve signup exists (e.g. 'Sign Up Free', 'Start Trial'). False if CTAs are only sales-led (e.g. 'Book a Demo', 'Contact Sales'). This is a preliminary signal — validated in Call 1C."
    }
  }
}
```

---

### Call 1B: Pricing & Trial Page

**When to run:** Only if Call 1A returned a `pricing_url`. Skip if no pricing page was found.

**Purpose:** Extract pricing tiers and free trial details from the dedicated pricing page.

```
website_intel_extract(
  url: "<pricing_url_from_call_1a>",
  mode: "scrape",
  prompt: "<prompt below>",
  schema: <schema below>
)
```

**Prompt:**
```
Extract pricing and trial information from this pricing page:

1. PRICING TIERS: For each pricing tier or plan shown, extract:
   - The tier/plan name (e.g. "Starter", "Pro", "Enterprise")
   - The price (monthly and/or annual if both are shown). If the price says "Contact Sales", "Custom", or "Talk to us", note that exactly.
   - A brief list of the key features or differentiators for that tier (high-level, not every bullet point)

2. FREE TRIAL: Is a free trial mentioned on this page? If yes, extract:
   - Trial duration (e.g. "14 days", "30 days")
   - Whether a credit card is required to start the trial
   - Any money-back guarantee mentioned
   - Any other trial terms (e.g. "no credit card required", "cancel anytime", feature limitations during trial)

3. FREE TIER: Is there a permanently free tier (not a trial)? If yes, what are its limitations?
```

**Schema:**
```json
{
  "type": "object",
  "properties": {
    "pricing_tiers": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "tier_name": { "type": "string", "description": "Name of the pricing tier/plan" },
          "price_monthly": { "type": "string", "description": "Monthly price, or 'Contact Sales' / 'Custom' / 'Not shown'" },
          "price_annual": { "type": "string", "description": "Annual price or per-month-billed-annually price, or 'Not shown'" },
          "key_features": { "type": "array", "items": { "type": "string" }, "description": "High-level features or differentiators for this tier" }
        }
      },
      "description": "All pricing tiers shown on the page"
    },
    "free_trial": {
      "type": "object",
      "properties": {
        "offered": { "type": "boolean", "description": "True if a free trial is mentioned" },
        "duration": { "type": "string", "description": "Trial duration, or 'Not specified'" },
        "credit_card_required": { "type": "string", "description": "'Yes', 'No', or 'Not specified'" },
        "money_back_guarantee": { "type": "string", "description": "Details of any money-back guarantee, or 'Not mentioned'" },
        "other_terms": { "type": "string", "description": "Any other trial terms mentioned, or 'None'" }
      }
    },
    "free_tier": {
      "type": "object",
      "properties": {
        "exists": { "type": "boolean", "description": "True if a permanently free tier exists (not a trial)" },
        "limitations": { "type": "string", "description": "Key limitations of the free tier, or 'N/A'" }
      }
    }
  }
}
```

---

### Call 1C: Signup Validation

**When to run:** Only if Call 1A returned a `signup_url` AND `appears_self_serve` is true. Skip if no signup URL was found or if the homepage only showed sales-led CTAs.

**Purpose:** Validate whether the signup page is truly self-serve or just a disguised contact form. This is critical because many companies use misleading CTAs (e.g. "Get Started Free" leads to a "Talk to Sales" form).

```
website_intel_extract(
  url: "<signup_url_from_call_1a>",
  mode: "scrape",
  prompt: "<prompt below>",
  schema: <schema below>
)
```

**Prompt:**
```
Analyze this page to determine if it offers TRUE self-serve signup or if it's actually a contact/sales form in disguise.

A TRUE self-serve signup page lets a user create an account immediately by providing their details (email, password, name) and getting instant access — no human interaction required. Signs of true self-serve:
- Fields for email, password, and/or name
- "Create Account" or "Sign Up" submit button
- OAuth options (Sign up with Google, GitHub, etc.)
- Immediate account creation or email verification flow

A DISGUISED SALES FORM looks like a signup page but actually routes the user to a sales conversation. Signs of a disguised sales form:
- Fields asking for company size, budget, use case, "tell us about your needs"
- "Request Access", "Request a Demo", "Get in Touch", "Submit", "Let's Talk" submit button
- "A member of our team will reach out" messaging
- "Schedule a call" or calendar booking widget
- No password field (just collecting lead info)

Also check for:
- Does the page mention "free trial" or "free plan"?
- Is there any indication of how long until the user gets access?
- Are there any terms shown (trial duration, credit card requirement)?

Report your assessment clearly: is this TRUE self-serve signup, a sales/contact form, or ambiguous?
```

**Schema:**
```json
{
  "type": "object",
  "properties": {
    "is_true_self_serve": {
      "type": "boolean",
      "description": "True if the page is a genuine self-serve signup where users can create an account without human interaction. False if it's a contact form, demo request, or sales inquiry form."
    },
    "page_type": {
      "type": "string",
      "description": "One of: 'self-serve signup', 'contact/sales form', 'demo request form', 'waitlist', 'ambiguous'"
    },
    "evidence": {
      "type": "string",
      "description": "Brief description of what you found that led to your assessment. E.g. 'Page has email + password fields with Create Account button' or 'Page asks for company size and use case with Request Demo button'"
    },
    "form_fields_found": {
      "type": "array",
      "items": { "type": "string" },
      "description": "List of form field labels found on the page (e.g. 'Email', 'Password', 'Company Size', 'Job Title')"
    },
    "submit_button_text": {
      "type": "string",
      "description": "The exact text on the form's submit button"
    },
    "mentions_free_trial": { "type": "boolean", "description": "True if the page mentions a free trial" },
    "mentions_free_plan": { "type": "boolean", "description": "True if the page mentions a permanently free plan" },
    "access_timing": {
      "type": "string",
      "description": "Any indication of when the user gets access. E.g. 'Immediate', 'After email verification', 'A team member will contact you within 24 hours', 'Not specified'"
    }
  }
}
```

---

### Combining Results Across Calls

After running the applicable calls, compile the Website Intelligence section of the research report:

**Self-Serve Signup:**
- If Call 1C ran and `is_true_self_serve` is true → "Yes" + describe the signup flow and evidence
- If Call 1C ran and `is_true_self_serve` is false → "No — page appears to be a {page_type}" + describe evidence
- If Call 1C was skipped (no signup URL found) → "No self-serve signup found on homepage"
- If Call 1A or 1C failed → "Could not be determined — website crawl failed"

**Pricing Tiers:**
- If Call 1B ran → list the tiers from the response
- If Call 1B was skipped (no pricing URL) → "No public pricing page found"
- If Call 1B failed → "Could not be determined — pricing page crawl failed"

**Free Trial:**
- If Call 1B ran and `free_trial.offered` is true → report the details
- If Call 1B ran and no trial found → "No free trial mentioned on pricing page"
- If Call 1B was skipped → "No public pricing page found"
- If Call 1C found trial mentions → include those as supplementary evidence

**Product Launches:**
- Use `product_launch_banners` from Call 1A
- If empty → "No recent product launch identified on homepage"
- Cross-reference with Apollo data in Step 7

**CTAs Found:**
- Use the `ctas` array from Call 1A — list each CTA text

**Signal 1 Assessment:**
Signal 1 is a MATCH if ANY of these are true: (a) self-serve signup confirmed in Call 1C, (b) free trial found in Call 1B, (c) product launch banner found in Call 1A.

---

## Section 2: SDR/BDR Job Description Analysis

**Tool:** `hiring-intel` MCP — specifically `extract_job_description` and `search_jobs`

This section uses dedicated hiring-intel MCP tools instead of website crawling. The approach depends on what data you have from the Apollo job postings lookup (SKILL.md Step 2).

### Finding the Job Description

Follow this decision tree:

1. **If you have a job posting URL from Apollo (Step 2) and it is NOT a LinkedIn URL:**
   Call `extract_job_description` with the URL directly.
   ```
   extract_job_description(url: "<job_posting_url>", mode: "single")
   ```
   This works for Greenhouse, Lever, Ashby, Workday, and most ATS platforms. Returns the full page content as markdown.

2. **If the job posting URL from Apollo is a LinkedIn URL (contains `linkedin.com/jobs`):**
   LinkedIn URLs are blocked by the scraper. Instead, search for the listing on other job boards:
   ```
   search_jobs(
     search_term: "<company_name> SDR OR BDR OR Sales Development",
     results_wanted: 5,
     linkedin_fetch_description: true
   )
   ```
   If you find a matching SDR/BDR listing, call `extract_job_description` on that URL.

3. **If no SDR/BDR job posting was found in Apollo (Step 2):**
   Search across job boards directly to check if one exists outside Apollo:
   ```
   search_jobs(
     search_term: "<company_name> SDR OR BDR OR Sales Development",
     results_wanted: 5
   )
   ```
   If results include an SDR/BDR role at the target company, call `extract_job_description` on that URL.

4. **If `search_jobs` also returns nothing:** Report "No SDR/BDR job posting found in Apollo or external job boards."

### Analyzing the Job Description

Once you have the job description text (from `extract_job_description`), analyze it yourself for inbound lead handling intent. This is an INTENT analysis, not a keyword match — do NOT just search for the literal word "inbound".

**What to look for (any of these phrases or similar language indicates inbound handling):**
- "qualify inbound leads" / "qualify marketing leads" / "qualify incoming leads"
- "respond to demo requests" / "handle demo requests" / "manage demo requests"
- "follow up on marketing qualified leads (MQLs)"
- "respond to incoming inquiries" / "handle incoming requests"
- "qualify leads from marketing campaigns"
- "manage inbound pipeline" / "work inbound pipeline"
- "convert website leads" / "engage website visitors"
- "respond to trial signups" / "qualify trial users" / "engage free trial leads"
- "handle chat inquiries" / "respond to live chat"
- "qualify leads generated by marketing" / "work marketing-sourced leads"
- "respond to content downloads" / "follow up on webinar attendees"
- Any similar language implying the role will receive and qualify leads that come TO the company (as opposed to purely outbound prospecting)

**What to extract from the description:**
1. **Job title** — the complete title as listed
2. **Inbound lead handling intent** — true/false based on intent analysis above
3. **Inbound-related phrases** — every sentence or phrase indicating inbound handling responsibility (include phrases even without the literal word "inbound")
4. **Key responsibilities** — list the main responsibilities from the posting
5. **Role type** — one of: "purely outbound", "purely inbound", or "mixed outbound and inbound"

### Reporting Rules

- If you retrieved the description and found inbound lead handling intent → summarize the relevant tasks, list the inbound-related phrases, and note the role type (purely inbound / mixed). Include the date posted if available.
- If you retrieved the description and no inbound intent found → say: **"SDR job listing does not indicate inbound lead handling"**
- If `extract_job_description` failed (page couldn't load) → say: **"SDR job listing could not be retrieved"** and mark signal as "Inconclusive"
- If no SDR/BDR job posting exists anywhere → say: **"No SDR/BDR job posting found in Apollo or external job boards"**

---

## Section 3: LinkedIn Ads

**Tool:** `ad-intel` MCP — specifically `ad_intel_linkedin_search`

This section uses the dedicated ad-intel MCP tool to query the LinkedIn Ad Library directly. No web crawling or URL construction needed — the tool handles the LinkedIn Ad Library API.

### How to Call the Tool

```
ad_intel_linkedin_search(
  account_owner: "<company_name>",
  date_option: "last-30-days"
)
```

**Parameters:**
- `account_owner` (required): The company name as it appears on LinkedIn. Use the company name from Apollo (e.g., "RoboMQ", "ClickIT", "Datadog"). Try the exact name first; if no results, try variations (e.g., full legal name vs. short name).
- `date_option`: Always use `"last-30-days"` for the qualification check.
- Other optional parameters (`keyword`, `countries`, `impressions_min_value`, `impressions_max_value`) — do not use these for the standard qualification check.

### What the Tool Returns

The tool returns structured ad data directly:
- **Total result count** — number of ads found
- **Per-ad details** — advertiser name, ad format, primary text, headline, CTA, impression range, date range, active status, landing page URL, payer info

### What to Extract

From the tool response, extract:
1. **Total active ad count** — the number of ads returned
2. **Ad themes** — categorize each ad by its high-level theme: "product demo promotion", "hiring/recruitment", "thought leadership/content", "event promotion", "product feature highlight", "customer testimonials", "brand awareness", etc.
3. **Ad samples** — for each ad (or a representative sample if many), note the headline/primary text and theme

### Reporting Rules

- If ads found (count > 0) → report the count and list the themes. Note: the qualification signal requires **more than 1 active ad** to count as a match.
- If the tool returned results but count is 0 → say: **"No active LinkedIn ads in the last 30 days"**
- If the tool call failed or returned an error → say: **"LinkedIn Ad Library lookup failed"** and mark signal as "Inconclusive"
- **Note:** The tool may return limited results due to LinkedIn access restrictions. If a warning about limited results is included, note this in the report.
