"""Central signature database for technology detection.

All patterns, hashes, and mappings live here. Detectors import from this module
so adding a new technology only requires editing this file.
"""

from __future__ import annotations

# ── Header signatures ────────────────────────────────────────────────────────

HEADER_SERVER_MAP: dict[str, dict] = {
    "nginx": {"name": "Nginx", "category": "Web Server", "website": "https://nginx.org"},
    "apache": {"name": "Apache", "category": "Web Server", "website": "https://httpd.apache.org"},
    "microsoft-iis": {"name": "IIS", "category": "Web Server", "website": "https://www.iis.net"},
    "litespeed": {"name": "LiteSpeed", "category": "Web Server", "website": "https://www.litespeedtech.com"},
    "caddy": {"name": "Caddy", "category": "Web Server", "website": "https://caddyserver.com"},
    "cloudflare": {"name": "Cloudflare", "category": "CDN", "website": "https://cloudflare.com"},
    "gunicorn": {"name": "Gunicorn", "category": "Web Server", "website": "https://gunicorn.org"},
    "openresty": {"name": "OpenResty", "category": "Web Server", "website": "https://openresty.org"},
    "google frontend": {"name": "Google Cloud", "category": "Hosting / PaaS", "website": "https://cloud.google.com"},
    "gws": {"name": "Google Web Server", "category": "Web Server", "website": "https://google.com"},
    "envoy": {"name": "Envoy", "category": "Reverse Proxy / Load Balancer", "website": "https://envoyproxy.io"},
}

HEADER_POWERED_BY_MAP: dict[str, dict] = {
    "php": {"name": "PHP", "category": "Programming Language", "website": "https://php.net"},
    "asp.net": {"name": "ASP.NET", "category": "Programming Language", "website": "https://dotnet.microsoft.com/apps/aspnet"},
    "express": {"name": "Express", "category": "JavaScript Framework", "website": "https://expressjs.com"},
    "next.js": {"name": "Next.js", "category": "JavaScript Framework", "website": "https://nextjs.org"},
    "nuxt": {"name": "Nuxt.js", "category": "JavaScript Framework", "website": "https://nuxt.com"},
    "django": {"name": "Django", "category": "JavaScript Framework", "website": "https://djangoproject.com"},
    "rails": {"name": "Ruby on Rails", "category": "JavaScript Framework", "website": "https://rubyonrails.org"},
    "flask": {"name": "Flask", "category": "Programming Language", "website": "https://flask.palletsprojects.com"},
    "kestrel": {"name": "ASP.NET Kestrel", "category": "Web Server", "website": "https://dotnet.microsoft.com"},
}

# Headers whose mere presence signals a specific technology
HEADER_PRESENCE_SIGNATURES: list[dict] = [
    {"header": "cf-ray", "name": "Cloudflare", "category": "CDN", "confidence": 1.0, "website": "https://cloudflare.com"},
    {"header": "cf-cache-status", "name": "Cloudflare", "category": "CDN", "confidence": 1.0, "website": "https://cloudflare.com"},
    {"header": "x-vercel-id", "name": "Vercel", "category": "Hosting / PaaS", "confidence": 1.0, "website": "https://vercel.com"},
    {"header": "x-vercel-cache", "name": "Vercel", "category": "Hosting / PaaS", "confidence": 1.0, "website": "https://vercel.com"},
    {"header": "x-shopify-stage", "name": "Shopify", "category": "E-commerce Platform", "confidence": 1.0, "website": "https://shopify.com"},
    {"header": "x-github-request-id", "name": "GitHub Pages", "category": "Hosting / PaaS", "confidence": 1.0, "website": "https://pages.github.com"},
    {"header": "x-wix-request-id", "name": "Wix", "category": "CMS / Website Builder", "confidence": 1.0, "website": "https://wix.com"},
    {"header": "x-powered-by-plesk", "name": "Plesk", "category": "Hosting / PaaS", "confidence": 0.9, "website": "https://plesk.com"},
]

# Header prefixes
HEADER_PREFIX_SIGNATURES: list[dict] = [
    {"prefix": "x-amz-", "name": "AWS", "category": "Hosting / PaaS", "confidence": 0.8, "website": "https://aws.amazon.com"},
    {"prefix": "x-netlify", "name": "Netlify", "category": "Hosting / PaaS", "confidence": 1.0, "website": "https://netlify.com"},
]

# Via header patterns
HEADER_VIA_MAP: dict[str, dict] = {
    "varnish": {"name": "Varnish", "category": "Reverse Proxy / Load Balancer", "website": "https://varnish-cache.org"},
    "cloudfront": {"name": "AWS CloudFront", "category": "CDN", "website": "https://aws.amazon.com/cloudfront/"},
    "akamai": {"name": "Akamai", "category": "CDN", "website": "https://akamai.com"},
    "fastly": {"name": "Fastly", "category": "CDN", "website": "https://fastly.com"},
    "cloudflare": {"name": "Cloudflare", "category": "CDN", "website": "https://cloudflare.com"},
}

# Security headers (presence = posture signal)
SECURITY_HEADERS: list[dict] = [
    {"header": "strict-transport-security", "name": "HSTS", "category": "Security / WAF"},
    {"header": "x-frame-options", "name": "X-Frame-Options", "category": "Security / WAF"},
    {"header": "x-content-type-options", "name": "X-Content-Type-Options", "category": "Security / WAF"},
    {"header": "x-xss-protection", "name": "X-XSS-Protection", "category": "Security / WAF"},
    {"header": "content-security-policy", "name": "Content Security Policy", "category": "Security / WAF"},
]


