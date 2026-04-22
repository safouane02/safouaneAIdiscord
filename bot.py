# safouane02.github

import os
import asyncio
import threading
import uvicorn
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()

from src.config import config
from src.handlers.reply_handler import handle_reply
from src.handlers.dm_handler import handle_dm
from src.services.database import init_db
from src.services.premium import init_premium_table
from src.services.reaction_roles import init_reaction_roles_table
from src.services.backup import create_backup, backup_loop
from src.services.logger import get_logger

log = get_logger("bot")


EXTENSIONS = [
    "src.handlers.commands",
    "src.handlers.mod_commands",
    "src.handlers.admin_commands",
    "src.handlers.ticket_commands",
    "src.handlers.broadcast",
    "src.handlers.level_commands",
    "src.handlers.automod_commands",
    "src.handlers.slash_mod",
    "src.handlers.welcome",
    "src.handlers.reaction_roles",
    "src.handlers.premium_commands",
]


def create_bot() -> commands.Bot:
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.reactions = True

    return commands.Bot(
        command_prefix=config.prefix,
        intents=intents,
        help_command=None,
    )


bot = create_bot()

@tasks.loop(minutes=5)
async def connection_watchdog():
    if bot.is_closed() or bot.latency > 15.0:
        log.critical(f"Zombie connection detected (Latency: {bot.latency})! Exiting process to let Render restart...")
        os._exit(1)

@connection_watchdog.before_loop
async def before_watchdog():
    await bot.wait_until_ready()

@bot.command(name="sync_commands", aliases=["sync"])
@commands.is_owner()
async def sync_commands(ctx):
    """Sync slash commands manually. Usage: !sync_commands"""
    msg = await ctx.send("Syncing...")
    try:
        synced = await bot.tree.sync()
        await msg.edit(content=f"✅ Synced {len(synced)} slash commands!")
    except Exception as e:
        await msg.edit(content=f"❌ Failed to sync: {e}")

def start_api():
    """Run FastAPI in a background thread."""
    try:
        import api
        api.set_bot(bot)
        port = int(os.getenv("API_PORT", "8000"))
        uvicorn.run(api.app, host="0.0.0.0", port=port, log_level="warning")
    except Exception as e:
        log.error(f"API server error: {e}")


@bot.event
async def on_ready():
    log.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    log.info(f"Serving {len(bot.guilds)} servers")


    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name="/help",
        )
    )

    create_backup()
    bot.loop.create_task(backup_loop())
    
    if not connection_watchdog.is_running():
        connection_watchdog.start()


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

    if message.guild and bot.user in message.mentions:
        has_target = any(m for m in message.mentions if not m.bot and m != bot.user)
        if has_target and message.author.guild_permissions.kick_members:
            mod_cog = bot.cogs.get("ModerationCog")
            if mod_cog:
                await mod_cog.process_ai_mod(message)
            return

    if message.reference:
        try:
            ref = await message.channel.fetch_message(message.reference.message_id)
            if ref.author.id == bot.user.id:
                await handle_reply(message)
                return
        except discord.NotFound:
            pass


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("⛔ You don't have permission.", mention_author=False)
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.reply(f"⚠️ Missing: `{error.param.name}`", mention_author=False)
        return
    log.error(f"Command error in {ctx.command}: {error}")


async def main():
    await init_db()
    await init_premium_table()
    await init_reaction_roles_table()

    if os.getenv("ENABLE_API", "true").lower() == "true":
        api_thread = threading.Thread(target=start_api, daemon=True)
        api_thread.start()
        log.info(f"API server started on port {os.getenv('API_PORT', '8000')}")

    async with bot:
        for ext in EXTENSIONS:
            try:
                await bot.load_extension(ext)
                log.info(f"Loaded {ext.split('.')[-1]}")
            except Exception as e:
                log.error(f"Failed to load {ext}: {e}")

        token = os.getenv("DISCORD_TOKEN")
        if not token:
            raise RuntimeError("DISCORD_TOKEN is not set. Please add it to your .env file or Discloud Dashboard Secrets.")

        await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
