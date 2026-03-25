"""
scraper.py
==========
Scraping engine for business listing websites.

Architecture:
- BaseScraper: Common logic (requests, retries, headers)
- JustdialScraper: Justdial-specific scraping
  - Primary method: Playwright (handles JavaScript-rendered pages)
  - Fallback method: requests + BeautifulSoup
- ScraperFactory: Returns the right scraper by name

To add a new website later, just create a new class that extends BaseScraper
and register it in ScraperFactory.
"""

import re
import time
import random
import logging
import requests
from bs4 import BeautifulSoup
from typing import Optional

logger = logging.getLogger(__name__)


# ===========================================================
# BASE SCRAPER
# ===========================================================

class BaseScraper:
    """
    Base class for all scrapers.
    Provides: session management, random headers, delay, and retry logic.
    """

    def __init__(self, user_agents: list, min_delay: float = 2,
                 max_delay: float = 5, max_retries: int = 3):
        self.user_agents = user_agents
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.session = requests.Session()

    def get_random_headers(self) -> dict:
        """Return browser-like headers with a random user agent."""
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
        }

    def random_delay(self):
        """Wait a random amount of time between requests."""
        delay = random.uniform(self.min_delay, self.max_delay)
        logger.debug(f"Waiting {delay:.1f}s before next request...")
        time.sleep(delay)

    def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch a URL with retry logic.

        Returns:
            HTML string on success, None on failure.
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Fetching (attempt {attempt}/{self.max_retries}): {url}")
                response = self.session.get(
                    url,
                    headers=self.get_random_headers(),
                    timeout=15
                )

                if response.status_code == 200:
                    logger.debug(f"Success: {len(response.text)} bytes received")
                    return response.text

                elif response.status_code == 403:
                    logger.warning("403 Forbidden - website may be blocking requests. Switching to Playwright...")
                    return None

                elif response.status_code == 429:
                    wait = 30 * attempt
                    logger.warning(f"429 Rate Limited. Waiting {wait}s...")
                    time.sleep(wait)

                else:
                    logger.warning(f"Unexpected status code: {response.status_code}")

            except requests.ConnectionError:
                logger.error(f"Connection error on attempt {attempt}. Check your internet.")
            except requests.Timeout:
                logger.error(f"Timeout on attempt {attempt}.")
            except requests.RequestException as e:
                logger.error(f"Request failed: {e}")

            if attempt < self.max_retries:
                wait = 5 * attempt
                logger.info(f"Retrying in {wait}s...")
                time.sleep(wait)

        logger.error(f"All {self.max_retries} attempts failed for: {url}")
        return None

    def scrape(self, city: str, category: str) -> list:
        """Subclasses must implement this."""
        raise NotImplementedError("Subclasses must implement scrape()")


# ===========================================================
# JUSTDIAL SCRAPER
# ===========================================================