# ── HTML / DOM signatures ────────────────────────────────────────────────────

# CMS signatures - (pattern, name, category, confidence, website)
CMS_HTML_SIGNATURES: list[dict] = [
    # WordPress
    {"pattern": "/wp-content/", "name": "WordPress", "category": "CMS / Website Builder", "confidence": 1.0, "website": "https://wordpress.org"},
    {"pattern": "/wp-includes/", "name": "WordPress", "category": "CMS / Website Builder", "confidence": 1.0, "website": "https://wordpress.org"},
    {"pattern": "wp-json", "name": "WordPress", "category": "CMS / Website Builder", "confidence": 0.9, "website": "https://wordpress.org"},
    # Shopify
    {"pattern": "cdn.shopify.com", "name": "Shopify", "category": "E-commerce Platform", "confidence": 1.0, "website": "https://shopify.com"},
    {"pattern": "Shopify.theme", "name": "Shopify", "category": "E-commerce Platform", "confidence": 1.0, "website": "https://shopify.com"},
    {"pattern": "shopify-section", "name": "Shopify", "category": "E-commerce Platform", "confidence": 0.9, "website": "https://shopify.com"},
    # Webflow
    {"pattern": "webflow.com", "name": "Webflow", "category": "CMS / Website Builder", "confidence": 0.9, "website": "https://webflow.com"},
    # Squarespace
    {"pattern": "static.squarespace.com", "name": "Squarespace", "category": "CMS / Website Builder", "confidence": 1.0, "website": "https://squarespace.com"},
    {"pattern": "sqs-", "name": "Squarespace", "category": "CMS / Website Builder", "confidence": 0.7, "website": "https://squarespace.com"},
    # Wix
    {"pattern": "static.wixstatic.com", "name": "Wix", "category": "CMS / Website Builder", "confidence": 1.0, "website": "https://wix.com"},
    # Ghost
    {"pattern": 'content="Ghost"', "name": "Ghost", "category": "CMS / Website Builder", "confidence": 1.0, "website": "https://ghost.org"},
    # Drupal
    {"pattern": "Drupal.settings", "name": "Drupal", "category": "CMS / Website Builder", "confidence": 1.0, "website": "https://drupal.org"},
    {"pattern": "/sites/default/files/", "name": "Drupal", "category": "CMS / Website Builder", "confidence": 0.8, "website": "https://drupal.org"},
    # HubSpot CMS
    {"pattern": "hs-scripts.com", "name": "HubSpot CMS", "category": "CMS / Website Builder", "confidence": 0.8, "website": "https://hubspot.com"},
    {"pattern": "js.hs-scripts.com", "name": "HubSpot CMS", "category": "CMS / Website Builder", "confidence": 0.9, "website": "https://hubspot.com"},
]

# Meta generator patterns
META_GENERATOR_MAP: dict[str, dict] = {
    "wordpress": {"name": "WordPress", "category": "CMS / Website Builder", "website": "https://wordpress.org"},
    "drupal": {"name": "Drupal", "category": "CMS / Website Builder", "website": "https://drupal.org"},
    "joomla": {"name": "Joomla", "category": "CMS / Website Builder", "website": "https://joomla.org"},
    "ghost": {"name": "Ghost", "category": "CMS / Website Builder", "website": "https://ghost.org"},
    "hugo": {"name": "Hugo", "category": "CMS / Website Builder", "website": "https://gohugo.io"},
    "jekyll": {"name": "Jekyll", "category": "CMS / Website Builder", "website": "https://jekyllrb.com"},
    "gatsby": {"name": "Gatsby", "category": "JavaScript Framework", "website": "https://gatsbyjs.com"},
    "next.js": {"name": "Next.js", "category": "JavaScript Framework", "website": "https://nextjs.org"},
    "hexo": {"name": "Hexo", "category": "CMS / Website Builder", "website": "https://hexo.io"},
    "webflow": {"name": "Webflow", "category": "CMS / Website Builder", "website": "https://webflow.com"},
}

