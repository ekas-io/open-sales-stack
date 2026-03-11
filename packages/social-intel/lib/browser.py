"""LinkedIn browser authentication and session management for social-intel."""

import logging
import os
import subprocess
import sys

logger = logging.getLogger("social-intel")

_pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION_FILE = os.path.join(_pkg_dir, "linkedin_session.json")


def ensure_dependencies():
    """Check and install linkedin-scraper and playwright if missing."""
    try:
        import linkedin_scraper  # noqa: F401
        logger.info("linkedin-scraper is installed")
    except ImportError:
        logger.info("linkedin-scraper not found, installing...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "linkedin-scraper>=3.0"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logger.info("linkedin-scraper installed successfully")

    try:
        subprocess.check_call(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        logger.warning("Failed to install playwright chromium browser")


async def _login_with_session(BrowserManager) -> object:
    """Reuse a saved LinkedIn session."""
    browser = BrowserManager(headless=True)
    await browser.start()
    await browser.load_session(SESSION_FILE)
    return browser


async def _login_with_credentials(BrowserManager, email: str, password: str) -> object:
    """Login programmatically using LINKEDIN_EMAIL / LINKEDIN_PASSWORD."""
    from linkedin_scraper import login_with_credentials

    browser = BrowserManager(headless=True)
    await browser.start()
    await login_with_credentials(browser.page, email=email, password=password)
    await browser.save_session(SESSION_FILE)
    return browser


async def _login_manual(BrowserManager) -> object:
    """Open a visible browser and wait for the user to log in manually."""
    from linkedin_scraper import wait_for_manual_login

    browser = BrowserManager(headless=False)
    await browser.start()
    await browser.page.goto("https://www.linkedin.com/login")
    await wait_for_manual_login(browser.page, timeout=300000)
    await browser.save_session(SESSION_FILE)
    return browser


async def get_authenticated_browser():
    """Return an authenticated BrowserManager instance.

    Priority: saved session → env credentials → manual browser login.
    """
    from linkedin_scraper import BrowserManager

    if os.path.exists(SESSION_FILE):
        logger.info("Reusing saved LinkedIn session")
        return await _login_with_session(BrowserManager)

    email = os.getenv("LINKEDIN_EMAIL", "")
    password = os.getenv("LINKEDIN_PASSWORD", "")
    if email and password:
        logger.info("Logging in with LINKEDIN_EMAIL / LINKEDIN_PASSWORD")
        return await _login_with_credentials(BrowserManager, email, password)

    logger.info("No credentials found — opening browser for manual login")
    return await _login_manual(BrowserManager)
