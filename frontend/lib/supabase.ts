"use client";

import { createClient, SupabaseClient } from "@supabase/supabase-js";

let _client: SupabaseClient | null = null;

function getClient(): SupabaseClient {
  if (!_client) {
    const url = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
    const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";
    if (!url || !key) {
      throw new Error("Supabase credentials not configured");
    }
    _client = createClient(url, key);
  }
  return _client;
}

/** Safe wrapper — never throws. Returns null if not configured. */
export function supabaseOrNull(): SupabaseClient | null {
  try {
    return getClient();
  } catch {
    return null;
  }
}

/** Throws if not configured — use in components that require a DB. */
export function getSupabase(): SupabaseClient {
  return getClient();
}
