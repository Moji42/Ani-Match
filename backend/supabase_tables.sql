-- Supabase table creation for ani-match
-- Run these in the Supabase SQL editor for your project

-- favorites table
create table if not exists favorites (
  id bigserial primary key,
  user_id text not null,
  anime text not null,
  added_at timestamptz default now()
);

-- watchlist table
create table if not exists watchlist (
  id bigserial primary key,
  user_id text not null,
  anime text not null,
  added_at timestamptz default now()
);

-- preferences table (for like/dislike and other simple user prefs)
create table if not exists preferences (
  id bigserial primary key,
  user_id text not null,
  anime text not null,
  action text not null,
  value text,
  added_at timestamptz default now()
);

-- Optional indexes for performance
create index if not exists idx_favorites_user on favorites(user_id);
create index if not exists idx_watchlist_user on watchlist(user_id);
create index if not exists idx_preferences_user_action on preferences(user_id, action);
