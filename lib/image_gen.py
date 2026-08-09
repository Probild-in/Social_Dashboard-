"""
Composites the creative (screenshot + price badge, for the anchor-price and
urgency templates) and uploads it to Vercel Blob so it has a public URL the
Graph API can fetch from.

For templates that need something other than a screenshot overlay (carousel
slides, generated local visuals), extend `composite_image()` — this covers
your two highest-volume formats (anchor_price_offer, urgency_slots) to start.
"""
import io
import os
import requests
from PIL import Image, ImageDraw, ImageFont
import vercel_blob

BASE_SCREENSHOT_URL = os.environ.get("PROBILD_SITE_SCREENSHOT_URL", "")


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype("/var/task/assets/Inter-Bold.ttf", size)
    except Exception:
        return ImageFont.load_default()


def composite_price_badge(screenshot_bytes: bytes, price: str, anchor_price: str) -> bytes:
    img = Image.open(io.BytesIO(screenshot_bytes)).convert("RGB")
    img = img.resize((1080, 1350))  # IG portrait aspect ratio

    draw = ImageDraw.Draw(img)
    badge_font = _load_font(64)
    strike_font = _load_font(36)

    # Price badge, bottom-left, brand green background (#22C55E, matches probild.in)
    draw.rectangle([(40, 1150), (600, 1300)], fill="#22C55E")
    draw.text((70, 1170), price, font=badge_font, fill="white")
    draw.line([(70, 1250), (260, 1250)], fill="white", width=3)
    draw.text((70, 1255), anchor_price, font=strike_font, fill="white")

    out = io.BytesIO()
    img.save(out, format="JPEG", quality=88)
    return out.getvalue()


def composite_image(asset_type: str, image_brief: str, variables: dict) -> bytes:
    if not BASE_SCREENSHOT_URL:
        raise RuntimeError("PROBILD_SITE_SCREENSHOT_URL not set — point it at a hosted site screenshot to overlay")

    screenshot_bytes = requests.get(BASE_SCREENSHOT_URL).content

    if asset_type in ("screenshot_overlay", "before_after_screenshot"):
        price = variables.get("price", "₹9,999")
        anchor = variables.get("anchor_price", "₹19,999")
        return composite_price_badge(screenshot_bytes, price, anchor)

    # Fallback: return the raw screenshot for now for unhandled asset types
    return screenshot_bytes


def upload_and_get_url(image_bytes: bytes, filename: str) -> str:
    result = vercel_blob.put(filename, image_bytes, {"addRandomSuffix": "true"})
    return result["url"]
