"""Scraper for us168168.com — restaurant & nail job listings (SSR).

Site: Nuxt 3 SPA with server-side rendering for job pages.
- Job listing page:  https://www.us168168.com/job/?page=N
- Each page has 20 items rendered server-side in
  <div class="universal-list-module-item" data-id="...">
- Filter by title keywords for restaurant vs nail.
- Cloudflare-protected; use cloudscraper to bypass.
"""

from __future__ import annotations

import re
import time
from datetime import datetime, timedelta
from typing import Any

from bs4 import BeautifulSoup

from ..db import DB
from ..email import EmailSender

DOMAIN = "https://www.us168168.com"
REQ_DELAY = 1.5
MAX_PAGES = 20
DAYS_BACK = 4


class Us168Scraper:
    """Scrape us168168.com job listings for a given category.

    Categories: 'restaurant_jobs', 'nail_jobs'
    Filtering is done by keyword matching on the title.
    """

    SOURCE = "us168168"

    CATEGORY_KEYWORDS = {
        "restaurant_jobs": [
            "餐馆", "餐厅", "厨师", "炒锅", "炒鑊", "厨房", "企台",
            "服务员", "收银", "帮炒", "油锅", "打杂", "洗碗",
            "寿司", "日餐", "奶茶", "甜品", "面包", "烘焙",
            "送外卖", "外卖",
        ],
        "nail_jobs": [
            "美甲", "指甲", "nail", "甲店", "美甲师", "指甲师",
            "美甲店", "指甲店", "美甲小工", "美甲大工", "美甲中工",
            "美甲学徒", "小工", "大工", "按摩",
        ],
    }

    def __init__(
        self,
        category: str,
        config: dict[str, Any],
        db: DB | None = None,
        email: EmailSender | None = None,
    ) -> None:
        # Strip source prefix if present (e.g. "us168_nail_jobs" → "nail_jobs")
        clean_cat = category.replace("us168_", "").replace("168worker_", "")
        self.category = clean_cat
        self.cfg = config.get(category, {})
        self.db = db
        self.email = email
        self.keywords = self.CATEGORY_KEYWORDS.get(clean_cat, [])

        import cloudscraper
        self._session = cloudscraper.create_scraper()

    # ── helpers ──────────────────────────────────────────────────────

    def fetch_page(self, page_num: int) -> str | None:
        url = f"{DOMAIN}/job/?page={page_num}"
        try:
            resp = self._session.get(url, timeout=20)
            resp.raise_for_status()
            return resp.text
        except Exception:
            return None

    def parse_page(self, html: str) -> list[dict[str, str]]:
        """Parse SSR HTML → list of matching listing dicts."""
        soup = BeautifulSoup(html, "html.parser")
        results: list[dict[str, str]] = []

        for item in soup.find_all("div", class_="universal-list-module-item"):
            data_id = item.get("data-id", "")
            full_text = item.get_text(separator=" ", strip=True)

            # Check if any keyword matches the title
            # The title is the first meaningful text block
            if not any(kw in full_text for kw in self.keywords):
                continue

            # Extract title (first meaningful text)
            title_el = item.find(["p", "span", "div"], class_=lambda c: c and "single-line" in str(c) and "flex-1" not in str(c))
            title = title_el.get_text(strip=True) if title_el else ""

            # Location
            loc_el = item.find("span", class_=lambda c: c and "flex-1" in str(c) and "single-line" in str(c))
            location = loc_el.get_text(strip=True) if loc_el else ""

            # Price/Salary
            price_el = item.find("span", class_=lambda c: c and "text-[20px]" in str(c))
            price = price_el.get_text(strip=True) if price_el else ""

            # Classify tags (job type)
            tags = []
            for tag_el in item.find_all("div", class_="classify-item"):
                tags.append(tag_el.get_text(strip=True))

            # Link to detail page
            link = f"https://www.us168168.com/job/details/{data_id}" if data_id else ""

            results.append({
                "title": title or full_text[:60],
                "link": link,
                "author": location,
                "date": "",  # date is in Nuxt data, not SSR; will use publishTime from API
                "salary": price,
                "tags": ",".join(tags),
                "data_id": data_id,
            })

        return results

    # ── public ───────────────────────────────────────────────────────

    def scrape(self) -> list[dict[str, str]]:
        """Scrape pages until we exhaust recent listings."""
        all_listings: list[dict[str, str]] = []

        for page_num in range(1, MAX_PAGES + 1):
            html = self.fetch_page(page_num)
            if not html:
                break

            listings = self.parse_page(html)
            if not listings:
                # Still continue - maybe no matches on this page
                pass

            for lst in listings:
                lst["source"] = self.SOURCE
                all_listings.append(lst)

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

        if self.db:
            errors = []
            for lst in listings:
                ok, err = self.db.upsert_listing(self.category, lst, source=self.SOURCE)
                if not ok and err:
                    errors.append(err)
            if errors:
                result["db_errors"] = errors[:5]

        if self.email:
            subject = f"【us168-{self.category}】{new_count} 条匹配"
            body = self._format_email(listings)
            sent, err = self.email.send(subject, body)
            if not sent:
                result["email_error"] = err

        return result

    def _format_email(self, listings: list[dict]) -> str:
        lines = [f"us168 {self.category} — 共 {len(listings)} 条匹配：\n"]
        for i, lst in enumerate(listings, 1):
            lines.append(
                f"{i}. {lst['title']}"
                f"\n    地区: {lst.get('author', '?')}"
                f"\n    薪资: {lst.get('salary', '?')}"
                f"\n    链接: {lst['link']}"
                f"\n"
            )
        lines.append(f"\n抓取时间: {datetime.now():%Y-%m-%d %H:%M:%S}")
        return "\n".join(lines)
