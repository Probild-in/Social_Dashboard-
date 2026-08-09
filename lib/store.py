"""
State store using Upstash Redis's REST API. Plain HTTPS requests — no
connection pooling needed, which is what makes it work cleanly in
serverless functions that spin up cold on every request.
"""
import json
import requests
import config

HEADERS = {"Authorization": f"Bearer {config.UPSTASH_REDIS_REST_TOKEN}"}


def set_json(key: str, value: dict, ttl_seconds: int | None = None):
    url = f"{config.UPSTASH_REDIS_REST_URL}/set/{key}"
    payload = json.dumps(value)
    params = {"EX": ttl_seconds} if ttl_seconds else {}
    resp = requests.post(url, headers=HEADERS, data=payload, params=params)
    resp.raise_for_status()


def get_json(key: str) -> dict | None:
    resp = requests.get(f"{config.UPSTASH_REDIS_REST_URL}/get/{key}", headers=HEADERS)
    resp.raise_for_status()
    result = resp.json().get("result")
    return json.loads(result) if result else None


def add_to_set(set_name: str, member: str):
    resp = requests.post(f"{config.UPSTASH_REDIS_REST_URL}/sadd/{set_name}/{member}", headers=HEADERS)
    resp.raise_for_status()


def get_set_members(set_name: str) -> list[str]:
    resp = requests.get(f"{config.UPSTASH_REDIS_REST_URL}/smembers/{set_name}", headers=HEADERS)
    resp.raise_for_status()
    return resp.json().get("result", [])


def remove_from_set(set_name: str, member: str):
    resp = requests.post(f"{config.UPSTASH_REDIS_REST_URL}/srem/{set_name}/{member}", headers=HEADERS)
    resp.raise_for_status()


def _command(command: list) -> dict:
    """Generic command execution for ops without a dedicated helper below —
    used for list operations where JSON values could contain characters
    that don't survive being embedded in a URL path."""
    resp = requests.post(config.UPSTASH_REDIS_REST_URL, headers=HEADERS, json=command)
    resp.raise_for_status()
    return resp.json()


def rpush_json(key: str, value: dict, max_len: int = 200):
    """Appends to a log list, trimmed to the most recent `max_len` entries
    (newest at the tail) so these logs don't grow unbounded."""
    _command(["RPUSH", key, json.dumps(value)])
    _command(["LTRIM", key, -max_len, -1])


def lrange_json(key: str, start: int = 0, end: int = -1) -> list[dict]:
    result = _command(["LRANGE", key, start, end]).get("result", [])
    return [json.loads(item) for item in result]
