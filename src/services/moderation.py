# safouane02.github

import os
import json
import re
from groq import AsyncGroq
from src.services.logger import get_logger

log = get_logger("moderation")

VALID_ACTIONS = {
    "ban", "kick", "unban", "softban", "timeout", "untimeout",
    "warn", "mute", "unmute", "lock", "unlock", "nuke",
    "clear", "nick", "move", "disconnect", "role_add", "role_remove"
}

_INTENT_PROMPT = f"""
You are a Discord moderation AI assistant. Analyze the admin's message and detect moderation intent.

Extract ONLY:
- action: one of {sorted(VALID_ACTIONS)} — or null if none
- target_id: Discord user ID from mention like <@123> — or null
- reason: short reason if mentioned — or null
- duration: duration string if mentioned (e.g. "10m", "1h", "1d") — or null
- amount: number if relevant (e.g. for clear) — or null

Respond ONLY with valid JSON, nothing else. Examples:
{{"action": "ban", "target_id": "123456", "reason": "spamming", "duration": null, "amount": null}}
{{"action": "timeout", "target_id": "789012", "reason": "being rude", "duration": "1h", "amount": null}}
{{"action": "clear", "target_id": null, "reason": null, "duration": null, "amount": 10}}
{{"action": null, "target_id": null, "reason": null, "duration": null, "amount": null}}
"""


async def detect_moderation_intent(message: str) -> dict:
    client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
    mention_ids = re.findall(r"<@!?(\d+)>", message)

    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": _INTENT_PROMPT},
            {"role": "user", "content": f"Message: {message}\nMentioned IDs: {mention_ids}"},
        ],
        max_tokens=150,
        temperature=0.1,
    )

    raw = response.choices[0].message.content.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        log.error(f"Failed to parse intent: {raw}")
        return {"action": None, "target_id": None, "reason": None, "duration": None, "amount": None}


def parse_duration(duration_str: str) -> int:
    """Convert duration string to seconds. e.g. '10m' -> 600"""
    if not duration_str:
        return 0
    units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    match = re.match(r"(\d+)([smhd])", duration_str.lower())
    if match:
        value, unit = int(match.group(1)), match.group(2)
        return value * units.get(unit, 60)
    return 0
