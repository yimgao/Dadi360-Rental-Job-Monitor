"""Scraper for 168worker.com — restaurant & nail job listings.

Site structure:
  - Category pages:  https://www.168worker.com/list/{list_id}_0/{page_num}
  - Listings in:     <div class="listdata"> blocks
  - Fields:          title <a class="title">, location <span class="fontdark">,
                     salary <div class="salary">, date <div class="timeandare"><p>
  - Detail page:     /page/{id}
  - Pagination:      /list/{list_id}_0/2, /list/{list_id}_0/3, …
"""

from __future__ import annotations

import re
import time
from datetime import datetime, timedelta
from typing import Any

import requests
from bs4 import BeautifulSoup

from ..db import DB
from ..email import EmailSender

DOMAIN = "https://www.168worker.com"
REQ_DELAY = 1.5
MAX_PAGES = 30  # safety cap
DAYS_BACK = 3

CATEGORY_MAP: dict[str, int] = {
    "restaurant_jobs": 1,
    "nail_jobs": 3,
}


class Worker168Scraper:
    """Scrape 168worker.com listings for a given category."""

    SOURCE = "168worker"

    def __init__(
        self,
        category: str,
        config: dict[str, Any],
        db: DB | None = None,
        email: EmailSender | None = None,
    ) -> None:
        self.category = category
        self.cfg = config.get(category, {})
        self.db = db
        self.email = email
        self.list_id = CATEGORY_MAP[category]
        self._session = requests.Session()
        self._session.headers.update(config.get("HEADERS", {}))
        # Site blocks requests without a proper User-Agent
        self._session.headers["User-Agent"] = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )

        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # Override Accept-Encoding: 'br' (Brotli) is not supported by requests
        self._session.headers["Accept-Encoding"] = "gzip, deflate"

    # ── helpers ──────────────────────────────────────────────────────

    def fetch_page(self, page_num: int) -> str | None:
        url = f"{DOMAIN}/list/{self.list_id}_0/{page_num}"
        try:
            resp = self._session.get(url, timeout=15)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException:
            return None

    def parse_page(self, html: str) -> list[dict[str, str]]:
        """Parse a category page → list of listing dicts.

        Each dict: {title, link, author (location), date, salary, source}
        """
        soup = BeautifulSoup(html, "html.parser")
        results: list[dict[str, str]] = []

        for block in soup.find_all("div", class_="listdata"):
            link_el = block.find("a", class_="title")
            if not link_el:
                continue

            title = link_el.get_text(strip=True)
            href = link_el.get("href", "")
            full_link = f"{DOMAIN}{href}" if href.startswith("/") else href

            # location
            location_el = block.find("span", class_="fontdark")
            location = location_el.get_text(strip=True).strip("（）()") if location_el else ""

            # salary
            salary_el = block.find("div", class_="salary")
            salary = salary_el.get_text(strip=True) if salary_el else ""

            # date
            date_el = block.find("div", class_="timeandare")
            post_date = ""
            if date_el:
                p = date_el.find("p")
                if p:
                    post_date = p.get_text(strip=True)

            results.append({
                "title": title,
                "link": full_link,
                "author": location,
                "date": post_date,
                "salary": salary,
            })

        return results

    @staticmethod
    def is_within_days(date_str: str, days: int = DAYS_BACK) -> bool:
        """Check if a date string (YYYY-MM-DD) is within the last N days."""
        if not date_str:
            return False
        try:
            dt = datetime.strptime(date_str.strip(), "%Y-%m-%d")
            return dt >= datetime.now() - timedelta(days=days)
        except ValueError:
            return False

    # ── public ───────────────────────────────────────────────────────

    def scrape(self) -> list[dict[str, str]]:
        """Scrape pages until we find data older than DAYS_BACK."""
        all_listings: list[dict[str, str]] = []
        cutoff_date = (datetime.now() - timedelta(days=DAYS_BACK)).strftime("%Y-%m-%d")

        for page_num in range(1, MAX_PAGES + 1):
            html = self.fetch_page(page_num)
            if not html:
                break

            listings = self.parse_page(html)
            if not listings:
                break  # empty page = no more data

            # filter by date
            for lst in listings:
                if lst["date"] >= cutoff_date:
                    lst["source"] = self.SOURCE
                    all_listings.append(lst)

            # stop if the last listing on this page is too old
            if listings and not self.is_within_days(listings[-1]["date"]):
                break

            time.sleep(REQ_DELAY)

        return all_listings

    def run(self) -> dict[str, Any]:
        start = time.time()
        listings = self.scrape()
        new_count = len(listings)
        elapsed = round(time.time() - start, 2)

        result: dict[str, Any] = {
            "category": self.category,
            "source": self.SOURCE,
            "new_count": new_count,
            "duration_s": elapsed,
            "success": True,
            "error": None,
        }

        if not listings:
            return result

        # persist
        if self.db:
            errors = []
            for lst in listings:
                ok, err = self.db.upsert_listing(self.category, lst, source=self.SOURCE)
                if not ok and err:
                    errors.append(err)
            if errors:
                result["db_errors"] = errors[:5]

        # email
        if self.email:
            subject = f"【168worker-{self.category}】{new_count} 条新匹配 (近3天)"
            body = self._format_email(listings)
            sent, err = self.email.send(subject, body)
            if not sent:
                result["email_error"] = err

        return result

    def _format_email(self, listings: list[dict]) -> str:
        lines = [f"168worker {self.category} — 近3天共 {len(listings)} 条：\n"]
        for i, lst in enumerate(listings, 1):
            lines.append(
                f"{i}. [{lst['date']}] {lst['title']}"
                f"\n    地区: {lst.get('author', '?')}"
                f"\n    薪资: {lst.get('salary', '?')}"
                f"\n    链接: {lst['link']}"
                f"\n"
            )
        lines.append(f"\n抓取时间: {datetime.now():%Y-%m-%d %H:%M:%S}")
        return "\n".join(lines)