# JavaScript framework detection
JS_FRAMEWORK_SIGNATURES: list[dict] = [
    # React / Next.js / Remix
    {"pattern": "react.production.min.js", "name": "React", "category": "JavaScript Framework", "confidence": 1.0, "website": "https://react.dev"},
    {"pattern": "react.development.js", "name": "React", "category": "JavaScript Framework", "confidence": 1.0, "website": "https://react.dev"},
    {"pattern": "react-dom", "name": "React", "category": "JavaScript Framework", "confidence": 0.9, "website": "https://react.dev"},
    {"pattern": "data-reactroot", "name": "React", "category": "JavaScript Framework", "confidence": 1.0, "website": "https://react.dev"},
    {"pattern": "__NEXT_DATA__", "name": "Next.js", "category": "JavaScript Framework", "confidence": 1.0, "website": "https://nextjs.org"},
    {"pattern": "_next/static", "name": "Next.js", "category": "JavaScript Framework", "confidence": 1.0, "website": "https://nextjs.org"},
    {"pattern": "__REMIX_CONTEXT__", "name": "Remix", "category": "JavaScript Framework", "confidence": 1.0, "website": "https://remix.run"},
    # Vue / Nuxt
    {"pattern": "vue.min.js", "name": "Vue.js", "category": "JavaScript Framework", "confidence": 1.0, "website": "https://vuejs.org"},
    {"pattern": "vue.global.prod.js", "name": "Vue.js", "category": "JavaScript Framework", "confidence": 1.0, "website": "https://vuejs.org"},
    {"pattern": "data-v-", "name": "Vue.js", "category": "JavaScript Framework", "confidence": 0.8, "website": "https://vuejs.org"},
    {"pattern": "__NUXT__", "name": "Nuxt.js", "category": "JavaScript Framework", "confidence": 1.0, "website": "https://nuxt.com"},
    {"pattern": "__nuxt", "name": "Nuxt.js", "category": "JavaScript Framework", "confidence": 0.9, "website": "https://nuxt.com"},
    # Angular
    {"pattern": "angular.min.js", "name": "Angular", "category": "JavaScript Framework", "confidence": 1.0, "website": "https://angular.io"},
    {"pattern": "ng-version", "name": "Angular", "category": "JavaScript Framework", "confidence": 1.0, "website": "https://angular.io"},
    {"pattern": 'ng-app="', "name": "AngularJS", "category": "JavaScript Framework", "confidence": 1.0, "website": "https://angularjs.org"},
    # Svelte
    {"pattern": "__svelte", "name": "Svelte", "category": "JavaScript Framework", "confidence": 1.0, "website": "https://svelte.dev"},
    # jQuery
    {"pattern": "jquery.min.js", "name": "jQuery", "category": "JavaScript Framework", "confidence": 1.0, "website": "https://jquery.com"},
    {"pattern": "jquery-migrate", "name": "jQuery", "category": "JavaScript Framework", "confidence": 0.9, "website": "https://jquery.com"},
    # Gatsby
    {"pattern": "___gatsby", "name": "Gatsby", "category": "JavaScript Framework", "confidence": 1.0, "website": "https://gatsbyjs.com"},
    {"pattern": "gatsby-", "name": "Gatsby", "category": "JavaScript Framework", "confidence": 0.7, "website": "https://gatsbyjs.com"},
]

# Analytics & tracking
ANALYTICS_SIGNATURES: list[dict] = [
    {"pattern": "google-analytics.com/analytics.js", "name": "Google Analytics", "category": "Analytics", "confidence": 1.0, "website": "https://analytics.google.com"},
    {"pattern": "gtag/js", "name": "Google Analytics", "category": "Analytics", "confidence": 1.0, "website": "https://analytics.google.com"},
    {"pattern": "ga('create'", "name": "Google Analytics", "category": "Analytics", "confidence": 1.0, "website": "https://analytics.google.com"},
    {"pattern": "googletagmanager.com/gtm.js", "name": "Google Tag Manager", "category": "Tag Manager", "confidence": 1.0, "website": "https://tagmanager.google.com"},
    {"pattern": "GTM-", "name": "Google Tag Manager", "category": "Tag Manager", "confidence": 0.7, "website": "https://tagmanager.google.com"},
    {"pattern": "cdn.segment.com/analytics.js", "name": "Segment", "category": "Analytics", "confidence": 1.0, "website": "https://segment.com"},
    {"pattern": "cdn.segment.com/v1/projects", "name": "Segment", "category": "Analytics", "confidence": 1.0, "website": "https://segment.com"},
    {"pattern": "cdn.mxpnl.com", "name": "Mixpanel", "category": "Analytics", "confidence": 1.0, "website": "https://mixpanel.com"},
    {"pattern": "mixpanel.init", "name": "Mixpanel", "category": "Analytics", "confidence": 1.0, "website": "https://mixpanel.com"},
    {"pattern": "cdn.amplitude.com", "name": "Amplitude", "category": "Analytics", "confidence": 1.0, "website": "https://amplitude.com"},
    {"pattern": "heap-api.com", "name": "Heap", "category": "Analytics", "confidence": 1.0, "website": "https://heap.io"},
    {"pattern": "static.hotjar.com", "name": "Hotjar", "category": "Analytics", "confidence": 1.0, "website": "https://hotjar.com"},
    {"pattern": "fullstory.com/s/fs.js", "name": "FullStory", "category": "Analytics", "confidence": 1.0, "website": "https://fullstory.com"},
    {"pattern": "clarity.ms", "name": "Microsoft Clarity", "category": "Analytics", "confidence": 1.0, "website": "https://clarity.microsoft.com"},
    {"pattern": "plausible.io/js", "name": "Plausible", "category": "Analytics", "confidence": 1.0, "website": "https://plausible.io"},
    {"pattern": "posthog.com", "name": "PostHog", "category": "Analytics", "confidence": 0.9, "website": "https://posthog.com"},
    {"pattern": "app.posthog.com", "name": "PostHog", "category": "Analytics", "confidence": 1.0, "website": "https://posthog.com"},
    {"pattern": "matomo.js", "name": "Matomo", "category": "Analytics", "confidence": 1.0, "website": "https://matomo.org"},
    {"pattern": "piwik.js", "name": "Matomo", "category": "Analytics", "confidence": 0.9, "website": "https://matomo.org"},
]

