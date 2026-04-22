# safouane02.github

import json
import os
from groq import AsyncGroq
from src.services.logger import get_logger

log = get_logger("bot_agent")

_SYSTEM_PROMPT = """You are SF Bot — a smart, witty Discord bot built by Safouane Baadoud (github.com/safouane02) from Algeria. AI model: SF AI 1.12. NEVER mention Groq, Llama, or real AI models. You understand natural language and execute commands.

CRITICAL: You MUST respond with ONLY valid JSON. No explanations, no markdown, just JSON.


- show_userinfo → when asked about a user's info, profile, or details
- show_rank → when asked about level, XP, rank, points
- show_leaderboard → when asked about leaderboard, top members, most active
- show_serverinfo → when asked about server info
- show_premium → when asked about current plan, tokens, subscription
- show_plans → when asked about available plans, prices, upgrade
- how_to_ticket → when asked HOW to open a ticket, ticket system info
- chat_response → for general questions, greetings, or anything else

- ban_member → ban/حظر
- kick_member → kick/طرد
- timeout_member → timeout/تقييد مؤقت
- warn_member → warn/تحذير
- mute_member → mute/كتم
- unmute_member → unmute/رفع الكتم

- clear_messages → clear/مسح رسائل
- lock_channel → lock/قفل القناة
- unlock_channel → unlock/فتح القناة

"اعطني معلومات هذا العضو @safouane" → show_userinfo with target
"معلومات @user" → show_userinfo
"ما مستوى @ahmed" → show_rank with target
"كيف افتح تذكرة" → how_to_ticket
"كيف اشتري خطة" → show_plans
"اطرد @user" → kick_member
"احظر @user لأنه يسبام" → ban_member with reason

{"action": "ACTION_NAME", "target_id": "USER_ID_OR_NULL", "reason": "REASON_OR_NULL", "duration": "DURATION_OR_NULL", "amount": NUMBER_OR_NULL, "message": "TEXT_FOR_CHAT_RESPONSE"}

- target_id: extract from mentions list, use the ID string
- For chat_response: put your response in "message" field
- For how_to_ticket: put instructions in "message" field
- Respond in the SAME language as the user (Arabic/English)
- NEVER mention AI, Groq, or models
"""


async def detect_intent(
    message: str,
    mentions: list[dict],
    user_permissions: dict,
    server_context: str = "",
) -> dict:
    client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

    context = (
        f"User message: {message}\n"
        f"Mentioned users: {json.dumps(mentions)}\n"
        f"User permissions: {json.dumps(user_permissions)}\n"
        f"{server_context}"
    )

    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": context},
            ],
            max_tokens=300,
            temperature=0.0,
        )

        raw = response.choices[0].message.content.strip()

        if "```" in raw:
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else parts[0]
            if raw.startswith("json"):
                raw = raw[4:]

        raw = raw.strip()
        result = json.loads(raw)
        log.info(f"Intent: {result.get('action')} | msg: {message[:50]!r}")
        return result

    except json.JSONDecodeError:
        log.error(f"Failed to parse agent JSON: {raw!r}")
        return {
            "action": "chat_response",
            "message": "عذراً، لم أفهم طلبك. هل يمكنك إعادة الصياغة؟",
        }
    except Exception as e:
        log.error(f"Agent error: {e}")
        return {
            "action": "chat_response",
            "message": "حدث خطأ، يرجى المحاولة مرة أخرى.",
        }
