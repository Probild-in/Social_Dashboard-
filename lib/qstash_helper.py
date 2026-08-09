from qstash import QStash
import config

qstash_client = QStash(config.QSTASH_TOKEN)


def enqueue_process_approval(request_id: str):
    """Called right after a Slack approval is recorded. Hands the actual
    publish+boost work to QStash, which reliably calls /api/process-approval
    (with retries on failure) — decoupled from the Slack webhook's 3s window."""
    qstash_client.message.publish_json(
        url=f"{config.PUBLIC_BASE_URL}/api/process-approval",
        body={"request_id": request_id},
        retries=3,
    )