# Advertising / retargeting
ADVERTISING_SIGNATURES: list[dict] = [
    {"pattern": "connect.facebook.net/en_US/fbevents.js", "name": "Meta Pixel", "category": "Advertising / Retargeting", "confidence": 1.0, "website": "https://facebook.com/business"},
    {"pattern": "fbq('init'", "name": "Meta Pixel", "category": "Advertising / Retargeting", "confidence": 1.0, "website": "https://facebook.com/business"},
    {"pattern": "connect.facebook.net", "name": "Meta Pixel", "category": "Advertising / Retargeting", "confidence": 0.9, "website": "https://facebook.com/business"},
    {"pattern": "snap.licdn.com/li.lms-analytics", "name": "LinkedIn Insight", "category": "Advertising / Retargeting", "confidence": 1.0, "website": "https://business.linkedin.com"},
    {"pattern": "static.ads-twitter.com/uwt.js", "name": "Twitter/X Pixel", "category": "Advertising / Retargeting", "confidence": 1.0, "website": "https://ads.twitter.com"},
    {"pattern": "googleadservices.com/pagead/conversion", "name": "Google Ads", "category": "Advertising / Retargeting", "confidence": 1.0, "website": "https://ads.google.com"},
    {"pattern": "analytics.tiktok.com", "name": "TikTok Pixel", "category": "Advertising / Retargeting", "confidence": 1.0, "website": "https://ads.tiktok.com"},
]

# Chat / support widgets
CHAT_SIGNATURES: list[dict] = [
    {"pattern": "widget.intercom.io", "name": "Intercom", "category": "Chat / Support Widget", "confidence": 1.0, "website": "https://intercom.com"},
    {"pattern": "Intercom(", "name": "Intercom", "category": "Chat / Support Widget", "confidence": 0.9, "website": "https://intercom.com"},
    {"pattern": "drift.com", "name": "Drift", "category": "Chat / Support Widget", "confidence": 0.8, "website": "https://drift.com"},
    {"pattern": "drift.load", "name": "Drift", "category": "Chat / Support Widget", "confidence": 1.0, "website": "https://drift.com"},
    {"pattern": "zopim.com", "name": "Zendesk Chat", "category": "Chat / Support Widget", "confidence": 1.0, "website": "https://zendesk.com"},
    {"pattern": "static.zdassets.com", "name": "Zendesk", "category": "Customer Support Platform", "confidence": 1.0, "website": "https://zendesk.com"},
    {"pattern": "js.usemessages.com", "name": "HubSpot Chat", "category": "Chat / Support Widget", "confidence": 1.0, "website": "https://hubspot.com"},
    {"pattern": "client.crisp.chat", "name": "Crisp", "category": "Chat / Support Widget", "confidence": 1.0, "website": "https://crisp.chat"},
    {"pattern": "cdn.livechatinc.com", "name": "LiveChat", "category": "Chat / Support Widget", "confidence": 1.0, "website": "https://livechat.com"},
    {"pattern": "wchat.freshchat.com", "name": "Freshchat", "category": "Chat / Support Widget", "confidence": 1.0, "website": "https://freshworks.com/live-chat-software"},
    {"pattern": "js.qualified.com", "name": "Qualified", "category": "Chat / Support Widget", "confidence": 1.0, "website": "https://qualified.com"},
    {"pattern": "code.tidio.co", "name": "Tidio", "category": "Chat / Support Widget", "confidence": 1.0, "website": "https://tidio.com"},
]

# A/B testing & feature flags
AB_TESTING_SIGNATURES: list[dict] = [
    {"pattern": "cdn.optimizely.com", "name": "Optimizely", "category": "A/B Testing / Feature Flags", "confidence": 1.0, "website": "https://optimizely.com"},
    {"pattern": "app.launchdarkly.com", "name": "LaunchDarkly", "category": "A/B Testing / Feature Flags", "confidence": 1.0, "website": "https://launchdarkly.com"},
    {"pattern": "dev.visualwebsiteoptimizer.com", "name": "VWO", "category": "A/B Testing / Feature Flags", "confidence": 1.0, "website": "https://vwo.com"},
    {"pattern": "optimize.google.com", "name": "Google Optimize", "category": "A/B Testing / Feature Flags", "confidence": 1.0, "website": "https://optimize.google.com"},
    {"pattern": "cdn.split.io", "name": "Split.io", "category": "A/B Testing / Feature Flags", "confidence": 1.0, "website": "https://split.io"},
    {"pattern": "statsig", "name": "Statsig", "category": "A/B Testing / Feature Flags", "confidence": 0.7, "website": "https://statsig.com"},
]