class JustdialScraper(BaseScraper):
    """
    Scraper for JustDial business listings.

    JustDial uses heavy JavaScript rendering, so Playwright is the
    primary scraping method. requests+BeautifulSoup is used as a fallback.

    URL format: https://www.justdial.com/{City}/{Category}
    Example:    https://www.justdial.com/Jaipur/Restaurants
    """

    SOURCE_NAME = "Justdial"

    def build_url(self, city: str, category: str) -> str:
        """
        Build the JustDial search URL.
        Handles spaces by converting to hyphens.
        """
        city_fmt = city.strip().replace(' ', '-').title()
        category_fmt = category.strip().replace(' ', '-').title()
        return f"https://www.justdial.com/{city_fmt}/{category_fmt}"

    def scrape(self, city: str, category: str, max_pages: int = 5) -> list:
        """
        Main entry point. Scrapes multiple pages of results.
        Tries Playwright first, falls back to requests.

        Args:
            city: City name (e.g., "Jaipur")
            category: Business category (e.g., "Restaurants")
            max_pages: Maximum number of result pages to scrape
        Returns:
            List of business record dicts
        """
        base_url = self.build_url(city, category)
        logger.info(f"Target URL: {base_url}")

        all_records = []
        use_playwright = True

        # Check Playwright availability
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.warning("Playwright not installed. Using requests+BeautifulSoup.")
            logger.warning("Install with: pip install playwright && playwright install chromium")
            use_playwright = False

        for page_num in range(1, max_pages + 1):
            # JustDial pagination: page 1 = base URL, page 2+ = /page-2, /page-3, etc.
            if page_num == 1:
                url = base_url
            else:
                url = f"{base_url}/page-{page_num}"

            logger.info(f"--- Page {page_num}/{max_pages}: {url} ---")

            page_records = []

            if use_playwright:
                try:
                    page_records = self._scrape_with_playwright(url)
                    if not page_records and page_num == 1:
                        logger.warning("Playwright returned 0 on page 1. Trying requests...")
                        use_playwright = False
                except Exception as e:
                    logger.warning(f"Playwright error: {e}. Switching to requests...")
                    use_playwright = False

            if not page_records:
                logger.info("Using requests + BeautifulSoup...")
                page_records = self._scrape_with_requests(url)

            if not page_records:
                logger.info(f"No records on page {page_num}. Stopping pagination.")
                break

            all_records.extend(page_records)
            logger.info(f"Page {page_num}: {len(page_records)} records (total: {len(all_records)})")

            # Respect the server — delay between page requests
            if page_num < max_pages:
                self.random_delay()

        logger.info(f"Total scraped: {len(all_records)} records across {page_num} pages")
        return all_records

    # ----------------------------------------------------------
    # PLAYWRIGHT METHOD
    # ----------------------------------------------------------

    def _scrape_with_playwright(self, url: str) -> list:
        """
        Open the page in a real browser and scroll to load all listings.
        This handles JavaScript-rendered content that requests can't see.
        """
        from playwright.sync_api import sync_playwright
        from config import MAX_SCROLLS, SCROLL_PAUSE, HEADLESS, PAGE_TIMEOUT

        records = []

        with sync_playwright() as p:
            # Try Firefox first (less bot detection), fall back to Chromium
            for browser_type_name in ['firefox', 'chromium']:
                try:
                    browser_type = getattr(p, browser_type_name)
                    launch_args = {}
                    if browser_type_name == 'chromium':
                        launch_args['args'] = [
                            '--no-sandbox', '--disable-setuid-sandbox',
                            '--disable-blink-features=AutomationControlled',
                            '--disable-http2', '--disable-dev-shm-usage',
                        ]
                    browser = browser_type.launch(headless=HEADLESS, **launch_args)
                    logger.info(f"Launched {browser_type_name} browser")
                    break
                except Exception as e:
                    logger.warning(f"{browser_type_name} not available: {e}")
                    if browser_type_name == 'chromium':
                        raise RuntimeError("No browser available for Playwright")

            # Create browser context with realistic settings
            context = browser.new_context(
                user_agent=random.choice(self.user_agents),
                viewport={'width': 1280, 'height': 800},
                locale='en-US',
            )

            page = context.new_page()

            try:
                logger.info("Navigating to page...")

                # Navigate — if it times out, still try to extract whatever loaded
                try:
                    page.goto(url, timeout=PAGE_TIMEOUT, wait_until='domcontentloaded')
                except Exception as nav_err:
                    logger.warning(f"Navigation incomplete: {nav_err}")
                    logger.info("Attempting to extract data from partially loaded page...")

                # Wait for JustDial listings to render (React app)
                try:
                    page.wait_for_selector('[class*="resultbox_textbox"]', timeout=15000)
                    logger.info("Listings detected in DOM")
                except Exception:
                    logger.warning("Listings selector not found. Trying with extra wait...")
                    page.wait_for_timeout(5000)

                # Dismiss cookie/popup dialogs if present
                for dismiss_selector in ['button:has-text("Accept")', '.modal-close', '#close-btn', '[aria-label="Close"]']:
                    try:
                        page.click(dismiss_selector, timeout=2000)
                        logger.debug(f"Dismissed popup: {dismiss_selector}")
                        break
                    except Exception:
                        pass

                # Scroll and collect records
                records = self._scroll_and_extract(page, MAX_SCROLLS, SCROLL_PAUSE)

            except Exception as e:
                logger.error(f"Playwright error: {e}")
            finally:
                context.close()
                browser.close()

        return records

    def _scroll_and_extract(self, page, max_scrolls: int, scroll_pause: float) -> list:
        """
        Scroll down the page incrementally, extracting listings after each scroll.
        Stops when no new content loads or max scrolls is reached.
        """
        records = []
        seen_names = set()  # Track names to avoid duplicates during scroll

        for scroll_num in range(max_scrolls):
            # Extract listings from current view
            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')
            current_records = self._parse_listings(soup)

            # Add only NEW records (not seen before)
            new_count = 0
            for record in current_records:
                name_key = record.get('Name', '').lower().strip()
                if name_key and name_key not in seen_names:
                    seen_names.add(name_key)
                    records.append(record)
                    new_count += 1

            logger.info(f"Scroll {scroll_num + 1}/{max_scrolls}: +{new_count} new | {len(records)} total")

            # Check page height before scrolling
            prev_height = page.evaluate("document.body.scrollHeight")

            # Scroll to bottom
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(int(scroll_pause * 1000))

            # Check if page grew (new content loaded)
            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == prev_height:
                logger.info("Page height unchanged - reached end of content")
                break

            # Click "Load More" button if it appears
            for load_more_sel in ['button:has-text("Load More")', 'a:has-text("Load More")', '.load-more-btn', '[class*="loadmore"]']:
                try:
                    btn = page.query_selector(load_more_sel)
                    if btn:
                        btn.click()
                        logger.debug("Clicked 'Load More'")
                        page.wait_for_timeout(2000)
                        break
                except Exception:
                    pass

        return records

    # ----------------------------------------------------------
    # REQUESTS FALLBACK METHOD
    # ----------------------------------------------------------

    def _scrape_with_requests(self, url: str) -> list:
        """
        Fetch page HTML using requests and parse with BeautifulSoup.
        This is the fallback when Playwright is unavailable.
        """
        html = self.fetch_page(url)
        if not html:
            logger.error("requests: Failed to fetch page HTML")
            return []

        soup = BeautifulSoup(html, 'html.parser')
        records = self._parse_listings(soup)
        logger.info(f"requests: Extracted {len(records)} records")
        return records

    # ----------------------------------------------------------
    # HTML PARSING
    # ----------------------------------------------------------

    def _parse_listings(self, soup: BeautifulSoup) -> list:
        """
        Find all business listing containers in the page HTML.

        JustDial DOM structure (verified 2024-2026):
            <main class="results_listing_container">
              <div class="resultbox_listview">
                <div>                              <- listing wrapper
                  <div class="resultbox">
                    <div class="resultbox_info">
                      <div class="resultbox_textbox">   <- we use this as container
                        <h2 class="resultbox_title">
                          <span class="resultbox_title_anchor"> NAME </span>
                        <li class="resultbox_totalrate">  RATING </li>
                        <div class="locatcity">          ADDRESS </div>
                        <span class="callNowAnchor">     PHONE  </span>
        """
        # Primary: find all resultbox_textbox divs (one per listing)
        listings = soup.find_all('div', class_=lambda c: c and 'resultbox_textbox' in c)

        if listings:
            logger.debug(f"Found {len(listings)} listings via resultbox_textbox")
        else:
            # Fallback: find by title class
            title_els = soup.find_all(class_=lambda c: c and 'resultbox_title_anchor' in c)
            listings = [el.find_parent('div', class_=lambda c: c and 'resultbox_textbox' in c)
                        for el in title_els if el.find_parent('div')]
            listings = [l for l in listings if l]
            logger.debug(f"Fallback: found {len(listings)} listings via title_anchor")

        records = []
        for listing in listings:
            try:
                record = self._extract_record(listing)
                if record and record.get('Name'):
                    records.append(record)
            except Exception as e:
                logger.debug(f"Skipping listing: {e}")

        return records

    def _extract_record(self, listing) -> dict:
        """
        Extract all fields from a single resultbox_textbox element.
        Selectors verified against live JustDial HTML (2024-2026).
        """
        record = {'Name': '', 'Phone': '', 'Address': '', 'Rating': '', 'Website': ''}

        # ---- Business Name ----
        # <span class="resultbox_title_anchor ...">Name</span>
        name_el = listing.find(class_=lambda c: c and 'resultbox_title_anchor' in c)
        if not name_el:
            name_el = listing.find('h2', class_=lambda c: c and 'resultbox_title' in c)
        record['Name'] = name_el.get_text(strip=True) if name_el else ''

        # ---- Rating ----
        # <li class="resultbox_totalrate ...">4.2</li>
        rating_el = listing.find('li', class_=lambda c: c and 'resultbox_totalrate' in c)
        record['Rating'] = rating_el.get_text(strip=True) if rating_el else ''

        # ---- Address ----
        # <div class="locatcity ...">Vaishali Nagar, Jaipur</div>
        addr_el = listing.find(class_=lambda c: c and 'locatcity' in c)
        if not addr_el:
            addr_el = listing.find('address')
        record['Address'] = addr_el.get_text(strip=True) if addr_el else ''

        # ---- Phone ----
        # <span class="callNowAnchor">09876543210</span>
        # Also visible as text in div.greenfill_animate.callbutton
        phone_el = listing.find(class_=lambda c: c and 'callNowAnchor' in c)
        if not phone_el:
            phone_el = listing.find(class_=lambda c: c and 'callbutton' in c)
        if phone_el:
            phone_text = phone_el.get_text(strip=True)
            # Validate it looks like a phone number
            import re as _re
            if _re.search(r'\d{7,}', phone_text):
                record['Phone'] = phone_text

        # Check tel: href links as fallback
        if not record['Phone']:
            tel_link = listing.find('a', href=_re.compile(r'^tel:'))
            if tel_link:
                record['Phone'] = tel_link.get('href', '').replace('tel:', '').strip()

        # ---- Website ----
        # Look for links to external sites (not justdial.com)
        for a_tag in listing.find_all('a', href=True):
            href = a_tag.get('href', '')
            if href.startswith('http') and 'justdial.com' not in href:
                record['Website'] = href
                break

        return record

    def _extract_text(self, element, selectors: list) -> str:
        """Try each CSS selector and return text of first match (kept for compatibility)."""
        for selector in selectors:
            try:
                found = element.select_one(selector)
                if found:
                    text = found.get_text(separator=' ', strip=True)
                    if text:
                        return text
            except Exception:
                continue
        return ''


# ===========================================================
# SCRAPER FACTORY
# ===========================================================

class ScraperFactory:
    """
    Factory class to get the right scraper by source name.

    To add a new website:
        1. Create a new scraper class extending BaseScraper
        2. Add it to the SCRAPERS dict below
        3. Use ScraperFactory.get_scraper('new_site', config) to use it
    """

    SCRAPERS = {
        'justdial': JustdialScraper,
        # 'sulekha': SulekhaScraper,     # Add more scrapers here later
        # 'indiamart': IndiaMArtScraper,
    }

    @staticmethod
    def get_scraper(source: str, config) -> BaseScraper:
        """
        Return an initialized scraper instance.

        Args:
            source: Name of the source website (e.g., 'justdial')
            config: The config module with constants
        Returns:
            Initialized BaseScraper subclass
        """
        scraper_class = ScraperFactory.SCRAPERS.get(source.lower())
        if not scraper_class:
            available = list(ScraperFactory.SCRAPERS.keys())
            raise ValueError(f"Unknown scraper '{source}'. Available: {available}")

        return scraper_class(
            user_agents=config.USER_AGENTS,
            min_delay=config.MIN_DELAY,
            max_delay=config.MAX_DELAY,
            max_retries=config.MAX_RETRIES,
        )
