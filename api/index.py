"""
Single FastAPI app = single Vercel Function, handling every route. Vercel
auto-detects this via requirements.txt and loads the `app` variable.

Routes:
  POST /api/generate            — kick off content gen -> composite image -> Slack approval request
  POST /api/slack/interactive   — Slack button click webhook (ack instantly, hand off to QStash)
  POST /api/process-approval    — QStash-invoked: does the actual publish + boost
  GET  /api/cron/budget-check   — Vercel Cron: checks active ad sets, pauses underperformers
"""
import json
import os
import sys
import time
import uuid
from urllib.parse import parse_qs

from fastapi import FastAPI, Request, HTTPException

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import config
import store
import content_gen
import image_gen
import ig_publish
import meta_boost
from qstash_helper import enqueue_process_approval
from slack_verify import verify_slack_signature
from slack_sdk import WebClient

app = FastAPI()
slack_client = WebClient(token=config.SLACK_BOT_TOKEN)

ACTIVE_ADSETS_KEY = "active_ad_sets"
PENDING_REQUESTS_KEY = "pending_requests"
DECISIONS_LOG_KEY = "decisions_log"
PUBLISHED_POSTS_KEY = "published_posts"
BUDGET_CHECK_LOG_KEY = "budget_check_log"


def _check_dashboard_token(request: Request):
    token = request.query_params.get("token") or request.headers.get("x-dashboard-token")
    if not config.DASHBOARD_TOKEN or token != config.DASHBOARD_TOKEN:
        raise HTTPException(status_code=401, detail="invalid or missing dashboard token")


@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/api/generate")
async def generate(request: Request):
    body = await request.json()
    template_id = body.get("template_id", "anchor_price_offer")
    variables = body.get("variables", {})
    geo = body.get("geo", "delhi")

    draft = content_gen.generate_draft(template_id, variables)
    image_bytes = image_gen.composite_image(draft["asset_type"], draft["image_brief"], variables)
    image_url = image_gen.upload_and_get_url(image_bytes, f"{template_id}-{int(time.time())}.jpg")

    request_id = str(uuid.uuid4())[:8]
    created_at = int(time.time())
    store.set_json(
        f"draft:{request_id}",
        {**draft, "image_url": image_url, "geo": geo, "created_at": created_at},
        ttl_seconds=86400 * 3,
    )
    store.add_to_set(PENDING_REQUESTS_KEY, request_id)

    text = (
        f"*New Probild post ready for review* (`{request_id}`)\n"
        f"*Template:* {draft['template_name']}\n*Caption:*\n{draft['caption']}\n"
        f"*Hashtags:* {' '.join(draft['hashtags'])}"
    )
    slack_client.chat_postMessage(
        channel=config.SLACK_APPROVAL_CHANNEL,
        text=text,
        blocks=[
            {"type": "section", "text": {"type": "mrkdwn", "text": text}},
            {"type": "image", "image_url": image_url, "alt_text": "draft creative"},
            {
                "type": "actions",
                "block_id": f"approval_{request_id}",
                "elements": [
                    {"type": "button", "text": {"type": "plain_text", "text": "✅ Approve"},
                     "style": "primary", "action_id": "approve_post", "value": request_id},
                    {"type": "button", "text": {"type": "plain_text", "text": "❌ Reject"},
                     "style": "danger", "action_id": "reject_post", "value": request_id},
                ],
            },
        ],
    )
    return {"request_id": request_id, "status": "pending_approval"}


