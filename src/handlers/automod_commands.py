# safouane02.github

import os
import discord
from discord.ext import commands
from discord import app_commands

from src.services.automod import (
    get_automod_settings, save_automod_settings,
    check_spam, check_duplicate, check_banned_words,
    check_invite_link, check_caps,
)
from src.services.log_service import send_log, automod_log_embed, set_log_channel, get_log_channel
from src.services.logger import get_logger

log = get_logger("automod")


class AutoModCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="setlogchannel", description="Set the log channel for moderation events")
    @app_commands.describe(channel="The channel to send logs to")
    @app_commands.checks.has_permissions(administrator=True)
    async def setlogchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await set_log_channel(interaction.guild.id, channel.id)
        await interaction.response.send_message(
            f"✅ Log channel set to {channel.mention}", ephemeral=True
        )

    @app_commands.command(name="automod", description="Configure AutoMod settings")
    @app_commands.describe(
        enabled="Enable or disable AutoMod",
        spam="Enable spam detection",
        invites="Block Discord invite links",
        caps="Block excessive caps lock",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def automod_config(
        self,
        interaction: discord.Interaction,
        enabled: bool = None,
        spam: bool = None,
        invites: bool = None,
        caps: bool = None,
    ):
        updates = {}
        if enabled is not None:
            updates["enabled"] = int(enabled)
        if spam is not None:
            updates["spam_enabled"] = int(spam)
        if invites is not None:
            updates["invite_filter"] = int(invites)
        if caps is not None:
            updates["caps_filter"] = int(caps)

        if updates:
            await save_automod_settings(interaction.guild.id, **updates)

        settings = await get_automod_settings(interaction.guild.id)
        log_ch_id = await get_log_channel(interaction.guild.id)
        log_ch = interaction.guild.get_channel(log_ch_id) if log_ch_id else None

        embed = discord.Embed(title="🛡️ AutoMod Settings", color=0x5865F2)
        embed.add_field(name="Status", value="✅ Enabled" if settings["enabled"] else "❌ Disabled", inline=True)
        embed.add_field(name="Spam Filter", value="✅" if settings["spam_enabled"] else "❌", inline=True)
        embed.add_field(name="Invite Filter", value="✅" if settings["invite_filter"] else "❌", inline=True)
        embed.add_field(name="Caps Filter", value="✅" if settings["caps_filter"] else "❌", inline=True)
        embed.add_field(name="Banned Words", value=str(len(settings["banned_words"])), inline=True)
        embed.add_field(name="Log Channel", value=log_ch.mention if log_ch else "Not set", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="addword", description="Add a word to the banned words list")
    @app_commands.describe(word="The word to ban")
    @app_commands.checks.has_permissions(administrator=True)
    async def addword(self, interaction: discord.Interaction, word: str):
        settings = await get_automod_settings(interaction.guild.id)
        words = settings["banned_words"]
        if word.lower() in [w.lower() for w in words]:
            await interaction.response.send_message(f"⚠️ `{word}` is already banned.", ephemeral=True)
            return
        words.append(word.lower())
        await save_automod_settings(interaction.guild.id, banned_words=words)
        await interaction.response.send_message(f"✅ Added `{word}` to banned words.", ephemeral=True)

    @app_commands.command(name="removeword", description="Remove a word from the banned words list")
    @app_commands.describe(word="The word to unban")
    @app_commands.checks.has_permissions(administrator=True)
    async def removeword(self, interaction: discord.Interaction, word: str):
        settings = await get_automod_settings(interaction.guild.id)
        words = [w for w in settings["banned_words"] if w.lower() != word.lower()]
        await save_automod_settings(interaction.guild.id, banned_words=words)
        await interaction.response.send_message(f"✅ Removed `{word}` from banned words.", ephemeral=True)

    @app_commands.command(name="bannedwords", description="List all banned words")
    @app_commands.checks.has_permissions(administrator=True)
    async def bannedwords(self, interaction: discord.Interaction):
        settings = await get_automod_settings(interaction.guild.id)
        words = settings["banned_words"]
        if not words:
            await interaction.response.send_message("No banned words set.", ephemeral=True)
            return
        await interaction.response.send_message(
            f"🚫 Banned words ({len(words)}): `{'`, `'.join(words)}`",
            ephemeral=True,
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        if message.author.guild_permissions.administrator:
            return

        settings = await get_automod_settings(message.guild.id)
        if not settings["enabled"]:
            return

        content = message.content
        reason = None
        action = "Message deleted"

        if settings["banned_words"]:
            word = check_banned_words(content, settings["banned_words"])
            if word:
                reason = f"Banned word: `{word}`"

        if not reason and settings["invite_filter"] and check_invite_link(content):
            reason = "Discord invite link"

        if not reason and settings["caps_filter"] and check_caps(content):
            reason = "Excessive caps lock"

        if not reason and settings["spam_enabled"] and check_spam(message.guild.id, message.author.id):
            reason = "Spam detected"
            action = "Message deleted + warned"
            try:
                await message.author.send(
                    f"⚠️ You are sending messages too fast in **{message.guild.name}**. Please slow down."
                )
            except discord.Forbidden:
                pass

        if not reason and check_duplicate(message.guild.id, message.author.id, content):
            reason = "Duplicate message"

        if reason:
            try:
                await message.delete()
            except discord.NotFound:
                pass

            embed = automod_log_embed(reason, message.author, content, action)
            await send_log(message.guild, self.bot, embed)
            log.info(f"AutoMod: {reason} | {message.author} in #{message.channel.name}")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        from src.services.log_service import join_log_embed
        embed = join_log_embed(member)
        await send_log(member.guild, self.bot, embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        from src.services.log_service import leave_log_embed
        embed = leave_log_embed(member)
        await send_log(member.guild, self.bot, embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot or not message.guild or not message.content:
            return
        from src.services.log_service import message_delete_embed
        embed = message_delete_embed(message)
        await send_log(message.guild, self.bot, embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot or not before.guild:
            return
        if before.content == after.content:
            return
        from src.services.log_service import message_edit_embed
        embed = message_edit_embed(before, after)
        await send_log(before.guild, self.bot, embed)

    async def cog_app_command_error(self, interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("⛔ You need Administrator permission.", ephemeral=True)
        else:
            log.error(f"AutoMod slash error: {error}")


async def setup(bot: commands.Bot):
    await bot.add_cog(AutoModCog(bot))
