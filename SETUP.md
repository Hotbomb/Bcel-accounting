# Kip Tracker setup guide (no coding needed)

This guide puts Kip Tracker on the internet using free accounts. It takes about 45 minutes the first time. Do the steps in order, on a computer if possible (a phone works but is fiddly).

You will create five free accounts: **Supabase** (the database), **Google Cloud** (for "Sign in with Google"), **Anthropic** (Claude, which reads the receipts), **Google AI Studio** (Gemini, the free backup reader) and **Cloudflare** (which runs the website).

> **Money rule:** nothing in this guide asks for a credit card. If any website asks for payment details, **stop and tell Claude in the chat** before entering anything.

Keep a private note open (for example in your phone's Notes app, *not* shared) to paste values into as you go. You'll collect:

| Name | Where it comes from |
|---|---|
| `SUPABASE_URL` | Supabase, step 1.5 |
| `SUPABASE_PUBLISHABLE_KEY` | Supabase, step 1.5 |
| `SUPABASE_SECRET_KEY` | Supabase, step 1.5 (keep secret!) |
| `ANTHROPIC_API_KEY` | Anthropic, step 3 (keep secret!) |
| `GEMINI_API_KEY` | Google AI Studio, step 4 (keep secret!) |

**Direct links** (open them on your phone):
Supabase sign-in https://supabase.com/dashboard/sign-in ·
SQL file https://github.com/Hotbomb/Bcel-accounting/blob/ccr-26fb9533-tieoku/supabase/migrations/0001_init.sql ·
Google Cloud https://console.cloud.google.com/projectcreate ·
Claude billing https://platform.claude.com/settings/billing ·
Gemini key https://aistudio.google.com/apikey ·
Cloudflare https://dash.cloudflare.com/?to=/:account/workers-and-pages

Websites change their button names now and then. If a button in this guide is missing, look for one with a similar name, or ask Claude in the chat and describe what you see.

---

## 1. Supabase (the database)

1. Go to **supabase.com**, click **Start your project**, then **Continue with GitHub** and allow access.
2. If asked to create an organization: name it anything (e.g. "Family"), choose the **Free** plan, click **Create organization**.
3. Click **New project**:
   - **Project name:** `kip-tracker`
   - **Database password:** click **Generate a password**, then copy it into your private note.
   - **Region:** **Southeast Asia (Singapore)** (closest to Laos).
   - Click **Create new project** and wait about 2 minutes until the dashboard appears.
4. **Create the tables.**
   1. In a new tab, open your GitHub repository, click the folder **supabase**, then **migrations**, then the file **0001_init.sql**.
   2. Click the **Copy raw file** button (two overlapping squares, top right of the file).
   3. Back in Supabase, click **SQL Editor** in the left sidebar (the icon looks like `>_`), then **New query** (or the **+** button).
   4. Click in the big empty box, paste (Ctrl+V or Cmd+V), then click **Run** (bottom right).
   5. You should see **"Success. No rows returned"**. If you see red error text, copy it and send it to Claude.
5. **Copy your keys.**
   1. Click the **gear icon (Project Settings)** at the bottom of the left sidebar.
   2. Open **Data API** (or **API**). Copy the **Project URL** (it looks like `https://abcdefgh.supabase.co`) into your note as `SUPABASE_URL`.
   3. Open **API Keys**.
      - Copy the **Publishable key** (starts with `sb_publishable_`) as `SUPABASE_PUBLISHABLE_KEY`.
      - Under **Secret keys**, click **Reveal** and copy it (starts with `sb_secret_`) as `SUPABASE_SECRET_KEY`. **Never share this key with anyone**, not even in this chat.
      - If you only see "anon" and "service_role" keys (older layout), use **anon** as the publishable key and **service_role** as the secret key.

## 2. Sign in with Google

### 2a. Create the Google login app

1. Go to **console.cloud.google.com** and sign in with your Google account. Accept the terms if asked. **Do not start a free trial or add billing.**
2. At the top, click the project picker (next to "Google Cloud"), then **New project**. Name it `kip-tracker` and click **Create**. Make sure it's selected at the top afterwards.
3. In the search bar at the top, type **Google Auth Platform** and open it. Click **Get started**.
   - **App name:** `Kip Tracker`. **User support email:** your email. Click **Next**.
   - **Audience:** choose **External**, then **Next**.
   - **Contact information:** your email, then **Next**.
   - Tick the agreement box, click **Continue**, then **Create**.
4. In the left menu, click **Audience**. Under **Test users**, click **Add users** and type your own Gmail address (later, your family's too). Click **Save**.
   *While the app stays in "Testing", only the people on this list can sign in at all, which adds an extra lock.*
5. In the left menu, click **Clients**, then **Create client**:
   - **Application type:** **Web application**. **Name:** `Kip Tracker`.
   - Under **Authorized redirect URIs**, click **Add URI**. To find the address to paste:
     - Keep this tab open. In Supabase, go to **Authentication** (person icon in the left sidebar), then **Sign In / Providers** (or **Providers**), then click **Google**.
     - Copy the **Callback URL (for OAuth)**, which looks like `https://abcdefgh.supabase.co/auth/v1/callback`.
     - Back in Google, paste it into the URI field.
   - Click **Create**. Google shows a **Client ID** and **Client secret**. Copy both.

### 2b. Turn on Google login in Supabase

1. You're still on the Supabase **Google** provider page. Switch **Enable Sign in with Google** on.
2. Paste the **Client ID** into **Client IDs** and the **Client secret** into **Client Secret (for OAuth)**.
3. Click **Save**.

## 3. Anthropic (Claude reads the receipts)

1. Go to **platform.claude.com** (also reachable from console.anthropic.com) and sign in with the same email as your Claude subscription.
2. **Check your credit first:** click **Billing** (in Settings).
   - If the balance shows credit (for example $100), great.
   - If it shows **$0.00**, your subscription credit is not available for the API. **Don't buy anything.** Tell Claude in the chat. The app can run on free Gemini only.
3. Click **API Keys**, then **Create Key**. Name it `kip-tracker` and click **Create**. Copy the key (starts with `sk-ant-`) as `ANTHROPIC_API_KEY`. It is shown only once.
4. Optional safety net: in **Limits**, set a monthly **spend limit** (e.g. $5). The app also stops using Claude at its own $5 monthly cap, which you can change later.

## 4. Google AI Studio (Gemini, the free backup)

1. Go to **aistudio.google.com** and sign in with your Google account.
2. Click **Get API key**, then **Create API key**. If asked for a project, choose `kip-tracker`.
3. Copy the key as `GEMINI_API_KEY`.
4. **Don't** click anything about billing or "upgrade". Staying on the free tier keeps it free. As agreed, Google may use what free-tier Gemini sees to improve its products. It's only used when Claude can't be.

## 5. Cloudflare (puts the website online)

*(Vercel's `vercel.app` addresses can't be reached from some internet providers in Laos, so the site runs on Cloudflare instead.)*

1. Go to https://dash.cloudflare.com/sign-up and create a free account (or sign in). **Don't add a payment method or pick a paid plan.**
2. Open **Workers & Pages** (https://dash.cloudflare.com/?to=/:account/workers-and-pages) and tap **Create**.
3. Choose **Import a repository** (or **Continue with GitHub**), connect GitHub, allow access to **Bcel-accounting**, and select it.
4. Fill in:
   - **Project name:** `bcel-accounting` (must be exactly this)
   - **Build command:** `npx opennextjs-cloudflare build`
   - **Deploy command:** `npx wrangler deploy`
5. Tap **Create and deploy** (or **Save and Deploy**) and wait about 3-5 minutes for the build to finish.
6. Open the Worker, then **Settings**, then **Variables and Secrets**. Tap **Add** and enter these five, choosing type **Secret** for each:
   - `SUPABASE_URL`
   - `SUPABASE_PUBLISHABLE_KEY`
   - `SUPABASE_SECRET_KEY`
   - `ANTHROPIC_API_KEY`
   - `GEMINI_API_KEY`

   Then tap **Deploy**.
7. Your address is shown under **Settings**, then **Domains & Routes**. It looks like `https://bcel-accounting.YOUR-NAME.workers.dev`. Open it and add `/setup-check` at the end to confirm every line shows a green tick.

## 6. Connect the address back to Supabase

1. In Supabase, go to **Authentication**, then **URL Configuration**.
2. **Site URL:** paste your Cloudflare address, e.g. `https://bcel-accounting.YOUR-NAME.workers.dev`. Click **Save**.
3. Under **Redirect URLs**, click **Add URL**, paste your address followed by `/auth/callback` (e.g. `https://bcel-accounting.YOUR-NAME.workers.dev/auth/callback`), and click **Save**.

## 7. First sign-in

1. Open your site address and tap **Sign in with Google**.
2. **The very first person to sign in becomes the admin.** Make sure that's you!
3. **Install it like an app:**
   - **iPhone (Safari):** tap the **Share** button (square with an arrow), then **Add to Home Screen**, then **Add**.
   - **Android (Chrome):** tap the **⋮** menu, then **Add to Home screen** (or **Install app**), then **Install**.

You're done. See **"How to test Stage 1"** in the README.

---

### If something goes wrong

- **"Waiting for approval" after signing in:** someone else signed in first and became admin. Tell Claude; it's fixable in a minute.
- **Google says "Access blocked" or "not a test user":** add that email under Google Auth Platform, then Audience, then Test users.
- **Google sign-in returns to the login page:** re-check step 6 (the Site URL and Redirect URL must match your Cloudflare address exactly, with `https://`).
- **Receipts say "could not be read":** open your site address with `/setup-check` at the end and fix any line marked with a red cross (Cloudflare: your Worker, then **Settings**, then **Variables and Secrets**).
