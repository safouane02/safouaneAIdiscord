import discord
from src.services.groq_service import ask_groq
from src.services.history import get_history, add_message, get_personality
from src.services.rate_limiter import is_rate_limited, remaining_cooldown
from src.services.context_builder import build_server_context
from src.services.logger import get_logger

log = get_logger("reply_handler")


async def handle_reply(message: discord.Message):
    user_input = message.content.strip()
    if not user_input:
        return

    user_id = message.author.id

    if is_rate_limited(user_id):
        wait = remaining_cooldown(user_id)
        await message.reply(f"⏳ Slow down! Try again in **{wait}s**.", mention_author=False)
        return

    async with message.channel.typing():
        try:
            history = get_history(user_id)
            system_prompt = get_personality(user_id)
            server_context = await build_server_context(message)

            guild_id = message.guild.id if message.guild else None
            reply = await ask_groq(user_input, history, system_prompt, server_context, guild_id=guild_id)

            add_message(user_id, "user", user_input)
            add_message(user_id, "assistant", reply)

            log.info(f"Reply to {message.author} ({user_id}): {user_input[:60]!r}")

            for chunk in _split_message(reply):
                await message.reply(chunk, mention_author=False)

        except Exception as e:
            from src.services.groq_service import TokenLimitError
            if isinstance(e, TokenLimitError):
                await message.reply(str(e), mention_author=False)
            else:
                log.error(f"Reply handler error for {user_id}: {e}")
                await message.reply("⚠️ Something went wrong, please try again.", mention_author=False)


def _split_message(text: str, limit: int = 1900) -> list[str]:
    return [text[i: i + limit] for i in range(0, len(text), limit)]