-- Kip Tracker: fix "Waiting for approval" for the owner.
-- Run once in Supabase: SQL Editor -> New query -> paste -> Run.

-- 1. Make sure signed-in people may use the tables at all. Row-level security
--    still limits everyone to their own rows. Safe to run more than once.
grant usage on schema public to authenticated, service_role;
grant select, insert, update, delete on all tables in schema public to authenticated, service_role;
grant usage, select on all sequences in schema public to authenticated, service_role;
grant execute on all functions in schema public to authenticated, service_role;

-- 2. Make your account the admin. CHANGE the email below to your own.
update public.profiles
set role = 'admin', approved = true
where email = 'YOUR-EMAIL@gmail.com';

-- 3. Show who has signed in so far.
select email, role, approved, created_at from public.profiles order by created_at;
