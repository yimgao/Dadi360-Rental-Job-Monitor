#!/usr/bin/env python3
"""dadi360 scraper — CLI entry point.

Usage:
    python -m src.main                    # run all enabled scrapers once
    python -m src.main --watch            # loop forever (for local use)
    python -m src.main --category rental  # run one category only
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

from dotenv import load_dotenv

from .db import DB
from .email import EmailSender
from .scrapers import RentalScraper, NailScraper, RestaurantScraper, Worker168Scraper, Us168Scraper

load_dotenv()

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(os.path.dirname(HERE), "config.json")


def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_scraper(category: str, config: dict, db: DB | None, email: EmailSender | None):
    cls_map = {
        "rental": RentalScraper,
        "nail_jobs": NailScraper,
        "restaurant_jobs": RestaurantScraper,
        "168worker_restaurant_jobs": Worker168Scraper,
        "168worker_nail_jobs": Worker168Scraper,
        "us168_restaurant_jobs": Us168Scraper,
        "us168_nail_jobs": Us168Scraper,
    }
    cls = cls_map.get(category)
    if cls is None:
        raise ValueError(f"Unknown category: {category}")
    if category.startswith("168worker_"):
        return cls(category=category.replace("168worker_", ""), config=config, db=db, email=email)
    return cls(category=category, config=config, db=db, email=email)


def run_category(category: str, config: dict, db: DB | None, email: EmailSender | None) -> dict:
    scraper = get_scraper(category, config, db, email)
    result = scraper.run()
    if db:
        db.log_run(
            category=category,
            new_count=result["new_count"],
            duration_s=result["duration_s"],
            success=result["success"],
            error=result.get("error") or result.get("email_error"),
            source=result.get("source", "dadi360"),
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="dadi360 scraper")
    parser.add_argument("--category", "-c", help="Run only one category")
    parser.add_argument("--watch", "-w", action="store_true", help="Loop forever")
    args = parser.parse_args()

    config = load_config()
    db: DB | None = None
    email: EmailSender | None = None

    try:
        db = DB()
    except RuntimeError as exc:
        print(f"[WARN] DB not configured: {exc}", file=sys.stderr)

    email = EmailSender(config.get("EMAIL"))

    categories = [args.category] if args.category else [k for k, v in config.items() if isinstance(v, dict) and v.get("enabled", True)]
    # filter out non-category keys
    valid = {"rental", "nail_jobs", "restaurant_jobs", "168worker_restaurant_jobs", "168worker_nail_jobs", "us168_restaurant_jobs", "us168_nail_jobs"}
    categories = [c for c in categories if c in valid]

    def run_all() -> None:
        for cat in categories:
            result = run_category(cat, config, db, email)
            status = "✓" if result["success"] else "✗"
            print(
                f"[{status}] {cat}: {result['new_count']} new listings "
                f"in {result['duration_s']}s"
            )
            if result.get("email_error"):
                print(f"  └ email error: {result['email_error']}", file=sys.stderr)

    run_all()

    if args.watch:
        interval_min = config.get("rental", {}).get("send_interval_minutes", 10)
        print(f"\nWatching every {interval_min} min (Ctrl+C to stop)...")
        try:
            while True:
                time.sleep(interval_min * 60)
                run_all()
        except KeyboardInterrupt:
            print("\nStopped.")


if __name__ == "__main__":
    main()
