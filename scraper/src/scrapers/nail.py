"""Nail salon job scraper (forum 56)."""

from .base import BaseScraper


class NailScraper(BaseScraper):
    def get_forum_id(self) -> int:
        return 56

    def get_search_keywords(self) -> list[str]:
        return self.cfg.get(
            "keywords",
            [
                "美甲", "指甲", "nail", "甲店", "美甲师", "指甲师", "美甲店", "指甲店",
                "美甲工作", "指甲工作", "美甲请人", "指甲请人", "美甲招聘", "指甲招聘",
                "美甲师招聘", "指甲师招聘", "美甲学徒", "指甲学徒", "美甲助理", "指甲助理",
                "美甲师傅", "指甲师傅", "美甲店请人", "指甲店请人", "美甲店招聘", "指甲店招聘",
                "小工", "大工",
            ],
        )

    def get_email_subject_prefix(self) -> str:
        return "美甲招聘"
