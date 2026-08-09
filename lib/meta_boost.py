import requests
import config


def _post(path: str, data: dict) -> dict:
    resp = requests.post(f"{config.GRAPH_BASE}/{path}", data={**data, "access_token": config.META_ACCESS_TOKEN})
    resp.raise_for_status()
    return resp.json()


def create_boost_campaign(media_id: str, campaign_name: str, geo: str = "delhi", daily_budget_inr: int | None = None) -> dict:
    daily_budget_inr = daily_budget_inr or config.DEFAULT_DAILY_BUDGET_INR
    geo_target = config.GEO_PRESETS[geo]

    campaign = _post(f"{config.AD_ACCOUNT_ID}/campaigns", {
        "name": campaign_name,
        "objective": "OUTCOME_ENGAGEMENT",
        "status": "PAUSED",
        "special_ad_categories": "[]",
    })

    targeting = {
        "geo_locations": {"custom_locations": [geo_target]},
        "age_min": 24,
        "age_max": 55,
        "flexible_spec": [{"interests": [{"name": "Small business"}, {"name": "Entrepreneurship"}]}],
        "exclusions": {"behaviors": [{"name": "Student"}]},
    }
    ad_set = _post(f"{config.AD_ACCOUNT_ID}/adsets", {
        "name": f"{campaign_name} - {geo}",
        "campaign_id": campaign["id"],
        "daily_budget": daily_budget_inr * 100,
        "billing_event": "IMPRESSIONS",
        "optimization_goal": "CONVERSATIONS",
        "destination_type": "WHATSAPP",
        "promoted_object": {"page_id": config.FB_PAGE_ID, "whatsapp_number": config.WHATSAPP_NUMBER},
        "targeting": targeting,
        "status": "PAUSED",
    })

    creative = _post(f"{config.AD_ACCOUNT_ID}/adcreatives", {
        "name": f"{campaign_name} creative",
        "object_story_id": f"{config.FB_PAGE_ID}_{media_id}",
    })
    ad = _post(f"{config.AD_ACCOUNT_ID}/ads", {
        "name": campaign_name,
        "adset_id": ad_set["id"],
        "creative": f'{{"creative_id":"{creative["id"]}"}}',
        "status": "PAUSED",
    })

    return {"campaign_id": campaign["id"], "ad_set_id": ad_set["id"], "ad_id": ad["id"]}


def get_adset_summary(ad_set_id: str) -> dict:
    """Pulls live status + spend + CPL for one ad set — used by the dashboard."""
    status_resp = requests.get(
        f"{config.GRAPH_BASE}/{ad_set_id}",
        params={"fields": "name,status,daily_budget", "access_token": config.META_ACCESS_TOKEN},
    ).json()

    insights_resp = requests.get(
        f"{config.GRAPH_BASE}/{ad_set_id}/insights",
        params={"fields": "spend,actions", "access_token": config.META_ACCESS_TOKEN},
    ).json()

    spend = 0.0
    conversations = 0
    if insights_resp.get("data"):
        row = insights_resp["data"][0]
        spend = float(row.get("spend", 0))
        conversations = int(next(
            (a["value"] for a in row.get("actions", []) if a["action_type"] == "onsite_conversion.messaging_conversation_started_7d"),
            0,
        ) or 0)

    cpl = round(spend / conversations, 2) if conversations else None

    return {
        "ad_set_id": ad_set_id,
        "name": status_resp.get("name"),
        "status": status_resp.get("status"),
        "daily_budget_inr": int(status_resp.get("daily_budget", 0)) / 100 if status_resp.get("daily_budget") else None,
        "spend_inr": spend,
        "conversations": conversations,
        "cpl_inr": cpl,
    }


def check_and_apply_budget_rule(ad_set_id: str) -> str:
    insights = requests.get(
        f"{config.GRAPH_BASE}/{ad_set_id}/insights",
        params={"fields": "spend,actions", "access_token": config.META_ACCESS_TOKEN},
    ).json()

    if not insights.get("data"):
        return "no_data_yet"

    row = insights["data"][0]
    spend = float(row.get("spend", 0))
    conversations = next(
        (a["value"] for a in row.get("actions", []) if a["action_type"] == "onsite_conversion.messaging_conversation_started_7d"),
        0,
    )
    conversations = int(conversations) if conversations else 0

    if spend < config.MIN_SPEND_BEFORE_PAUSE_CHECK_INR:
        return "sample_too_small"

    if conversations == 0 or (spend / max(conversations, 1)) > config.TARGET_CPL_INR * 1.5:
        _post(ad_set_id, {"status": "PAUSED"})
        return "paused_underperforming"

    return "performing_within_target"
