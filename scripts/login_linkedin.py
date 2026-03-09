"""
Open a visible browser window for manual LinkedIn login.

Exit codes:
  0 — login successful, session saved
  1 — login failed or timed out
"""

import asyncio
import os
import sys

_script_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(_script_dir)
_pkg_dir = os.path.join(_root_dir, "packages", "social-intel")


async def manual_login():
    from linkedin_scraper import BrowserManager, wait_for_manual_login, is_logged_in

    browser = BrowserManager(headless=False)
    try:
        await browser.start()
        await browser.page.goto("https://www.linkedin.com/login")
        await wait_for_manual_login(browser.page, timeout=300000)

        logged_in = await is_logged_in(browser.page)
        if logged_in:
            session_file = os.path.join(_pkg_dir, "linkedin_session.json")
            await browser.save_session(session_file)
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception:
        sys.exit(1)
    finally:
        await browser.close()


asyncio.run(manual_login())
