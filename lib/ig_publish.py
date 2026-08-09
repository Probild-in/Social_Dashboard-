import time
import requests
import config


def publish_single_image(image_url: str, caption: str, hashtags: list[str]) -> str:
    full_caption = f"{caption}\n\n{' '.join(hashtags)}"

    container_resp = requests.post(
        f"{config.GRAPH_BASE}/{config.IG_BUSINESS_ACCOUNT_ID}/media",
        data={"image_url": image_url, "caption": full_caption, "access_token": config.META_ACCESS_TOKEN},
    )
    container_resp.raise_for_status()
    creation_id = container_resp.json()["id"]

    time.sleep(3)

    publish_resp = requests.post(
        f"{config.GRAPH_BASE}/{config.IG_BUSINESS_ACCOUNT_ID}/media_publish",
        data={"creation_id": creation_id, "access_token": config.META_ACCESS_TOKEN},
    )
    publish_resp.raise_for_status()
    return publish_resp.json()["id"]


def get_post_permalink(media_id: str) -> str:
    resp = requests.get(
        f"{config.GRAPH_BASE}/{media_id}",
        params={"fields": "permalink", "access_token": config.META_ACCESS_TOKEN},
    )
    resp.raise_for_status()
    return resp.json()["permalink"]