# Email / marketing automation
MARKETING_SIGNATURES: list[dict] = [
    {"pattern": "js.hsforms.net", "name": "HubSpot", "category": "Marketing Automation", "subcategory": "Forms & Tracking", "confidence": 1.0, "website": "https://hubspot.com"},
    {"pattern": "hbspt.forms.create", "name": "HubSpot", "category": "Marketing Automation", "subcategory": "Forms & Tracking", "confidence": 1.0, "website": "https://hubspot.com"},
    {"pattern": "js.hs-scripts.com", "name": "HubSpot", "category": "Marketing Automation", "subcategory": "Forms & Tracking", "confidence": 1.0, "website": "https://hubspot.com"},
    {"pattern": "hs-analytics.net", "name": "HubSpot", "category": "Marketing Automation", "subcategory": "Analytics", "confidence": 1.0, "website": "https://hubspot.com"},
    {"pattern": "hscollectedforms.net", "name": "HubSpot", "category": "Marketing Automation", "subcategory": "Forms & Tracking", "confidence": 1.0, "website": "https://hubspot.com"},
    {"pattern": "hs-banner.com", "name": "HubSpot", "category": "Marketing Automation", "subcategory": "Consent", "confidence": 1.0, "website": "https://hubspot.com"},
    {"pattern": "munchkin.marketo.net", "name": "Marketo", "category": "Marketing Automation", "confidence": 1.0, "website": "https://marketo.com"},
    {"pattern": "mktoForms2", "name": "Marketo", "category": "Marketing Automation", "confidence": 1.0, "website": "https://marketo.com"},
    {"pattern": "pi.pardot.com", "name": "Pardot", "category": "Marketing Automation", "confidence": 1.0, "website": "https://pardot.com"},
    {"pattern": "piAId", "name": "Pardot", "category": "Marketing Automation", "confidence": 0.9, "website": "https://pardot.com"},
    {"pattern": "chimpstatic.com", "name": "Mailchimp", "category": "Marketing Automation", "confidence": 1.0, "website": "https://mailchimp.com"},
    {"pattern": "mc.js", "name": "Mailchimp", "category": "Marketing Automation", "confidence": 0.6, "website": "https://mailchimp.com"},
    {"pattern": "trackcmp.net", "name": "ActiveCampaign", "category": "Marketing Automation", "confidence": 1.0, "website": "https://activecampaign.com"},
    {"pattern": "static.klaviyo.com", "name": "Klaviyo", "category": "Marketing Automation", "confidence": 1.0, "website": "https://klaviyo.com"},
    {"pattern": "track.customer.io", "name": "Customer.io", "category": "Marketing Automation", "confidence": 1.0, "website": "https://customer.io"},
    {"pattern": "sdk.iad-01.braze.com", "name": "Braze", "category": "Marketing Automation", "confidence": 1.0, "website": "https://braze.com"},
    {"pattern": "braze.com/sdk", "name": "Braze", "category": "Marketing Automation", "confidence": 0.9, "website": "https://braze.com"},
]

# CDN / asset delivery
CDN_SIGNATURES: list[dict] = [
    {"pattern": "cdnjs.cloudflare.com", "name": "Cloudflare CDN", "category": "CDN", "confidence": 0.7, "website": "https://cdnjs.com"},
    {"pattern": "cdn.jsdelivr.net", "name": "jsDelivr", "category": "CDN", "confidence": 0.7, "website": "https://jsdelivr.com"},
    {"pattern": "unpkg.com", "name": "unpkg", "category": "CDN", "confidence": 0.7, "website": "https://unpkg.com"},
    {"pattern": "cloudfront.net", "name": "AWS CloudFront", "category": "CDN", "confidence": 0.8, "website": "https://aws.amazon.com/cloudfront/"},
    {"pattern": "fastly.net", "name": "Fastly", "category": "CDN", "confidence": 0.8, "website": "https://fastly.com"},
    {"pattern": "akamaized.net", "name": "Akamai", "category": "CDN", "confidence": 0.8, "website": "https://akamai.com"},
    {"pattern": "akamai.net", "name": "Akamai", "category": "CDN", "confidence": 0.8, "website": "https://akamai.com"},
]

# Font services
FONT_SIGNATURES: list[dict] = [
    {"pattern": "fonts.googleapis.com", "name": "Google Fonts", "category": "Font Service", "confidence": 1.0, "website": "https://fonts.google.com"},
    {"pattern": "use.typekit.net", "name": "Adobe Fonts", "category": "Font Service", "confidence": 1.0, "website": "https://fonts.adobe.com"},
    {"pattern": "fontawesome.com", "name": "Font Awesome", "category": "Font Service", "confidence": 0.9, "website": "https://fontawesome.com"},
    {"pattern": "fa-", "name": "Font Awesome", "category": "Font Service", "confidence": 0.4, "website": "https://fontawesome.com"},
]

# Payment / e-commerce
PAYMENT_SIGNATURES: list[dict] = [
    {"pattern": "js.stripe.com", "name": "Stripe", "category": "Payment Processing", "confidence": 1.0, "website": "https://stripe.com"},
    {"pattern": "paypal.com/sdk", "name": "PayPal", "category": "Payment Processing", "confidence": 1.0, "website": "https://paypal.com"},
    {"pattern": "js.braintreegateway.com", "name": "Braintree", "category": "Payment Processing", "confidence": 1.0, "website": "https://braintreepayments.com"},
    {"pattern": "squareup.com", "name": "Square", "category": "Payment Processing", "confidence": 0.8, "website": "https://squareup.com"},
]

# Consent / privacy
CONSENT_SIGNATURES: list[dict] = [
    {"pattern": "cdn.cookielaw.org", "name": "OneTrust", "category": "Consent / Privacy", "confidence": 1.0, "website": "https://onetrust.com"},
    {"pattern": "onetrust.com", "name": "OneTrust", "category": "Consent / Privacy", "confidence": 0.9, "website": "https://onetrust.com"},
    {"pattern": "consent.cookiebot.com", "name": "Cookiebot", "category": "Consent / Privacy", "confidence": 1.0, "website": "https://cookiebot.com"},
    {"pattern": "consent.trustarc.com", "name": "TrustArc", "category": "Consent / Privacy", "confidence": 1.0, "website": "https://trustarc.com"},
    {"pattern": "osano.com", "name": "Osano", "category": "Consent / Privacy", "confidence": 0.9, "website": "https://osano.com"},
]

