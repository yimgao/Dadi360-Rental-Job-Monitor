-- dadi360 Supabase schema
-- Paste this into Supabase SQL Editor to create all tables.

-- 1. Matched listings
CREATE TABLE listings (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  link TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  author TEXT DEFAULT '',
  date TEXT DEFAULT '',
  description TEXT DEFAULT '',
  category TEXT NOT NULL CHECK (category IN ('rental', 'nail_jobs', 'restaurant_jobs')),
  found_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_listings_category ON listings (category);
CREATE INDEX idx_listings_found_at ON listings (found_at DESC);

-- 2. Run history
CREATE TABLE runs (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  category TEXT NOT NULL,
  new_count INTEGER DEFAULT 0,
  duration_s REAL DEFAULT 0,
  success BOOLEAN DEFAULT TRUE,
  error TEXT,
  started_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_runs_category ON runs (category);
CREATE INDEX idx_runs_started_at ON runs (started_at DESC);

-- 3. Config (frontend-editable key-value pairs)
CREATE TABLE config (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  key TEXT NOT NULL UNIQUE,
  value TEXT NOT NULL DEFAULT ''
);

-- Default config rows (adjust as needed)
INSERT INTO config (key, value) VALUES
  ('rental_keywords', '2房一厅,两房一厅,2卧一厅,两卧一厅,2室1厅,两室一厅'),
  ('nail_keywords', '美甲,指甲,nail,美甲师,指甲师,美甲店'),
  ('restaurant_keywords', '餐厅,餐馆,厨师,企台,收银,服务员'),
  ('receiver_email', ''),
  ('scrape_interval_min', '10')
ON CONFLICT (key) DO NOTHING;

-- Enable Row Level Security (public read/insert for anon key)
ALTER TABLE listings ENABLE ROW LEVEL SECURITY;
ALTER TABLE runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE config ENABLE ROW LEVEL SECURITY;

-- Allow anon access (safe for this monitoring dashboard)
CREATE POLICY "anon_select_listings" ON listings FOR SELECT USING (true);
CREATE POLICY "anon_insert_listings" ON listings FOR INSERT WITH CHECK (true);
CREATE POLICY "anon_select_runs" ON runs FOR SELECT USING (true);
CREATE POLICY "anon_insert_runs" ON runs FOR INSERT WITH CHECK (true);
CREATE POLICY "anon_select_config" ON config FOR SELECT USING (true);
CREATE POLICY "anon_insert_config" ON config FOR INSERT WITH CHECK (true);
CREATE POLICY "anon_update_config" ON config FOR UPDATE USING (true);
