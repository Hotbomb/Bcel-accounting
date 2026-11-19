-- Kip Tracker: Stage 1 database schema
-- Run this whole file once in Supabase: SQL Editor -> New query -> paste -> Run.
-- Every table holding personal data has row-level security (RLS) turned on,
-- so the database itself refuses to show one person's data to another.

-- ---------------------------------------------------------------------------
-- Profiles: one row per signed-in person. The very first person to sign in
-- becomes the admin and is approved automatically. Everyone after that waits
-- for approval (Stage 2 adds invite codes).
-- ---------------------------------------------------------------------------
create table public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  email text not null,
  display_name text,
  role text not null default 'member' check (role in ('admin', 'member')),
  approved boolean not null default false,
  monthly_receipt_limit integer,          -- null = use the global default
  last_sync_at timestamptz,
  created_at timestamptz not null default now()
);

alter table public.profiles enable row level security;

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  is_first boolean;
begin
  select not exists (select 1 from public.profiles) into is_first;
  insert into public.profiles (id, email, display_name, role, approved)
  values (
    new.id,
    coalesce(new.email, ''),
    coalesce(new.raw_user_meta_data ->> 'full_name', new.raw_user_meta_data ->> 'name'),
    case when is_first then 'admin' else 'member' end,
    is_first
  );
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- Helper functions used by the security rules below.
create or replace function public.is_approved()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select coalesce((select approved from public.profiles where id = auth.uid()), false);
$$;

create or replace function public.is_admin()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select coalesce((select role = 'admin' and approved from public.profiles where id = auth.uid()), false);
$$;

create policy "read own profile" on public.profiles
  for select using (id = auth.uid() or public.is_admin());
create policy "update own display name" on public.profiles
  for update using (id = auth.uid()) with check (id = auth.uid());

-- Stop members from promoting or approving themselves.
create or replace function public.protect_profile_fields()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  if not public.is_admin() and auth.uid() is not null then
    new.role := old.role;
    new.approved := old.approved;
    new.monthly_receipt_limit := old.monthly_receipt_limit;
    new.email := old.email;
  end if;
  return new;
end;
$$;

create trigger protect_profile_fields
  before update on public.profiles
  for each row execute function public.protect_profile_fields();

-- ---------------------------------------------------------------------------
-- App settings (a single row). Everyone signed in can read; only admin edits.
-- ---------------------------------------------------------------------------
create table public.app_settings (
  id integer primary key default 1 check (id = 1),
  claude_monthly_cap_usd numeric(10, 2) not null default 5.00,
  per_user_monthly_receipt_limit integer not null default 500,
  claude_paused_month text,               -- e.g. '2026-11' when credits ran out
  updated_at timestamptz not null default now()
);

insert into public.app_settings (id) values (1);

alter table public.app_settings enable row level security;
create policy "read settings" on public.app_settings
  for select using (public.is_approved());
create policy "admin edits settings" on public.app_settings
  for update using (public.is_admin()) with check (public.is_admin());

-- ---------------------------------------------------------------------------
-- Transactions: spending, income and transfers between your own accounts.
-- ---------------------------------------------------------------------------
create table public.transactions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users (id) on delete cascade,
  kind text not null check (kind in ('expense', 'income', 'own_transfer')),
  source text not null check (source in ('receipt', 'manual')),
  status text not null default 'confirmed' check (status in ('confirmed', 'needs_review')),
  review_reasons text[] not null default '{}',
  occurred_at timestamptz not null,
  amount numeric(18, 2) not null check (amount >= 0),
  currency text not null default 'LAK',
  amount_lak numeric(18, 2),              -- amount converted to kip (null = unknown yet)
  fee numeric(18, 2),
  to_amount numeric(18, 2),               -- currency exchanges only
  to_currency text,
  exchange_rate numeric(18, 6),
  receipt_type text check (receipt_type in ('transfer', 'qr_payment', 'currency_exchange', 'other')),
  counterparty_name text,
  counterparty_account text,              -- always masked
  from_account text,                      -- always masked
  transaction_ref text,                   -- BCEL bill number / reference 2
  ticket_ref text,                        -- BCEL ticket / reference 1
  dedupe_key text,                        -- fallback when there is no reference
  memo text,
  category text not null default 'other',
  confidence numeric(4, 3),
  extractor text,                         -- which AI read it, e.g. 'anthropic:claude-haiku-5-5'
  review_image_path text,                 -- temporary, only while it needs review
  review_image_expires_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create unique index transactions_user_ref_unique
  on public.transactions (user_id, transaction_ref)
  where transaction_ref is not null;
