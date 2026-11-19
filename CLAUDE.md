# Working with the owner of this project

- The owner does not code and often works from a phone without a PC.
- Explain every step in plain language with exact taps/clicks.
- Every time a step involves a website, give a direct link to that exact page.
- Every time SQL must be run, paste the full SQL in the chat (ready to copy) AND give a link to the file on GitHub.
- Ask before anything that costs money or is hard to undo. The app must stay free (Claude API credit, then free Gemini).
- Stop after each stage, explain how to test it, and wait for the owner's OK.

# Project status (update this section when things change)

- **What it is:** Kip Tracker, a private family spending tracker that reads BCEL One receipt images. See README.md for how it works and the 4-stage roadmap.
- **Hosting:** Cloudflare Workers (project `bcel-accounting`, built with OpenNext: build `npx opennextjs-cloudflare build`, deploy `npx wrangler deploy`). Cloudflare rebuilds automatically on every push to branch `ccr-26fb9533-tieoku` (the repo's only/default branch). Vercel was abandoned because `vercel.app` is unreachable from the owner's network in Laos.
- **Services:** Supabase (Postgres + RLS, Google sign-in, `review-images` bucket), Claude Haiku 5.5 first, free-tier Gemini as fallback. Secrets live only in Cloudflare (Settings -> Variables and Secrets): `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SECRET_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`.
- **Database:** migrations `0001_init.sql` and `0002_access_and_admin.sql` have been run by the owner. Any new SQL must be given to the owner to run by hand (pasted in chat + GitHub link).
- **Stage:** Stage 1 is built and deployed; the owner can sign in as admin. Receipt reading with real images on the live site has NOT been confirmed yet. Stages 2-4 not started; wait for the owner's OK on Stage 1 first.
- **Decisions made:** Google sign-in only (no email links); everything must stay free (no card on file anywhere); Gemini on free tier accepted; review images kept up to 7 days; transfers to family count as spending; own-account transfers and THB->LAK exchanges do not; THB spending converted with the latest exchange-receipt rate; UI theme is BCEL red with frosted glass (no BCEL logo).
- **Receipt types (from the owner's samples):** transfer to a person, own-account currency exchange, QR/merchant payment. Never commit real receipt images; tests use made-up data.
- **Debugging aid:** `/setup-check` on the live site shows which settings are wrong without revealing values. This environment cannot open the live site, so ask the owner for screenshots.
