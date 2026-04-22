# safouane02.github

import discord
from discord import app_commands
from discord.ext import commands

from src.services.reaction_roles import (
    add_reaction_role, remove_reaction_role,
    get_role_for_reaction, get_all_reaction_roles,
)
from src.services.logger import get_logger

log = get_logger("reaction_roles")


class ReactionRolesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="reactionrole", description="Add or remove a reaction role")
    @app_commands.describe(
        action="add or remove",
        message_id="ID of the message",
        emoji="The emoji to react with",
        role="The role to assign",
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="add", value="add"),
        app_commands.Choice(name="remove", value="remove"),
        app_commands.Choice(name="list", value="list"),
    ])
    @app_commands.checks.has_permissions(administrator=True)
    async def reactionrole(
        self,
        interaction: discord.Interaction,
        action: str,
        message_id: str = None,
        emoji: str = None,
        role: discord.Role = None,
    ):
        guild_id = interaction.guild.id

        if action == "list":
            entries = await get_all_reaction_roles(guild_id)
            if not entries:
                await interaction.response.send_message("No reaction roles set.", ephemeral=True)
                return

            lines = []
            for e in entries:
                r = interaction.guild.get_role(e["role_id"])
                role_text = r.mention if r else f"Deleted ({e['role_id']})"
                lines.append(f"{e['emoji']} → {role_text} (msg: `{e['message_id']}`)")

            embed = discord.Embed(
                title="🎭 Reaction Roles",
                description="\n".join(lines),
                color=0x5865F2,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if not message_id or not emoji:
            await interaction.response.send_message(
                "⚠️ Please provide `message_id` and `emoji`.", ephemeral=True
            )
            return

        try:
            msg_id = int(message_id)
        except ValueError:
            await interaction.response.send_message("⚠️ Invalid message ID.", ephemeral=True)
            return

        if action == "add":
            if not role:
                await interaction.response.send_message("⚠️ Please provide a role.", ephemeral=True)
                return

            msg = None
            for channel in interaction.guild.text_channels:
                try:
                    msg = await channel.fetch_message(msg_id)
                    break
                except Exception:
                    continue

            if not msg:
                await interaction.response.send_message("⚠️ Message not found.", ephemeral=True)
                return

            await add_reaction_role(guild_id, msg_id, emoji, role.id)

            try:
                await msg.add_reaction(emoji)
            except Exception:
                pass

            await interaction.response.send_message(
                f"✅ Reaction role added: {emoji} → {role.mention}",
                ephemeral=True,
            )
            log.info(f"Reaction role added: {emoji} → {role.name} on msg {msg_id}")

        elif action == "remove":
            await remove_reaction_role(guild_id, msg_id, emoji)
            await interaction.response.send_message(
                f"✅ Removed reaction role for {emoji} on message `{msg_id}`",
                ephemeral=True,
            )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        emoji = str(payload.emoji)
        role_id = await get_role_for_reaction(guild.id, payload.message_id, emoji)
        if not role_id:
            return

        role = guild.get_role(role_id)
        member = guild.get_member(payload.user_id)

        if role and member:
            try:
                await member.add_roles(role, reason="Reaction role")
                log.info(f"Added role {role.name} to {member} via reaction")
            except discord.Forbidden:
                pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        emoji = str(payload.emoji)
        role_id = await get_role_for_reaction(guild.id, payload.message_id, emoji)
        if not role_id:
            return

        role = guild.get_role(role_id)
        member = guild.get_member(payload.user_id)

        if role and member:
            try:
                await member.remove_roles(role, reason="Reaction role removed")
            except discord.Forbidden:
                pass

    async def cog_app_command_error(self, interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("⛔ You need Administrator permission.", ephemeral=True)
        else:
            log.error(f"Reaction role error: {error}")


async def setup(bot: commands.Bot):
    await bot.add_cog(ReactionRolesCog(bot))
