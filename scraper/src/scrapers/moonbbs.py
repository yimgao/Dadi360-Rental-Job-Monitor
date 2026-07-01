"""Scraper for moonbbs.com — Discuz! forum with job & rental listings.

Relevant forums:
  - Forum 57: 求职招聘 (job hiring)
  - Forum 48: 租房 (rental: NYC/LA/SF)

URL pattern:  https://www.moonbbs.com/forum-{fid}-{page}.html
Each page has ~30-50 thread rows in <tbody> with class "normal" or "th".
Thread link:  <a href="thread-{tid}-1-1.html">TITLE</a>
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

DOMAIN = "https://www.moonbbs.com"
REQ_DELAY = 1.5
MAX_PAGES = 20
DAYS_BACK = 4

CATEGORY_MAP: dict[str, dict[str, Any]] = {
    "rental":       {"fid": 48, "source": "moonbbs", "cat": "rental"},
    "restaurant_jobs": {"fid": 57, "source": "moonbbs", "cat": "restaurant_jobs"},
    "nail_jobs":    {"fid": 57, "source": "moonbbs", "cat": "nail_jobs"},
}

CATEGORY_KEYWORDS = {
    "rental": ["租房", "出租", "求租", "公寓", "studio", "单房", "套房", "整房"],
    "restaurant_jobs": ["餐馆", "餐厅", "厨师", "厨房", "企台", "收银", "炒锅", "奶茶", "寿司", "服务员", "帮炒"],
    "nail_jobs": ["美甲", "指甲", "甲店", "美甲师", "美甲店", "指甲师"],
}


class MoonbbsScraper:
    """Scrape moonbbs.com forum listings."""

    SOURCE = "moonbbs"

    def __init__(
        self,
        category: str,
        config: dict[str, Any],
        db: DB | None = None,
        email: EmailSender | None = None,
    ) -> None:
        # Strip prefix
        clean_cat = category.replace("moonbbs_", "").replace("us168_", "").replace("168worker_", "")
        self.category = clean_cat
        self.cfg = config.get(category, {})
        self.db = db
        self.email = email
        self.fid = CATEGORY_MAP[clean_cat]["fid"]
        self.keywords = CATEGORY_KEYWORDS.get(clean_cat, [])

        self._session = requests.Session()
        self._session.headers["User-Agent"] = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
        self._session.headers["Accept-Language"] = "zh-CN,zh;q=0.9,en;q=0.8"
        self._session.verify = False
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def fetch_page(self, page_num: int) -> str | None:
        url = f"{DOMAIN}/forum-{self.fid}-{page_num}.html"
        try:
            resp = self._session.get(url, timeout=15)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException:
            return None

    def parse_page(self, html: str) -> list[dict[str, str]]:
        soup = BeautifulSoup(html, "html.parser")
        results: list[dict[str, str]] = []

        for row in soup.select("tbody[id^=normalthread]"):
            title_el = row.find("a", class_="xst")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            href = title_el.get("href", "")
            full_link = f"{DOMAIN}/{href}" if href.startswith("/") else f"{DOMAIN}/" + href

            if self.keywords and not any(kw in title for kw in self.keywords):
                continue

            # Author
            author_el = row.select_one("td.by cite a")
            author = author_el.get_text(strip=True) if author_el else ""

            # Date — from <span title="2026-6-29">
            date_el = row.select_one("td.by em span")
            date = date_el.get("title", "") if date_el else ""
            if not date and date_el:
                date = date_el.get_text(strip=True)

            results.append({
                "title": title,
                "link": full_link,
                "author": author,
                "date": date,
            })

        return results

    def scrape(self) -> list[dict[str, str]]:
        all_listings: list[dict[str, str]] = []
        for page_num in range(1, MAX_PAGES + 1):
            html = self.fetch_page(page_num)
            if not html:
                break
            listings = self.parse_page(html)
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
            "category": self.category, "source": self.SOURCE,
            "new_count": new_count, "duration_s": elapsed,
            "success": True, "error": None,
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
            subject = f"【moonbbs-{self.category}】{new_count} 条匹配"
            body = self._format_email(listings)
            sent, err = self.email.send(subject, body)
            if not sent:
                result["email_error"] = err
        return result

    def _format_email(self, listings: list[dict]) -> str:
        lines = [f"moonbbs {self.category} — 共 {len(listings)} 条匹配：\n"]
        for i, lst in enumerate(listings, 1):
            lines.append(f"{i}. {lst['title']}\n    链接: {lst['link']}\n")
        lines.append(f"\n抓取时间: {datetime.now():%Y-%m-%d %H:%M:%S}")
        return "\n".join(lines)
