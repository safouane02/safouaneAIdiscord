# safouane02.github

import os
import discord
from discord.ext import commands
from src.services.whitelist import add_user, remove_user, list_users
from src.services.logger import get_logger

log = get_logger("admin_commands")

_pending_add: dict[int, int] = {}
_pending_remove: dict[int, int] = {}


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _is_owner(self, user_id: int) -> bool:
        return user_id == int(os.getenv("OWNER_ID", "0"))

    @commands.command(name="add")
    async def add_to_whitelist(self, ctx: commands.Context, member: discord.Member = None):
        if not self._is_owner(ctx.author.id):
            await ctx.reply("⛔ Only the bot owner can use this command.", mention_author=False)
            return

        if not member:
            await ctx.reply("Usage: `!add @user`", mention_author=False)
            return

        _pending_add[ctx.author.id] = member.id

        try:
            await ctx.author.send(
                f"🔐 To add **{member}** to the DM whitelist, reply with the password."
            )
            await ctx.reply("📩 Check your DMs to confirm.", mention_author=False)
        except discord.Forbidden:
            await ctx.reply("⚠️ I can't DM you. Please enable DMs from server members.", mention_author=False)

    @commands.command(name="remove")
    async def remove_from_whitelist(self, ctx: commands.Context, member: discord.Member = None):
        if not self._is_owner(ctx.author.id):
            await ctx.reply("⛔ Only the bot owner can use this command.", mention_author=False)
            return

        if not member:
            await ctx.reply("Usage: `!remove @user`", mention_author=False)
            return

        if remove_user(member.id):
            await ctx.reply(f"✅ **{member}** removed from DM whitelist.", mention_author=False)
        else:
            await ctx.reply(f"⚠️ **{member}** was not in the whitelist.", mention_author=False)

    @commands.command(name="whitelist")
    async def show_whitelist(self, ctx: commands.Context):
        if not self._is_owner(ctx.author.id):
            await ctx.reply("⛔ Only the bot owner can use this command.", mention_author=False)
            return

        users = list_users()
        if not users:
            await ctx.reply("📋 The DM whitelist is empty.", mention_author=False)
            return

        lines = []
        for uid in users:
            user = ctx.bot.get_user(uid)
            label = str(user) if user else f"Unknown ({uid})"
            lines.append(f"• {label} — `{uid}`")

        embed = discord.Embed(
            title="📋 DM Whitelist",
            description="\n".join(lines),
            color=0x5865F2,
        )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if not isinstance(message.channel, discord.DMChannel):
            return

        if message.content.startswith("!"):
            return

        user_id = message.author.id

        if user_id in _pending_add:
            correct_password = os.getenv("WHITELIST_PASSWORD", "changeme")

            if message.content.strip() == correct_password:
                target_id = _pending_add.pop(user_id)
                target = message.guild if hasattr(message, "guild") else None

                if add_user(target_id):
                    user_obj = self.bot.get_user(target_id)
                    name = str(user_obj) if user_obj else str(target_id)
                    await message.reply(f"✅ **{name}** has been added to the DM whitelist.")
                    log.info(f"Owner added user {target_id} to whitelist")
                else:
                    await message.reply("⚠️ That user is already in the whitelist.")
            else:
                _pending_add.pop(user_id, None)
                await message.reply("❌ Wrong password. Request cancelled.")


async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))
