# Fixing Persistence (Favorites, Watchlist, Preferences)

Your tables are created, but **persistence likely isn't working due to Supabase Row Level Security (RLS)** policies blocking inserts.

## Quick Fix (5 minutes)

### Step 1: Disable RLS on the tables
1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Click **New Query** and copy-paste the contents of `backend/fix_rls_policies.sql`
4. Click **Run**

This will disable RLS on `favorites`, `watchlist`, and `preferences` tables, allowing your backend to insert/read/delete records.

### Step 2: Start the backend and test
```bash
cd /home/moji42/ani-match/backend
python3 app.py
```

### Step 3: Start the frontend
```bash
cd /home/moji42/ani-match/frontend
npm run dev
```

### Step 4: Test in the UI
1. Open http://localhost:8080 (or 8081 if 8080 is in use)
2. Sign in (register if needed)
3. Search for an anime and open its details
4. Click **Add to Favorites** or **Add to Watchlist**
5. Open **My Library** (next to logout button) and verify the item appears

## If it still doesn't work:

1. **Check Flask logs**: Look at the output in your terminal where you ran `python3 app.py`
   - Search for error messages containing "Supabase" or "Failed to add"
   
2. **Test the backend directly**:
   ```bash
   cd /home/moji42/ani-match/backend
   python3 test_persistence.py
   ```
   This will register a test user, add favorites, and show any errors.

3. **Verify your Supabase credentials** in `backend/.env`:
   - Check that `SUPABASE_URL` and `SUPABASE_KEY` are set correctly
   - The key should be your **anon key** or **service role key** (from Settings > API)

## Production Note (Optional)

If you want to keep RLS enabled for security, use the commented-out policies in `fix_rls_policies.sql` instead. They require the user's JWT to match their `user_id` in the database.

For now, **disabling RLS is the simplest approach for development**.
