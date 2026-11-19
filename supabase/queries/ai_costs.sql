-- Kip Tracker: check AI costs (read-only, changes nothing).
-- Supabase -> SQL Editor -> New query -> paste ONE part -> Run.
-- (The editor only shows the result of the last query, so run the parts one at a time.)

-- Part 1: the last 50 AI calls, newest first (times in Vientiane).
select
  to_char(created_at at time zone 'Asia/Vientiane', 'YYYY-MM-DD HH24:MI:SS') as time_vientiane,
  provider,
  model,
  success,
  error_kind,
  input_tokens,
  output_tokens,
  round(cost_usd, 5) as cost_usd
from public.api_usage
order by created_at desc
limit 50;

-- Part 2: totals per month and per AI.
select
  usage_month,
  provider,
  count(*) as calls,
  count(*) filter (where success) as successful_calls,
  round(sum(cost_usd), 4) as total_cost_usd,
  round(avg(cost_usd) filter (where success), 5) as avg_cost_per_receipt_usd
from public.api_usage
group by usage_month, provider
order by usage_month desc, provider;
