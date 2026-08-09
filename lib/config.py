import os

# --- Anthropic ---
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
CLAUDE_MODEL = "claude-sonnet-4-6"

# --- Slack ---
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_APPROVAL_CHANNEL = os.environ.get("SLACK_APPROVAL_CHANNEL", "#probild-content")
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]

# --- Meta ---
META_ACCESS_TOKEN = os.environ["META_ACCESS_TOKEN"]
IG_BUSINESS_ACCOUNT_ID = os.environ["IG_BUSINESS_ACCOUNT_ID"]
FB_PAGE_ID = os.environ["FB_PAGE_ID"]
AD_ACCOUNT_ID = os.environ["AD_ACCOUNT_ID"]
GRAPH_API_VERSION = "v21.0"
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

# --- Boost defaults ---
DEFAULT_DAILY_BUDGET_INR = 200
WHATSAPP_NUMBER = os.environ.get("WHATSAPP_NUMBER", "")
MIN_SPEND_BEFORE_PAUSE_CHECK_INR = 500
TARGET_CPL_INR = 150

GEO_PRESETS = {
    "delhi": {"type": "custom_location", "latitude": 28.6139, "longitude": 77.2090, "radius": 25, "distance_unit": "kilometer"},
    "dubai": {"type": "custom_location", "latitude": 25.2048, "longitude": 55.2708, "radius": 25, "distance_unit": "kilometer"},
}

# --- Upstash Redis (state store) --- auto-added when you connect Upstash via Vercel Marketplace
UPSTASH_REDIS_REST_URL = os.environ["UPSTASH_REDIS_REST_URL"]
UPSTASH_REDIS_REST_TOKEN = os.environ["UPSTASH_REDIS_REST_TOKEN"]

# --- Upstash QStash (async task queue) --- from console.upstash.com, separate from Redis
QSTASH_TOKEN = os.environ["QSTASH_TOKEN"]
QSTASH_CURRENT_SIGNING_KEY = os.environ["QSTASH_CURRENT_SIGNING_KEY"]

# --- Vercel Blob (image hosting) --- auto-added when you create a Blob store
BLOB_READ_WRITE_TOKEN = os.environ["BLOB_READ_WRITE_TOKEN"]

# Your deployed domain, e.g. https://probild-pipeline.vercel.app — needed so QStash
# knows where to call back. Set this yourself after your first deploy.
PUBLIC_BASE_URL = os.environ["PUBLIC_BASE_URL"]

# Vercel auto-injects this for Cron requests — used to verify cron calls are real
CRON_SECRET = os.environ.get("CRON_SECRET", "")

# Shared secret to view the dashboard — set your own value, put it in the
# dashboard URL as ?token=... Anyone with this token can see campaign spend
# and post drafts, so don't reuse a token you use elsewhere.
DASHBOARD_TOKEN = os.environ.get("DASHBOARD_TOKEN", "")
