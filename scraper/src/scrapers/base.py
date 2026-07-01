"""Base scraper class — shared scraping logic for all c.dadi360 categories."""

from __future__ import annotations

import re
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime
from typing import Any

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..db import DB
from ..email import EmailSender

DOMAIN = "https://c.dadi360.com"
REQ_DELAY = 2  # seconds between requests
REQ_TIMEOUT = 20  # seconds per request


class BaseScraper(ABC):
    """Abstract base for a forum-scraping category.

    Subclasses override the abstract methods to supply category-specific
    forum IDs, search keywords, and email subject prefixes.
    """

    def __init__(
        self,
        category: str,
        config: dict[str, Any],
        db: DB | None = None,
        email: EmailSender | None = None,
    ) -> None:
        self.category = category
        self.cfg = config.get(category, {})
        self.global_cfg = config
        self.db = db
        self.email = email
        self._session = requests.Session()
        headers = dict(config.get("HEADERS", {}))
        # strip 'br' from Accept-Encoding if brotli is not installed
        if ae := headers.get("Accept-Encoding", ""):
            try:
                import brotli  # noqa: F401
            except ImportError:
                ae = ae.replace("br", "").strip(" ,").strip()
                if ae:
                    headers["Accept-Encoding"] = ae
                else:
                    headers.pop("Accept-Encoding", None)
        self._session.headers.update(headers)
        self._session.verify = False

        # retry adapter: up to 3 attempts, backoff 0.5s
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self._session.mount("https://", adapter)
        self._session.mount("http://", adapter)

        # suppress SSL warnings for c.dadi360.com
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # ── subclass overrides ──────────────────────────────────────────

    @abstractmethod
    def get_search_keywords(self) -> list[str]:
        ...

    @abstractmethod
    def get_email_subject_prefix(self) -> str:
        ...

    @abstractmethod
    def get_forum_id(self) -> int:
        ...

    # ── shared helpers ──────────────────────────────────────────────

    def fetch_html(self, url: str) -> str | None:
        """Return raw HTML, or None on failure."""
        try:
            resp = self._session.get(url, timeout=REQ_TIMEOUT)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException:
            return None

    def parse_listings(self, html: str) -> list[dict[str, str]]:
        """Parse forum page HTML → list of matched listing dicts."""
        soup = BeautifulSoup(html, "html.parser")
        results: list[dict[str, str]] = []
        keywords = self.get_search_keywords()

        for row in soup.find_all("tr", class_="bg_small_yellow"):
            link_el = row.find("a", href=True)
            if not link_el:
                continue

            title = link_el.get_text(strip=True)
            if not any(kw in title for kw in keywords):
                continue

            href = link_el["href"]
            full_link = self._abs_url(href)

            author = ""
            if author_cell := row.find("td", class_="row3"):
                if author_link := author_cell.find("a"):
                    author = author_link.get_text(strip=True)
                else:
                    author = author_cell.get_text(strip=True)

            post_date = self._extract_date(row)

            results.append(
                {"title": title, "link": full_link, "author": author, "date": post_date}
            )

        return results

    def fetch_description(self, url: str) -> str:
        """Fetch full post body from a listing detail page."""
        html = self.fetch_html(url)
        if not html:
            return ""
        soup = BeautifulSoup(html, "html.parser")
        if body := soup.find("div", class_="postbody"):
            return body.get_text(separator="\n", strip=True)
        return ""

    # ── public entry points ─────────────────────────────────────────

    def scrape_all_pages(self, fetch_desc: bool = False) -> tuple[list[dict[str, str]], int]:
        """Scrape every configured page and return matched listings.

        Returns:
            (listings, failed_page_count)

        Args:
            fetch_desc: If True, also fetch the full post body for each
                        listing (adds ~2s per listing). Off by default.
        """
        forum_id = self.get_forum_id()
        max_pages = self.cfg.get("max_pages", 5)
        all_listings: list[dict[str, str]] = []
        failures = 0

        for page in range(1, max_pages + 1):
            url = self._page_url(forum_id, page)
            html = self.fetch_html(url)
            if html:
                all_listings.extend(self.parse_listings(html))
            else:
                failures += 1
            time.sleep(REQ_DELAY)

        if fetch_desc:
            for listing in all_listings:
                listing["description"] = self.fetch_description(listing["link"])
                time.sleep(REQ_DELAY)

        return all_listings, failures

    def run(self) -> dict[str, Any]:
        """Full run cycle: scrape → filter → persist → notify."""
        start = time.time()
        listings, failures = self.scrape_all_pages()
        new_count = len(listings)
        elapsed = round(time.time() - start, 2)

        result: dict[str, Any] = {
            "category": self.category,
            "new_count": new_count,
            "duration_s": elapsed,
            "success": True,
            "error": None,
        }

        # detect real failure: zero results AND all pages failed
        max_pages = self.cfg.get("max_pages", 5)
        if failures >= max_pages:
            result["success"] = False
            result["error"] = f"All {failures}/{max_pages} pages failed to fetch"
            return result
        if failures > 0:
            result["warning"] = f"{failures}/{max_pages} pages failed"

        if not listings:
            return result

        # persist to Supabase
        if self.db:
            errors = []
            for lst in listings:
                ok, err = self.db.upsert_listing(self.category, lst)
                if not ok and err:
                    errors.append(err)
            if errors:
                result["db_errors"] = errors[:5]

        # send email notification
        if self.email:
            subject = f"【{self.get_email_subject_prefix()}】{new_count} 条新匹配"
            body = self._format_email(listings)
            sent, err = self.email.send(subject, body)
            if not sent:
                result["email_error"] = err

        return result

    # ── internal helpers ────────────────────────────────────────────

    @staticmethod
    def _abs_url(href: str) -> str:
        if href.startswith(("http://", "https://")):
            return href
        prefix = "/" if href.startswith("/") else "/"
        return f"{DOMAIN}{prefix}{href}"

    @staticmethod
    def _page_url(forum_id: int, page_num: int) -> str:
        if page_num == 1:
            return f"https://c.dadi360.com/c/forums/show/{forum_id}.page"
        offset = (page_num - 1) * 90
        return f"https://c.dadi360.com/c/forums/show/{offset}/{forum_id}.page"

    @staticmethod
    def _extract_date(row) -> str:
        cells = row.find_all("td")
        for cell in cells:
            text = cell.get_text(strip=True)
            # common forum date formats
            if re.search(r"\d{1,2}/\d{1,2}/\d{4}", text):
                return text
        return ""

    def _format_email(self, listings: list[dict]) -> str:
        lines: list[str] = []
        lines.append(f"共 {len(listings)} 条匹配结果：\n")
        for i, lst in enumerate(listings, 1):
            lines.append(
                f"{i}. [{lst['date']}] {lst['title']}"
                f"\n    作者: {lst.get('author', '?')}"
                f"\n    链接: {lst['link']}"
                f"\n"
            )
        lines.append(f"\n抓取时间: {datetime.now():%Y-%m-%d %H:%M:%S}")
        return "\n".join(lines)
