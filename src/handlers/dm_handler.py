# safouane02.github

import os
import discord
import traceback
from src.services.groq_service import ask_groq, TokenLimitError
from src.services.history import get_history, add_message, get_personality
from src.services.rate_limiter import is_rate_limited, remaining_cooldown
from src.services.whitelist import is_allowed
from src.services.logger import get_logger

log = get_logger("dm_handler")


async def handle_dm(message: discord.Message):
    user_id = message.author.id
    owner_id = int(os.getenv("OWNER_ID", "0"))

    if not is_allowed(user_id, owner_id):
        await message.channel.send(
            "⛔ Sorry, I only respond to whitelisted users in DMs.\n"
            "Ask the bot owner to add you using `!add`."
        )
        log.info(f"Blocked DM from non-whitelisted user {message.author} ({user_id})")
        return

    if is_rate_limited(user_id):
        wait = remaining_cooldown(user_id)
        await message.channel.send(f"⏳ Slow down! Try again in **{wait}s**.")
        return

    user_input = message.content.strip()
    if not user_input:
        return

    async with message.channel.typing():
        try:
            history = get_history(user_id)
            system_prompt = get_personality(user_id)
            reply = await ask_groq(user_input, history, system_prompt)

            add_message(user_id, "user", user_input)
            add_message(user_id, "assistant", reply)

            log.info(f"Processed DM from user_id={user_id}")

            for chunk in _split(reply):
                await message.channel.send(chunk)

        except TokenLimitError as e:
            await message.channel.send(str(e))
        except Exception as e:
            log.error(f"DM handler error for {user_id}: {e}\n{traceback.format_exc()}")
            await message.channel.send("⚠️ Something went wrong, please try again.")


def _split(text: str, limit: int = 1900) -> list[str]:
    return [text[i: i + limit] for i in range(0, len(text), limit)]
