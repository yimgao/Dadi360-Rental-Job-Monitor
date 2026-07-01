-- 给 anon 角色添加 DELETE 权限（用于数据清理）
-- 运行在 Supabase SQL Editor

-- 允许 anon 删除 listings
CREATE POLICY "anon_delete_listings" ON listings FOR DELETE USING (true);

-- 允许 anon 删除 runs
CREATE POLICY "anon_delete_runs" ON runs FOR DELETE USING (true);
