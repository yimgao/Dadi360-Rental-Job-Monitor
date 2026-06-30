"""Supabase persistence layer for scraper results."""

from __future__ import annotations

import os
import json
from datetime import datetime, timezone
from typing import Any

from supabase import create_client, Client


class DB:
    """Thin wrapper around Supabase for dadi360 scrapers.

    Expects SUPABASE_URL and SUPABASE_SERVICE_KEY in environment.
    """

    def __init__(self) -> None:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        self._client: Client = create_client(url, key)

    # ── listings ─────────────────────────────────────────────────────

    def upsert_listing(
        self, category: str, listing: dict[str, Any], source: str = "dadi360"
    ) -> tuple[bool, str | None]:
        """Insert a listing. Idempotent on (link)."""
        try:
            row = {
                "link": listing["link"],
                "title": listing.get("title", ""),
                "author": listing.get("author", ""),
                "date": listing.get("date", ""),
                "description": listing.get("description", ""),
                "category": category,
                "source": source,
                "found_at": datetime.now(timezone.utc).isoformat(),
            }
            self._client.table("listings").upsert(row, on_conflict="link").execute()
            return True, None
        except Exception as exc:
            return False, str(exc)

    def bulk_upsert_listings(
        self, category: str, listings: list[dict[str, Any]], source: str = "dadi360"
    ) -> tuple[int, list[str]]:
        """Insert many listings. Returns (success_count, errors)."""
        ok = 0
        errors: list[str] = []
        for lst in listings:
            success, err = self.upsert_listing(category, lst, source=source)
            if success:
                ok += 1
            elif err:
                errors.append(err)
        return ok, errors

    def log_run(
        self,
        category: str,
        new_count: int,
        duration_s: float,
        success: bool,
        error: str | None = None,
        source: str = "dadi360",
    ) -> None:
        """Insert a run record."""
        try:
            self._client.table("runs").insert(
                {
                    "category": category,
                    "new_count": new_count,
                    "duration_s": duration_s,
                    "success": success,
                    "error": error,
                    "source": source,
                    "started_at": datetime.now(timezone.utc).isoformat(),
                }
            ).execute()
        except Exception:
            pass

    # ── config (read-only from scraper side) ─────────────────────────

    def get_config(self) -> dict[str, Any]:
        """Read config from Supabase ``config`` table (single row)."""
        try:
            resp = self._client.table("config").select("*").limit(1).execute()
            if resp.data:
                return resp.data[0]
        except Exception:
            pass
        return {}

    # ── sent IDs for dedup (cross-run) ───────────────────────────────

    def load_sent_ids(self) -> set[str]:
        """Load all previously-seen listing links."""
        ids: set[str] = set()
        try:
            resp = self._client.table("listings").select("link").execute()
            for row in resp.data or []:
                if link := row.get("link"):
                    ids.add(link)
        except Exception:
            pass
        return ids