# All HTML-scanned signature lists combined for easy iteration
ALL_HTML_SIGNATURES: list[list[dict]] = [
    CMS_HTML_SIGNATURES,
    JS_FRAMEWORK_SIGNATURES,
    ANALYTICS_SIGNATURES,
    ADVERTISING_SIGNATURES,
    CHAT_SIGNATURES,
    AB_TESTING_SIGNATURES,
    MARKETING_SIGNATURES,
    CDN_SIGNATURES,
    FONT_SIGNATURES,
    PAYMENT_SIGNATURES,
    CONSENT_SIGNATURES,
]


# ── DNS signatures ────────────────────────────────────────────────────────────

MX_PROVIDER_MAP: dict[str, dict] = {
    "google.com": {"name": "Google Workspace", "category": "Email Provider", "website": "https://workspace.google.com"},
    "googlemail.com": {"name": "Google Workspace", "category": "Email Provider", "website": "https://workspace.google.com"},
    "outlook.com": {"name": "Microsoft 365", "category": "Email Provider", "website": "https://microsoft.com/microsoft-365"},
    "microsoft.com": {"name": "Microsoft 365", "category": "Email Provider", "website": "https://microsoft.com/microsoft-365"},
    "pphosted.com": {"name": "Proofpoint", "category": "Security / WAF", "subcategory": "Email Security", "website": "https://proofpoint.com"},
    "mimecast.com": {"name": "Mimecast", "category": "Security / WAF", "subcategory": "Email Security", "website": "https://mimecast.com"},
    "barracuda": {"name": "Barracuda", "category": "Security / WAF", "subcategory": "Email Security", "website": "https://barracuda.com"},
    "zoho.com": {"name": "Zoho Mail", "category": "Email Provider", "website": "https://zoho.com/mail"},
}

# SPF include patterns in TXT records
TXT_SPF_MAP: dict[str, dict] = {
    "_spf.google.com": {"name": "Google Workspace", "category": "Email Provider", "website": "https://workspace.google.com"},
    "spf.protection.outlook.com": {"name": "Microsoft 365", "category": "Email Provider", "website": "https://microsoft.com/microsoft-365"},
    "sendgrid.net": {"name": "SendGrid", "category": "Email Sending Service", "website": "https://sendgrid.com"},
    "amazonses.com": {"name": "Amazon SES", "category": "Email Sending Service", "website": "https://aws.amazon.com/ses/"},
    "mailgun.org": {"name": "Mailgun", "category": "Email Sending Service", "website": "https://mailgun.com"},
    "mandrillapp.com": {"name": "Mandrill", "category": "Email Sending Service", "website": "https://mandrillapp.com"},
    "postmarkapp.com": {"name": "Postmark", "category": "Email Sending Service", "website": "https://postmarkapp.com"},
    "servers.mcsv.net": {"name": "Mailchimp", "category": "Email Sending Service", "website": "https://mailchimp.com"},
    "mktomail.com": {"name": "Marketo", "category": "Marketing Automation", "website": "https://marketo.com"},
    "hubspotemail.net": {"name": "HubSpot", "category": "Marketing Automation", "subcategory": "Email Sending", "website": "https://hubspot.com"},
    "zendesk.com": {"name": "Zendesk", "category": "Customer Support Platform", "website": "https://zendesk.com"},
    "freshdesk.com": {"name": "Freshdesk", "category": "Customer Support Platform", "website": "https://freshworks.com/freshdesk"},
}

# Domain verification TXT record prefixes
TXT_VERIFICATION_MAP: dict[str, dict] = {
    "google-site-verification=": {"name": "Google Search Console", "category": "SEO", "confidence": 0.5, "website": "https://search.google.com/search-console"},
    "MS=": {"name": "Microsoft 365", "category": "Email Provider", "confidence": 0.6, "website": "https://microsoft.com/microsoft-365"},
    "facebook-domain-verification=": {"name": "Meta Business", "category": "Advertising / Retargeting", "confidence": 0.5, "website": "https://business.facebook.com"},
    "atlassian-domain-verification=": {"name": "Atlassian", "category": "CRM", "subcategory": "Project Management", "confidence": 0.5, "website": "https://atlassian.com"},
    "docusign=": {"name": "DocuSign", "category": "Marketing Automation", "subcategory": "E-Signature", "confidence": 0.5, "website": "https://docusign.com"},
    "stripe-verification=": {"name": "Stripe", "category": "Payment Processing", "confidence": 0.5, "website": "https://stripe.com"},
    "slack-domain-verification=": {"name": "Slack", "category": "CRM", "subcategory": "Communication", "confidence": 0.5, "website": "https://slack.com"},
}

# CNAME target patterns
CNAME_TARGET_MAP: dict[str, dict] = {
    "github.io": {"name": "GitHub Pages", "category": "Hosting / PaaS", "website": "https://pages.github.com"},
    "netlify.app": {"name": "Netlify", "category": "Hosting / PaaS", "website": "https://netlify.com"},
    "netlify.com": {"name": "Netlify", "category": "Hosting / PaaS", "website": "https://netlify.com"},
    "vercel-dns.com": {"name": "Vercel", "category": "Hosting / PaaS", "website": "https://vercel.com"},
    "shopify.com": {"name": "Shopify", "category": "E-commerce Platform", "website": "https://shopify.com"},
    "zendesk.com": {"name": "Zendesk", "category": "Customer Support Platform", "website": "https://zendesk.com"},
    "freshdesk.com": {"name": "Freshdesk", "category": "Customer Support Platform", "website": "https://freshworks.com/freshdesk"},
    "ghost.io": {"name": "Ghost Pro", "category": "CMS / Website Builder", "website": "https://ghost.org"},
    "hubspot.net": {"name": "HubSpot CMS", "category": "CMS / Website Builder", "website": "https://hubspot.com"},
    "herokuapp.com": {"name": "Heroku", "category": "Hosting / PaaS", "website": "https://heroku.com"},
    "wpengine.com": {"name": "WP Engine", "category": "Hosting / PaaS", "website": "https://wpengine.com"},
    "squarespace.com": {"name": "Squarespace", "category": "CMS / Website Builder", "website": "https://squarespace.com"},
    "statuspage.io": {"name": "Statuspage", "category": "Performance / Monitoring", "website": "https://statuspage.io"},
    "status.io": {"name": "Status.io", "category": "Performance / Monitoring", "website": "https://status.io"},
    "fastly.net": {"name": "Fastly", "category": "CDN", "website": "https://fastly.com"},
    "cloudfront.net": {"name": "AWS CloudFront", "category": "CDN", "website": "https://aws.amazon.com/cloudfront/"},
}

