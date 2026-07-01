"""Scraper for us168168.com — restaurant & nail job listings (SSR).

Site: Nuxt 3 SPA with server-side rendering for job pages.
- Job listing page:  https://www.us168168.com/job/?page=N
- Each page has 20 items rendered server-side in
  <div class="universal-list-module-item" data-id="...">
- Filter by title/keywords for restaurant vs nail.
- Cloudflare-protected; use cloudscraper to bypass.
- Incremental: pre-loads existing links to skip DB writes for dupes.
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

# Expanded keyword lists for better classification
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "restaurant_jobs": [
        "餐馆", "餐厅", "厨师", "炒锅", "炒鑊", "厨房", "企台",
        "服务员", "收银", "帮炒", "油锅", "打杂", "洗碗",
        "寿司", "日餐", "奶茶", "甜品", "面包", "烘焙",
        "送外卖", "外卖", "熟手炒", "厨房工", "快餐",
        "饺子", "面点", "烧烤", "火锅", "后厨", "前厅",
    ],
    "nail_jobs": [
        "美甲", "指甲", "nail", "甲店", "美甲师", "指甲师",
        "美甲店", "指甲店", "小工", "大工", "中工",
        "按摩", "美甲学徒", "美甲助理", "美甲师傅",
        "指甲工", "甲工",
    ],
}


class Us168Scraper:
    """Scrape us168168.com job listings for a given category."""

    SOURCE = "us168168"

    def __init__(
        self,
        category: str,
        config: dict[str, Any],
        db: DB | None = None,
        email: EmailSender | None = None,
    ) -> None:
        clean_cat = category.replace("us168_", "").replace("168worker_", "")
        self.category = clean_cat
        self.cfg = config.get(category, {})
        self.db = db
        self.email = email
        self.keywords = CATEGORY_KEYWORDS.get(clean_cat, [])

        import cloudscraper
        self._session = cloudscraper.create_scraper()

    def fetch_page(self, page_num: int) -> str | None:
        url = f"{DOMAIN}/job/?page={page_num}"
        try:
            resp = self._session.get(url, timeout=20)
            resp.raise_for_status()
            return resp.text
        except Exception:
            return None

    def parse_page(self, html: str) -> list[dict[str, str]]:
        soup = BeautifulSoup(html, "html.parser")
        results: list[dict[str, str]] = []

        for item in soup.find_all("div", class_="universal-list-module-item"):
            data_id = item.get("data-id", "")
            full_text = item.get_text(separator=" ", strip=True)

            if not any(kw in full_text for kw in self.keywords):
                continue

            title_el = item.find(
                ["p", "span", "div"],
                class_=lambda c: c and "single-line" in str(c) and "flex-1" not in str(c),
            )
            title = title_el.get_text(strip=True) if title_el else ""

            loc_el = item.find(
                "span", class_=lambda c: c and "flex-1" in str(c) and "single-line" in str(c)
            )
            location = loc_el.get_text(strip=True) if loc_el else ""

            price_el = item.find("span", class_=lambda c: c and "text-[20px]" in str(c))
            price = price_el.get_text(strip=True) if price_el else ""

            tags = []
            for tag_el in item.find_all("div", class_="classify-item"):
                tags.append(tag_el.get_text(strip=True))

            link = f"https://www.us168168.com/job/details/{data_id}" if data_id else ""

            results.append({
                "title": title or full_text[:60],
                "link": link,
                "author": location,
                "date": "",
                "salary": price,
                "tags": ",".join(tags),
                "data_id": data_id,
            })

        return results

    def _extract_nuxt_dates(self, html: str) -> list[str]:
        """Extract publish dates from Nuxt SSR __NUXT__ JSON."""
        import json
        m = re.search(
            r'<script[^>]*type="application/json"[^>]*>(.*?)</script>',
            html, re.DOTALL,
        )
        if not m:
            return []
        data = json.loads(m.group(1))
        dates: list[str] = []
        for val in data:
            if isinstance(val, dict) and "publishTime" in val:
                ts = val["publishTime"]
                if isinstance(ts, (int, float)) and ts > 1000000000000:
                    dt = datetime.fromtimestamp(ts / 1000).strftime("%m/%d/%Y")
                    dates.append(dt)
        return dates

    def scrape(self, existing_links: set[str] | None = None) -> list[dict[str, str]]:
        """Scrape pages, filtering out already-known links and extracting dates."""
        all_listings: list[dict[str, str]] = []

        for page_num in range(1, MAX_PAGES + 1):
            html = self.fetch_page(page_num)
            if not html:
                break

            # Extract dates from Nuxt SSR data (if available)
            nuxt_dates = self._extract_nuxt_dates(html)

            listings = self.parse_page(html)

            # Assign dates by position (from Nuxt SSR) or fallback
            now_str = datetime.now().strftime("%m/%d/%Y")
            for i, lst in enumerate(listings):
                lst["date"] = nuxt_dates[i] if i < len(nuxt_dates) else now_str

                if existing_links and lst["link"] in existing_links:
                    continue
                lst["source"] = self.SOURCE
                all_listings.append(lst)

            time.sleep(REQ_DELAY)

        return all_listings

    def run(self) -> dict[str, Any]:
        # Pre-load existing links for incremental mode
        existing: set[str] | None = None
        if self.db:
            existing = self.db.load_sent_ids()

        start = time.time()
        listings = self.scrape(existing_links=existing)
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
                f"\n    链接: {lst['link']}\n"
            )
        lines.append(f"\n抓取时间: {datetime.now():%Y-%m-%d %H:%M:%S}")
        return "\n".join(lines)
