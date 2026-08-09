# Probild IG Pipeline — Vercel Deployment

Generate → Slack-approve → publish → boost, running entirely as Vercel
serverless functions. No server to manage, but a few pieces of external
infra are required because serverless functions are stateless and can't
block waiting for a Slack click.

## What you need to set up (in order)

### 1. Push this to a GitHub repo
Vercel deploys from Git. Create a repo, push this folder, then in the
Vercel dashboard: **Add New → Project → Import** your repo.

### 2. Connect Upstash Redis (state storage)
In your Vercel project → **Storage** tab → **Create Database** → choose
**Upstash** (via Marketplace) → Redis. This auto-adds `UPSTASH_REDIS_REST_URL`
and `UPSTASH_REDIS_REST_TOKEN` to your project's env vars — you don't set
these manually.

### 3. Connect Vercel Blob (image hosting)
Same **Storage** tab → **Create Database** → **Blob**. Auto-adds
`BLOB_READ_WRITE_TOKEN`.

### 4. Set up Upstash QStash (async task queue)
This is separate from Redis — go to [console.upstash.com](https://console.upstash.com) →
**QStash** → copy your `QSTASH_TOKEN` and `QSTASH_CURRENT_SIGNING_KEY`. This
handles the "publish + boost" work after a Slack approval, since Slack
requires your webhook to respond within 3 seconds and that's not enough
time to actually publish to Instagram and create ad campaigns.

### 5. Set the remaining environment variables
In Vercel project → **Settings → Environment Variables**, add:

| Variable | Where to get it |
|---|---|
| `ANTHROPIC_API_KEY` | console.anthropic.com |
| `SLACK_BOT_TOKEN` | Your Slack app → OAuth & Permissions (needs `chat:write`) |
| `SLACK_SIGNING_SECRET` | Your Slack app → Basic Information |
| `SLACK_APPROVAL_CHANNEL` | e.g. `#probild-content` |
| `META_ACCESS_TOKEN` | Meta Developer app, long-lived system-user token |
| `IG_BUSINESS_ACCOUNT_ID` | Meta Business Suite / Graph API Explorer |
| `FB_PAGE_ID` | Your linked Facebook Page |
| `AD_ACCOUNT_ID` | Format `act_1234567890` |
| `WHATSAPP_NUMBER` | e.g. `91XXXXXXXXXX` |
| `PROBILD_SITE_SCREENSHOT_URL` | A hosted screenshot of a demo site to overlay pricing on |
| `PUBLIC_BASE_URL` | Set **after** your first deploy — see step 7 |
| `DASHBOARD_TOKEN` | Any random string you choose — protects `/dashboard.html` |

### 6. First deploy
```bash
npm i -g vercel
vercel login
vercel link          # links this folder to your Vercel project
vercel --prod
```
You'll get a URL like `https://probild-pipeline.vercel.app`.

### 7. Set `PUBLIC_BASE_URL`
Go back to env vars and set `PUBLIC_BASE_URL` to that deployed URL, then
redeploy (`vercel --prod`) so it's picked up. QStash needs this to know
where to call back.

### 8. Point Slack at your deployment
In your Slack app config → **Interactivity & Shortcuts** → turn on, set
Request URL to:
```
https://probild-pipeline.vercel.app/api/slack/interactive
```

### 9. Trigger your first post
```bash
curl -X POST https://probild-pipeline.vercel.app/api/generate \
  -H "Content-Type: application/json" \
  -d '{"template_id": "anchor_price_offer", "geo": "delhi"}'
```
This generates the draft, composites the image, uploads it to Blob, and
posts it to your Slack channel with Approve/Reject buttons. Click Approve
→ QStash calls `/api/process-approval` → publishes to Instagram and creates
a **paused** boost campaign → posts the result back to Slack.

## Dashboard

A single-page dashboard lives at `/dashboard.html` on your deployment
(e.g. `https://probild-pipeline.vercel.app/dashboard.html`), showing in one
place:

- **Active ad campaigns** — live status, daily budget, spend, conversations, CPL (pulled fresh from Meta on each load)
- **Pending approvals** — drafts waiting on a Slack decision, with the creative and caption
- **Recently published** — last 20 posts with links to the live post and the ad set that's boosting it
- **Recent approval decisions** — approve/reject history
- **Budget check history** — what the cron job found and paused, over time

Set a `DASHBOARD_TOKEN` env var (any random string you choose) — the
dashboard asks for it once and stores it in the browser's local storage.
Anyone with the token can see campaign spend and draft captions, so treat
it like a password and don't reuse one from elsewhere. For anything more
sensitive than a solo/small-team internal tool, layer on
[Vercel's built-in Deployment Protection](https://vercel.com/docs/deployment-protection)
as well.

The dashboard auto-refreshes every 30 seconds — no build step, no extra
dependencies, it's a static HTML file Vercel serves directly from `/public`.

## Important limits to know

- **Cron frequency**: the included `vercel.json` runs the budget-check
  every 6 hours — this requires a **Pro plan**. On the free Hobby plan,
  cron jobs are capped at once per day and max 2 jobs total; change the
  schedule to `"0 9 * * *"` (once daily) if you're on Hobby.
- **Function duration**: set to 60s in `vercel.json`. Image compositing +
  the IG publish + boost campaign creation should comfortably fit, but if
  you add heavier image generation, you may need a Pro plan for longer
  durations.
- **Boost campaigns land PAUSED** — nothing spends until you manually
  review targeting in Ads Manager and flip it live. Keep this gate until
  you've got a few weeks of CPL data you trust.
- **`PROBILD_SITE_SCREENSHOT_URL`** currently points to one static
  screenshot for all posts. Swap in a rotation or per-client screenshots
  as you build out the case-study template.

## Local testing before deploying
```bash
pip install -r requirements.txt
cd api && vercel dev   # or: uvicorn index:app --reload, with lib/ on PYTHONPATH
```
