"""Restaurant job scraper (forum 56 — same board as nail)."""

from .base import BaseScraper


class RestaurantScraper(BaseScraper):
    def get_forum_id(self) -> int:
        return self.cfg.get("forum_id", 56)

    def get_search_keywords(self) -> list[str]:
        return self.cfg.get("keywords", ["餐厅", "餐馆", "厨师", "企台", "收银", "服务员"])

    def get_email_subject_prefix(self) -> str:
        return "餐厅招聘"