@app.post("/api/slack/interactive")
async def slack_interactive(request: Request):
    raw_body = (await request.body()).decode()
    timestamp = request.headers.get("x-slack-request-timestamp", "")
    signature = request.headers.get("x-slack-signature", "")

    if not verify_slack_signature(timestamp, raw_body, signature):
        raise HTTPException(status_code=401, detail="invalid signature")

    payload = json.loads(parse_qs(raw_body)["payload"][0])
    action = payload["actions"][0]
    request_id = action["value"]
    decision = "approved" if action["action_id"] == "approve_post" else "rejected"

    store.set_json(f"decision:{request_id}", {"decision": decision}, ttl_seconds=86400)
    store.remove_from_set(PENDING_REQUESTS_KEY, request_id)

    draft = store.get_json(f"draft:{request_id}") or {}
    store.rpush_json(DECISIONS_LOG_KEY, {
        "request_id": request_id,
        "decision": decision,
        "template_name": draft.get("template_name"),
        "timestamp": int(time.time()),
    })

    if decision == "approved":
        enqueue_process_approval(request_id)  # hand off — don't block this webhook response

    # Must respond fast — Slack requires an ack within 3s
    return {"text": f"{'✅ Approved' if decision == 'approved' else '❌ Rejected'} — processing..."}


@app.post("/api/process-approval")
async def process_approval(request: Request):
    body = await request.json()
    request_id = body["request_id"]

    draft = store.get_json(f"draft:{request_id}")
    if not draft:
        raise HTTPException(status_code=404, detail="draft not found or expired")

    media_id = ig_publish.publish_single_image(draft["image_url"], draft["caption"], draft["hashtags"])
    permalink = ig_publish.get_post_permalink(media_id)

    boost = meta_boost.create_boost_campaign(
        media_id=media_id,
        campaign_name=f"probild_{draft['template_id']}_{draft['geo']}_{request_id}",
        geo=draft["geo"],
    )
    store.add_to_set(ACTIVE_ADSETS_KEY, boost["ad_set_id"])
    store.rpush_json(PUBLISHED_POSTS_KEY, {
        "request_id": request_id,
        "template_name": draft.get("template_name"),
        "geo": draft.get("geo"),
        "permalink": permalink,
        "media_id": media_id,
        "ad_set_id": boost["ad_set_id"],
        "image_url": draft.get("image_url"),
        "timestamp": int(time.time()),
    })

    slack_client.chat_postMessage(
        channel=config.SLACK_APPROVAL_CHANNEL,
        text=f"Published: {permalink}\nBoost campaign created (PAUSED, review in Ads Manager): `{boost['ad_set_id']}`",
    )
    return {"status": "done", "permalink": permalink, "boost": boost}


@app.get("/api/cron/budget-check")
async def budget_check(request: Request):
    auth = request.headers.get("authorization", "")
    if config.CRON_SECRET and auth != f"Bearer {config.CRON_SECRET}":
        raise HTTPException(status_code=401, detail="unauthorized")

    ad_set_ids = store.get_set_members(ACTIVE_ADSETS_KEY)
    results = {}
    for ad_set_id in ad_set_ids:
        results[ad_set_id] = meta_boost.check_and_apply_budget_rule(ad_set_id)

    store.rpush_json(BUDGET_CHECK_LOG_KEY, {"timestamp": int(time.time()), "results": results})

    if any(v == "paused_underperforming" for v in results.values()):
        slack_client.chat_postMessage(
            channel=config.SLACK_APPROVAL_CHANNEL,
            text=f"Budget check results: {json.dumps(results, indent=2)}",
        )
    return results


@app.get("/api/dashboard-data")
async def dashboard_data(request: Request):
    _check_dashboard_token(request)

    pending_ids = store.get_set_members(PENDING_REQUESTS_KEY)
    pending = [store.get_json(f"draft:{rid}") | {"request_id": rid} for rid in pending_ids if store.get_json(f"draft:{rid}")]

    published = list(reversed(store.lrange_json(PUBLISHED_POSTS_KEY, -20, -1)))
    decisions = list(reversed(store.lrange_json(DECISIONS_LOG_KEY, -20, -1)))
    budget_log = list(reversed(store.lrange_json(BUDGET_CHECK_LOG_KEY, -10, -1)))

    active_ad_set_ids = store.get_set_members(ACTIVE_ADSETS_KEY)
    campaigns = [meta_boost.get_adset_summary(aid) for aid in active_ad_set_ids]

    return {
        "pending_approvals": pending,
        "published_posts": published,
        "recent_decisions": decisions,
        "campaigns": campaigns,
        "budget_check_log": budget_log,
    }
