import hashlib
import hmac
import time
import config


def verify_slack_signature(timestamp: str, body: str, signature: str) -> bool:
    if abs(time.time() - int(timestamp)) > 60 * 5:
        return False  # stale request, possible replay

    basestring = f"v0:{timestamp}:{body}"
    computed = "v0=" + hmac.new(
        config.SLACK_SIGNING_SECRET.encode(), basestring.encode(), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(computed, signature)
