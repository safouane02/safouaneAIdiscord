import os
import re
from groq import AsyncGroq
from src.services.logger import get_logger
from src.services.key_pool import pool
from src.services import cache as response_cache
from src.services.prompt_builder import build_prompt

log = get_logger("groq_service")

MODELS = {
    "fast":     "meta-llama/llama-4-scout-17b-16e-instruct",
    "light":    "openai/gpt-4o-mini",
    "balanced": "llama-3.3-70b-versatile",
    "smart":    "moonshotai/kimi-k2-instruct",
    "heavy":    "openai/gpt-4o",
}

_COMPLEX = [
    "explain", "why", "how does", "how do", "difference between", "compare",
    "analyze", "implement", "algorithm", "architecture", "debug", "optimize",
    "design", "write", "create", "build", "generate", "develop",
    "اشرح", "لماذا", "كيف يعمل", "الفرق", "قارن", "حلل", "نفذ",
    "اكتب", "انشئ", "ابني", "طور", "خوارزمية",
]

_SIMPLE = [
    "what is", "who is", "when", "where", "define", "name",
    "ما هو", "من هو", "متى", "أين", "عرف", "هل", "كم",
]


def _pick_model(message: str) -> str:
    msg = message.lower()
    words = msg.split()
    n = len(words)
    has_code = "```" in message or bool(
        re.search(r"\b(def |class |import |SELECT |CREATE |async def )\b", message)
    )

    if has_code or n > 60:
        return MODELS["heavy"]

    is_complex = any(k in msg for k in _COMPLEX)
    is_simple = any(k in msg for k in _SIMPLE)

    if is_complex and n >= 4:
        return MODELS["smart"]
    if is_complex:
        return MODELS["balanced"]
    if is_simple and n <= 10:
        return MODELS["fast"]
    if n <= 4:
        return MODELS["fast"]
    if n <= 15:
        return MODELS["light"]

    return MODELS["balanced"]


def _compress_history(history: list[dict], max_pairs: int = 4) -> list[dict]:
    """Keep only the last N exchanges to reduce token usage."""
    if len(history) <= max_pairs * 2:
        return history
    return history[-(max_pairs * 2):]


class TokenLimitError(Exception):
    pass


async def ask_groq(
    user_message: str,
    history: list[dict] = None,
    system_prompt: str = None,
    server_context: str = None,
    use_cache: bool = True,
    guild_id: int = None,
) -> str:
    # check cache for short/simple questions with no history
    if use_cache and not history:
        cached = response_cache.get(user_message)
        if cached:
            log.info(f"Cache hit for: {user_message[:50]!r}")
            return cached

    # build minimal relevant prompt
    smart_prompt = build_prompt(user_message, system_prompt)
    if server_context:
        smart_prompt = f"{smart_prompt}\n\n{server_context}"

    # use premium model if server has premium
    if guild_id:
        try:
            from src.services.premium import get_features
            features = await get_features(guild_id)
            premium_model = features.get("ai_model")
            if premium_model and premium_model in MODELS:
                model = MODELS[premium_model]
            else:
                model = _pick_model(user_message)
        except Exception:
            model = _pick_model(user_message)
    else:
        model = _pick_model(user_message)
    compressed_history = _compress_history(history or [])

    messages = [
        {"role": "system", "content": smart_prompt},
        *compressed_history,
        {"role": "user", "content": user_message},
    ]

    # check daily token limit
    if guild_id:
        try:
            from src.services.premium import check_token_limit, add_token_usage, get_plan, WEBSITE_URL
            can_use, used, limit = await check_token_limit(guild_id)
            if not can_use:
                plan = await get_plan(guild_id)
                raise TokenLimitError(
                    f"⚠️ لقد وصل السيرفر لحد الـ AI اليومي (**{limit:,}** token)\n"
                    f"الخطة الحالية: **{plan['name']} {plan['emoji']}**\n"
                    f"للترقية وزيادة الحد: **{WEBSITE_URL}**"
                )
        except TokenLimitError:
            raise
        except Exception as e:
            log.warning(f"Token limit check failed: {e}")

    api_key = pool.next_key()
    client = AsyncGroq(api_key=api_key)

    log.info(
        f"Model: {model.split('/')[-1]} | "
        f"Key #{pool._current_index}/{pool.count} | "
        f"Msg: {user_message[:40]!r}"
    )

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=1024,
            temperature=0.7,
        )
        answer = response.choices[0].message.content

        # track token usage
        if guild_id:
            try:
                from src.services.premium import add_token_usage
                tokens_used = response.usage.total_tokens if response.usage else len(answer.split()) * 2
                await add_token_usage(guild_id, tokens_used)
            except Exception:
                pass

        # cache only if no history (generic question)
        if use_cache and not history:
            response_cache.set(user_message, answer)

        return answer

    except Exception as e:
        if model != MODELS["balanced"]:
            log.warning(f"Model {model} failed ({e}), falling back to balanced")
            fallback_key = pool.next_key()
            client = AsyncGroq(api_key=fallback_key)
            response = await client.chat.completions.create(
                model=MODELS["balanced"],
                messages=messages,
                max_tokens=1024,
                temperature=0.7,
            )
            return response.choices[0].message.content
        raise