"""Rental listing scraper (forum 87)."""

from .base import BaseScraper


class RentalScraper(BaseScraper):
    def get_forum_id(self) -> int:
        return 87

    def get_search_keywords(self) -> list[str]:
        return self.cfg.get(
            "search_terms",
            ["2房一厅", "两房一厅", "2卧一厅", "两卧一厅", "2室1厅", "两室一厅", "2房1厅", "两房1厅", "2卧1厅", "两卧1厅"],
        )

    def get_email_subject_prefix(self) -> str:
        return "租房"
