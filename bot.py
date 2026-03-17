import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

from src.config import config
from src.handlers.reply_handler import handle_reply
from src.handlers.dm_handler import handle_dm
from src.services.database import init_db
from src.services.logger import get_logger

load_dotenv()
log = get_logger("bot")


def create_bot() -> commands.Bot:
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    return commands.Bot(
        command_prefix=config.prefix,
        intents=intents,
        help_command=None,
    )


bot = create_bot()


@bot.event
async def on_ready():
    log.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name="!help",
        )
    )


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if isinstance(message.channel, discord.DMChannel):
        if not message.content.startswith(config.prefix):
            await handle_dm(message)
        await bot.process_commands(message)
        return

    await bot.process_commands(message)

    if message.content.startswith(config.prefix):
        return

    # AI moderation — bot mentioned with a target user
    if message.guild and bot.user in message.mentions:
        has_target = any(m for m in message.mentions if not m.bot and m != bot.user)
        if has_target and message.author.guild_permissions.kick_members:
            mod_cog = bot.cogs.get("ModerationCog")
            if mod_cog:
                await mod_cog.process_ai_mod(message)
            return

    # reply-based AI conversation
    if message.reference:
        try:
            ref = await message.channel.fetch_message(message.reference.message_id)
            if ref.author.id == bot.user.id:
                await handle_reply(message)
        except discord.NotFound:
            pass


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.reply(f"⚠️ Missing argument: `{error.param.name}`", mention_author=False)
        return
    log.error(f"Command error in {ctx.command}: {error}")


async def main():
    await init_db()

    async with bot:
        await bot.load_extension("src.handlers.commands")
        await bot.load_extension("src.handlers.mod_commands")
        await bot.load_extension("src.handlers.admin_commands")
        await bot.load_extension("src.handlers.ticket_commands")
        await bot.load_extension("src.handlers.broadcast")
        await bot.load_extension("src.handlers.level_commands")

        token = os.getenv("DISCORD_TOKEN")
        if not token:
            raise RuntimeError("DISCORD_TOKEN is not set in .env")

        await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())