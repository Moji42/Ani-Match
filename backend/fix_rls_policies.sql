-- Fix RLS policies for ani-match persistence tables
-- Run this in your Supabase SQL editor

-- Disable RLS on the tables (simplest approach for testing)
ALTER TABLE public.favorites DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.watchlist DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.preferences DISABLE ROW LEVEL SECURITY;

-- If you prefer to keep RLS enabled, use these policies instead:
-- (Comment out the DISABLE statements above and use these)

-- -- Enable RLS
-- ALTER TABLE public.favorites ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.watchlist ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.preferences ENABLE ROW LEVEL SECURITY;

-- -- Favorites policies (allow select/insert/delete own records)
-- CREATE POLICY "Allow users to select own favorites"
--   ON public.favorites
--   FOR SELECT
--   USING (auth.uid()::text = user_id);

-- CREATE POLICY "Allow users to insert own favorites"
--   ON public.favorites
--   FOR INSERT
--   WITH CHECK (auth.uid()::text = user_id);

-- CREATE POLICY "Allow users to delete own favorites"
--   ON public.favorites
--   FOR DELETE
--   USING (auth.uid()::text = user_id);

-- -- Watchlist policies
-- CREATE POLICY "Allow users to select own watchlist"
--   ON public.watchlist
--   FOR SELECT
--   USING (auth.uid()::text = user_id);

-- CREATE POLICY "Allow users to insert own watchlist"
--   ON public.watchlist
--   FOR INSERT
--   WITH CHECK (auth.uid()::text = user_id);

-- CREATE POLICY "Allow users to delete own watchlist"
--   ON public.watchlist
--   FOR DELETE
--   USING (auth.uid()::text = user_id);

-- -- Preferences policies
-- CREATE POLICY "Allow users to select own preferences"
--   ON public.preferences
--   FOR SELECT
--   USING (auth.uid()::text = user_id);

-- CREATE POLICY "Allow users to insert own preferences"
--   ON public.preferences
--   FOR INSERT
--   WITH CHECK (auth.uid()::text = user_id);

-- CREATE POLICY "Allow users to delete own preferences"
--   ON public.preferences
--   FOR DELETE
--   USING (auth.uid()::text = user_id);
