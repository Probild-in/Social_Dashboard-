TEMPLATES = [
    {
        "id": "anchor_price_offer",
        "name": "Anchor-Price Offer",
        "brief": (
            "Write an Instagram caption for Probild, a website design/dev business "
            "for local small businesses. Offer: a full business website for ₹9,999 "
            "(anchor against ₹19,999, strike-through framing). Include mobile-ready "
            "and WhatsApp-button as included features. End with a clear WhatsApp CTA. "
            "Keep it punchy, under 80 words, no hashtags spam (max 3 relevant ones)."
        ),
        "asset_type": "screenshot_overlay",
        "cta": "whatsapp",
    },
    {
        "id": "pain_point_carousel",
        "name": "Pain-Point Educational",
        "brief": (
            "Write a 3-slide Instagram carousel (one short line per slide) on signs "
            "a local business website is losing customers: no mobile view, no WhatsApp "
            "button, looks outdated vs competitors. Slide 4 caption: soft CTA to DM 'FIX' "
            "for a free review. Tone: helpful, not salesy."
        ),
        "asset_type": "carousel_text_slides",
        "cta": "dm",
    },
    {
        "id": "proof_case_study",
        "name": "Proof / Case Study",
        "brief": (
            "Write an Instagram caption showcasing a before/after: a local business had "
            "no online presence, Probild built them a site in a short timeframe. "
            "Use a placeholder [CLIENT_NAME] and [TIMEFRAME] I'll fill in. End with "
            "'Want the same for your business?' CTA."
        ),
        "asset_type": "before_after_screenshot",
        "cta": "whatsapp",
    },
    {
        "id": "local_geo",
        "name": "Local-Flavor Geo-Tagged",
        "brief": (
            "Write a short, locally-flavored Instagram caption for [CITY] business "
            "owners, pointing out that competitors nearby likely already have a website "
            "and they might not. CTA: WhatsApp to get one built fast."
        ),
        "asset_type": "generated_local_visual",
        "cta": "whatsapp",
    },
    {
        "id": "urgency_slots",
        "name": "Urgency / Limited Slots",
        "brief": (
            "Write an Instagram caption: Probild is taking only 5 new website projects "
            "this month at the ₹9,999 launch price. Create genuine urgency without being "
            "spammy. CTA: message now to lock a slot."
        ),
        "asset_type": "screenshot_overlay",
        "cta": "whatsapp",
    },
]


def get_template(template_id: str) -> dict:
    for t in TEMPLATES:
        if t["id"] == template_id:
            return t
    raise ValueError(f"Unknown template id: {template_id}")
