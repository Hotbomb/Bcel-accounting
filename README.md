# Kip Tracker

A private, invite-only spending tracker for BCEL One payment receipts. It's mobile-first and installable as an app (PWA) on iPhone, Android and PC.

- **Setup (no coding):** see [SETUP.md](SETUP.md).
- **Stage:** 1 of 4. Web upload, receipt reading with AI fallback and cost tracking, transaction list, simple dashboard, manual income.

## How it works

1. You pick photos on the **Add receipts** page. Your device first skips photos that clearly aren't BCEL receipts: it looks for the red BCEL bands at the top and bottom. It then shrinks the rest and uploads them one at a time.
2. The server skips photos it has seen before (by fingerprint), checks rate and monthly limits, and asks **Claude Haiku 5.5** to decide "is this a BCEL receipt?" and extract the details as strict JSON. If Claude fails, its credit runs out, or the monthly cap (default $5) is reached, it uses **Gemini** (free tier) instead. Claude is used again automatically the next month.
3. The answer is validated and cleaned:
   - Dates are converted to Vientiane time and checked against the reference number.
   - Account numbers are masked.
   - "." notes are removed.
   - Transfers between your own accounts (like THB to LAK exchanges) are marked as **own transfers** and not counted as spending.
4. Duplicates are detected by the bank reference number. A same amount + time + recipient match is sent to **Needs review** rather than dropped.
5. Low-confidence or incomplete receipts go to **Needs review**. Only these keep their image, privately, for up to 7 days. All other images are never stored.

Every AI call's estimated cost is saved in the `api_usage` table.

## How to test Stage 1

1. **Sign in** with Google. The dashboard should be empty.
2. **Add receipts:** tap *Choose photos* and select your 3 sample receipts plus about 5 normal photos.
   - Expect roughly: *"Added 3 receipts, skipped 5 other photos."*
3. **Upload the same photos again.** Expect *"3 already added"*, and no new AI costs.
4. **Transactions:** check that each receipt's amount, date and time, and name (including the Lao shop name) are right.
   - The THB to LAK exchange shows 🔁 *Own transfer (not spending)*.
5. **Manual entry:** add an income (e.g. salary 5,000,000 ₭). The dashboard's *Income this month* updates.
6. **Edit and delete:** open a transaction, change its category and save. Then delete a test entry.
7. **Dashboard:** today / week / month totals, last-month comparison, per-day chart, categories, top recipients.
8. **Costs:** in Supabase, go to **Table Editor** and open **api_usage** to see each AI call and its estimated cost.

## For developers

```bash
npm install
cp .env.example .env.local   # fill in values
npm run dev                   # http://localhost:3000
npm test                      # unit tests
npm run typecheck && npm run lint && npm run build
```

- Next.js 15 (App Router) + Tailwind 4, deployed on Vercel (region `sin1`).
- Supabase: Google auth, Postgres with row-level security (`supabase/migrations`), private storage bucket `review-images`.
- AI: `@anthropic-ai/sdk` (structured outputs via `messages.parse` + Zod), `@google/genai` fallback. Keys exist only as server environment variables.
- Key code: `src/lib/receipt/` (prompt, schema, providers, fallback, normalisation, pre-filter) and `src/app/api/receipts/route.ts`.

## Roadmap

- **Stage 2:** invite codes and member approval, categories that learn per recipient, budgets with 80% / 100% warnings.
- **Stage 3:** iPhone Shortcut + automation, Android share target, upload tokens, daily and weekly accountability, notifications.
- **Stage 4:** Android helper app (APK via GitHub Actions), Lao translation polish, CSV export, admin page, account deletion.
