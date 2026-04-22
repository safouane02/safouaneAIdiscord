# safouane02.github

import os
from groq import AsyncGroq
from src.services.logger import get_logger

log = get_logger("ticket_ai")

_SYSTEM_PROMPT = """You are a helpful support bot assistant for a Discord server.
Your job is to help users solve their issues in support tickets.

Rules:
- Be friendly, clear, and concise
- Try to solve the user's problem yourself first
- If you truly cannot help (need account access, server-specific info, payment issues, or complex technical problems), 
  respond with exactly this JSON: {"escalate": true, "reason": "brief reason"}
- Otherwise respond normally with helpful text
- Respond in the same language the user uses
- Keep responses under 400 words
"""


async def handle_ticket_message(conversation: list[dict]) -> tuple[str, bool]:
    """
    Returns (response_text, should_escalate)
    """
    client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            *conversation,
        ],
        max_tokens=600,
        temperature=0.5,
    )

    content = response.choices[0].message.content.strip()

    if content.startswith("{") and '"escalate": true' in content:
        import json
        try:
            parsed = json.loads(content)
            reason = parsed.get("reason", "complex issue")
            return reason, True
        except Exception:
            pass

    return content, False