# NS record patterns
NS_PROVIDER_MAP: dict[str, dict] = {
    "cloudflare.com": {"name": "Cloudflare DNS", "category": "DNS Provider", "website": "https://cloudflare.com"},
    "awsdns": {"name": "AWS Route 53", "category": "DNS Provider", "website": "https://aws.amazon.com/route53/"},
    "googledomains.com": {"name": "Google Domains", "category": "DNS Provider", "website": "https://domains.google.com"},
    "google.com": {"name": "Google Cloud DNS", "category": "DNS Provider", "website": "https://cloud.google.com/dns"},
    "domaincontrol.com": {"name": "GoDaddy DNS", "category": "DNS Provider", "website": "https://godaddy.com"},
    "registrar-servers.com": {"name": "Namecheap DNS", "category": "DNS Provider", "website": "https://namecheap.com"},
    "nsone.net": {"name": "NS1", "category": "DNS Provider", "website": "https://ns1.com"},
    "dynect.net": {"name": "Dyn (Oracle)", "category": "DNS Provider", "website": "https://dyn.com"},
    "digitalocean.com": {"name": "DigitalOcean DNS", "category": "DNS Provider", "website": "https://digitalocean.com"},
    "hetzner.com": {"name": "Hetzner DNS", "category": "DNS Provider", "website": "https://hetzner.com"},
}

# Subdomains to probe for CNAME records
CNAME_SUBDOMAINS: list[str] = [
    "www", "mail", "cdn", "api", "app", "blog", "docs",
    "status", "support", "help", "shop", "store",
]


# ── SSL certificate signatures ──────────────────────────────────────────────

SSL_ISSUER_MAP: dict[str, dict] = {
    "let's encrypt": {"name": "Let's Encrypt", "category": "SSL / Certificate Authority", "confidence": 0.8, "website": "https://letsencrypt.org"},
    "digicert": {"name": "DigiCert", "category": "SSL / Certificate Authority", "confidence": 0.8, "website": "https://digicert.com"},
    "sectigo": {"name": "Sectigo", "category": "SSL / Certificate Authority", "confidence": 0.8, "website": "https://sectigo.com"},
    "comodo": {"name": "Sectigo (Comodo)", "category": "SSL / Certificate Authority", "confidence": 0.8, "website": "https://sectigo.com"},
    "cloudflare": {"name": "Cloudflare", "category": "CDN", "subcategory": "SSL", "confidence": 0.9, "website": "https://cloudflare.com"},
    "amazon": {"name": "AWS ACM", "category": "SSL / Certificate Authority", "confidence": 0.8, "website": "https://aws.amazon.com/certificate-manager/"},
    "globalsign": {"name": "GlobalSign", "category": "SSL / Certificate Authority", "confidence": 0.8, "website": "https://globalsign.com"},
    "godaddy": {"name": "GoDaddy SSL", "category": "SSL / Certificate Authority", "confidence": 0.8, "website": "https://godaddy.com"},
    "google trust services": {"name": "Google Trust Services", "category": "SSL / Certificate Authority", "confidence": 0.8, "website": "https://pki.goog"},
}


# ── robots.txt signatures ───────────────────────────────────────────────────

ROBOTS_SIGNATURES: list[dict] = [
    {"pattern": "/wp-admin", "name": "WordPress", "category": "CMS / Website Builder", "confidence": 0.9, "website": "https://wordpress.org"},
    {"pattern": "/ghost/", "name": "Ghost", "category": "CMS / Website Builder", "confidence": 0.9, "website": "https://ghost.org"},
    {"pattern": "/admin/shopify/", "name": "Shopify", "category": "E-commerce Platform", "confidence": 0.9, "website": "https://shopify.com"},
    {"pattern": "/cart", "name": "E-commerce Platform", "category": "E-commerce Platform", "confidence": 0.4},
    {"pattern": "Yoast SEO", "name": "Yoast SEO", "category": "SEO", "confidence": 1.0, "website": "https://yoast.com"},
]

SITEMAP_SIGNATURES: list[dict] = [
    {"pattern": 'generator="WordPress"', "name": "WordPress", "category": "CMS / Website Builder", "confidence": 1.0, "website": "https://wordpress.org"},
    {"pattern": "Yoast SEO plugin", "name": "Yoast SEO", "category": "SEO", "confidence": 1.0, "website": "https://yoast.com"},
    {"pattern": "hubspot.com", "name": "HubSpot", "category": "Marketing Automation", "confidence": 0.7, "website": "https://hubspot.com"},
]


