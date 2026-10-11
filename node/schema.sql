-- Run once in the selected Supabase project's SQL Editor.
-- State contains private exam keys: only the Node server's service role may access it.
create table if not exists public.learning_states (
 user_id uuid primary key references auth.users(id) on delete cascade,
 body jsonb not null default '{}'::jsonb,
 version bigint not null default 0,
 updated_at timestamptz not null default now()
);
alter table public.learning_states enable row level security;
revoke all on public.learning_states from anon, authenticated;
grant select, insert, update, delete on public.learning_states to service_role;
-- Deliberately no client policy: every read/write passes server auth and owner checks.
create table if not exists public.account_sessions (
 id text primary key,
 user_id uuid not null references auth.users(id) on delete cascade,
 created_at timestamptz not null default now(),
 expires_at timestamptz not null
);
alter table public.account_sessions enable row level security;
revoke all on public.account_sessions from anon, authenticated;
grant select, insert, update, delete on public.account_sessions to service_role;
