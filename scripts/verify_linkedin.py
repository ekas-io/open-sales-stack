"""
Verify LinkedIn credentials by attempting a programmatic login.

Exit codes:
  0 — login successful
  1 — login failed (bad credentials, captcha, etc.)
  2 — missing credentials
"""

import asyncio
import os
import sys

# Add packages to path so linkedin_scraper is importable
_script_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(_script_dir)
_pkg_dir = os.path.join(_root_dir, "packages", "social-intel")

from dotenv import load_dotenv

load_dotenv(os.path.join(_pkg_dir, ".env"))
load_dotenv(os.path.join(_root_dir, ".env"))

email = os.getenv("LINKEDIN_EMAIL", "")
password = os.getenv("LINKEDIN_PASSWORD", "")

if not email or not password:
    sys.exit(2)


async def verify():
    from linkedin_scraper import BrowserManager, login_with_credentials, is_logged_in

    browser = BrowserManager(headless=True)
    try:
        await browser.start()
        await login_with_credentials(browser.page, email=email, password=password)

        logged_in = await is_logged_in(browser.page)
        if logged_in:
            # Save the session so future runs don't need to re-login
            session_file = os.path.join(_pkg_dir, "linkedin_session.json")
            await browser.save_session(session_file)
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception:
        sys.exit(1)
    finally:
        await browser.close()


asyncio.run(verify())