# ── Cookie signatures ────────────────────────────────────────────────────────

COOKIE_SIGNATURES: dict[str, dict] = {
    "__hstc": {"name": "HubSpot", "category": "Marketing Automation", "confidence": 1.0, "website": "https://hubspot.com"},
    "hubspotutk": {"name": "HubSpot", "category": "Marketing Automation", "confidence": 1.0, "website": "https://hubspot.com"},
    "__hssc": {"name": "HubSpot", "category": "Marketing Automation", "confidence": 1.0, "website": "https://hubspot.com"},
    "_mkto_trk": {"name": "Marketo", "category": "Marketing Automation", "confidence": 1.0, "website": "https://marketo.com"},
    "_ga": {"name": "Google Analytics", "category": "Analytics", "confidence": 1.0, "website": "https://analytics.google.com"},
    "_gid": {"name": "Google Analytics", "category": "Analytics", "confidence": 1.0, "website": "https://analytics.google.com"},
    "_gat": {"name": "Google Analytics", "category": "Analytics", "confidence": 0.9, "website": "https://analytics.google.com"},
    "_fbp": {"name": "Meta Pixel", "category": "Advertising / Retargeting", "confidence": 1.0, "website": "https://facebook.com/business"},
    "_fbc": {"name": "Meta Pixel", "category": "Advertising / Retargeting", "confidence": 1.0, "website": "https://facebook.com/business"},
    "PHPSESSID": {"name": "PHP", "category": "Programming Language", "confidence": 0.9, "website": "https://php.net"},
    "ASP.NET_SessionId": {"name": "ASP.NET", "category": "Programming Language", "confidence": 1.0, "website": "https://dotnet.microsoft.com"},
    "JSESSIONID": {"name": "Java", "category": "Programming Language", "confidence": 0.9, "website": "https://java.com"},
    "connect.sid": {"name": "Express.js", "category": "JavaScript Framework", "confidence": 0.8, "website": "https://expressjs.com"},
    "laravel_session": {"name": "Laravel", "category": "JavaScript Framework", "confidence": 1.0, "website": "https://laravel.com"},
    "__cf_bm": {"name": "Cloudflare Bot Management", "category": "Security / WAF", "confidence": 1.0, "website": "https://cloudflare.com"},
    "cf_clearance": {"name": "Cloudflare", "category": "Security / WAF", "confidence": 1.0, "website": "https://cloudflare.com"},
    "optimizelyEndUserId": {"name": "Optimizely", "category": "A/B Testing / Feature Flags", "confidence": 1.0, "website": "https://optimizely.com"},
    "_dc_gtm_": {"name": "Google Tag Manager", "category": "Tag Manager", "confidence": 0.9, "website": "https://tagmanager.google.com"},
}

# Cookie prefix patterns (for partial matches)
COOKIE_PREFIX_SIGNATURES: dict[str, dict] = {
    "pardot": {"name": "Pardot", "category": "Marketing Automation", "confidence": 0.9, "website": "https://pardot.com"},
    "visitor_id": {"name": "Pardot", "category": "Marketing Automation", "confidence": 0.7, "website": "https://pardot.com"},
    "_rails_session": {"name": "Ruby on Rails", "category": "Programming Language", "confidence": 1.0, "website": "https://rubyonrails.org"},
    "_session_id": {"name": "Ruby on Rails", "category": "Programming Language", "confidence": 0.5, "website": "https://rubyonrails.org"},
    "wp-settings-": {"name": "WordPress", "category": "CMS / Website Builder", "confidence": 1.0, "website": "https://wordpress.org"},
    "_shopify_": {"name": "Shopify", "category": "E-commerce Platform", "confidence": 1.0, "website": "https://shopify.com"},
    "__stripe_": {"name": "Stripe", "category": "Payment Processing", "confidence": 1.0, "website": "https://stripe.com"},
    "intercom-": {"name": "Intercom", "category": "Chat / Support Widget", "confidence": 1.0, "website": "https://intercom.com"},
    "crisp-client": {"name": "Crisp", "category": "Chat / Support Widget", "confidence": 1.0, "website": "https://crisp.chat"},
    "ajs_": {"name": "Segment", "category": "Analytics", "confidence": 0.9, "website": "https://segment.com"},
}


# ── Favicon hash signatures ─────────────────────────────────────────────────

# MD5 hashes of known default favicons
FAVICON_HASH_MAP: dict[str, dict] = {
    "d41d8cd98f00b204e9800998ecf8427e": {"name": "Empty Favicon", "category": "Web Server", "confidence": 0.3},
    # WordPress default favicon
    "b25e29432b278e3e33919be498c76a2c": {"name": "WordPress", "category": "CMS / Website Builder", "confidence": 0.7, "website": "https://wordpress.org"},
    # Shopify default favicon
    "e8dbe587a4e1db98da0421a5e0b2c98e": {"name": "Shopify", "category": "E-commerce Platform", "confidence": 0.7, "website": "https://shopify.com"},
    # Apache default
    "3e3f85817f89bb70b546c3c9ff2fe26e": {"name": "Apache", "category": "Web Server", "confidence": 0.6, "website": "https://httpd.apache.org"},
    # Nginx default
    "2c7d3b7c0e85a33c45d1e3ff7b4b2a7f": {"name": "Nginx", "category": "Web Server", "confidence": 0.6, "website": "https://nginx.org"},
}
