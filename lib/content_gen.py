import json
import anthropic
import config
from templates import get_template

client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


def generate_draft(template_id: str, variables: dict | None = None) -> dict:
    template = get_template(template_id)
    variables = variables or {}

    prompt = f"""{template['brief']}

Variables to use if placeholders appear in the brief: {json.dumps(variables)}

Respond ONLY with JSON, no markdown fences, in this exact shape:
{{
  "caption": "...",
  "hashtags": ["...", "..."],
  "image_brief": "one sentence describing what the accompanying image/carousel should show"
}}"""

    resp = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = resp.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    draft = json.loads(raw)

    return {
        "template_id": template_id,
        "template_name": template["name"],
        "asset_type": template["asset_type"],
        "cta": template["cta"],
        "caption": draft["caption"],
        "hashtags": draft.get("hashtags", []),
        "image_brief": draft["image_brief"],
    }