create index transactions_user_time on public.transactions (user_id, occurred_at desc);
create index transactions_dedupe on public.transactions (user_id, dedupe_key);

alter table public.transactions enable row level security;
create policy "own transactions: read" on public.transactions
  for select using (user_id = auth.uid() and public.is_approved());
create policy "own transactions: insert" on public.transactions
  for insert with check (user_id = auth.uid() and public.is_approved());
create policy "own transactions: update" on public.transactions
  for update using (user_id = auth.uid() and public.is_approved())
  with check (user_id = auth.uid());
create policy "own transactions: delete" on public.transactions
  for delete using (user_id = auth.uid() and public.is_approved());

create or replace function public.touch_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

create trigger transactions_touch
  before update on public.transactions
  for each row execute function public.touch_updated_at();

-- ---------------------------------------------------------------------------
-- Your own bank accounts (learned automatically from the "from" side of
-- receipts) so transfers between them are not counted as spending.
-- ---------------------------------------------------------------------------
create table public.own_accounts (
  user_id uuid not null default auth.uid() references auth.users (id) on delete cascade,
  account_masked text not null,
  currency text,
  holder_name text,
  created_at timestamptz not null default now(),
  primary key (user_id, account_masked)
);

alter table public.own_accounts enable row level security;
create policy "own accounts: all" on public.own_accounts
  for all using (user_id = auth.uid() and public.is_approved())
  with check (user_id = auth.uid());

-- ---------------------------------------------------------------------------
-- Fingerprints of photos already processed, so the same photo is never sent
-- to the AI twice. Only a hash is stored, never the photo.
-- ---------------------------------------------------------------------------
create table public.image_hashes (
  user_id uuid not null default auth.uid() references auth.users (id) on delete cascade,
  sha256 text not null,
  result text not null check (result in ('receipt', 'not_receipt', 'duplicate')),
  created_at timestamptz not null default now(),
  primary key (user_id, sha256)
);

alter table public.image_hashes enable row level security;
create policy "own hashes: all" on public.image_hashes
  for all using (user_id = auth.uid() and public.is_approved())
  with check (user_id = auth.uid());

-- ---------------------------------------------------------------------------
-- AI usage and estimated cost, one row per AI call. Written only by the
-- server (secret key). People can read their own rows; admin reads all.
-- ---------------------------------------------------------------------------
create table public.api_usage (
  id bigint generated always as identity primary key,
  user_id uuid references auth.users (id) on delete set null,
  provider text not null check (provider in ('anthropic', 'gemini')),
  model text not null,
  input_tokens integer not null default 0,
  output_tokens integer not null default 0,
  cost_usd numeric(12, 6) not null default 0,
  success boolean not null,
  error_kind text,
  usage_month text not null,              -- 'YYYY-MM' in Vientiane time
  created_at timestamptz not null default now()
);

create index api_usage_month on public.api_usage (usage_month, provider);
create index api_usage_user_month on public.api_usage (user_id, usage_month);

alter table public.api_usage enable row level security;
create policy "read own usage" on public.api_usage
  for select using (user_id = auth.uid() or public.is_admin());

-- ---------------------------------------------------------------------------
-- Private storage for receipt images that need review (deleted after 7 days
-- or as soon as you confirm the transaction).
-- ---------------------------------------------------------------------------
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('review-images', 'review-images', false, 5242880, array['image/jpeg', 'image/png', 'image/webp'])
on conflict (id) do nothing;

create policy "review images: owner read" on storage.objects
  for select using (
    bucket_id = 'review-images' and (storage.foldername(name))[1] = auth.uid()::text
  );
create policy "review images: owner insert" on storage.objects
  for insert with check (
    bucket_id = 'review-images' and (storage.foldername(name))[1] = auth.uid()::text
  );
create policy "review images: owner delete" on storage.objects
  for delete using (
    bucket_id = 'review-images' and (storage.foldername(name))[1] = auth.uid()::text
  );
