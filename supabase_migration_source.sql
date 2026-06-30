-- Migration: add source column to listings and runs tables
-- Run this in Supabase SQL Editor

ALTER TABLE listings ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'dadi360' NOT NULL;
ALTER TABLE runs ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'dadi360' NOT NULL;

-- Backfill existing data
UPDATE listings SET source = 'dadi360' WHERE source IS NULL;

CREATE INDEX IF NOT EXISTS idx_listings_source ON listings (source);
CREATE INDEX IF NOT EXISTS idx_runs_source ON runs (source);
