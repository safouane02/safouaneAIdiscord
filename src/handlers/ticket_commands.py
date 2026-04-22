# safouane02.github

import os
import io
import asyncio
import discord
from datetime import datetime
from discord.ext import commands

from src.services.ticket_store import (
    create_ticket, get_ticket, update_ticket,
    close_ticket, next_ticket_id, get_stats, set_rating,
)
from src.services.ticket_config import (
    get_panel_message, get_ticket_message,
    set_panel_message, set_ticket_message,
    reset_panel_message, reset_ticket_message,
)
from src.services.ticket_ai import handle_ticket_message
from src.services.logger import get_logger

log = get_logger("tickets")



class TicketCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _support_role_name(self) -> str:
        return os.getenv("SUPPORT_ROLE", "Support")

    def _support_role(self, guild: discord.Guild) -> discord.Role | None:
        return discord.utils.get(guild.roles, name=self._support_role_name())

    def _ticket_category(self, guild: discord.Guild) -> discord.CategoryChannel | None:
        return discord.utils.get(guild.categories, name=os.getenv("TICKET_CATEGORY", "Tickets"))

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def ticketsetup(self, ctx):
        guild = ctx.guild
        msg = await ctx.send("⚙️ Setting up ticket system...")

        support_role = self._support_role(guild)
        if not support_role:
            support_role = await guild.create_role(
                name=self._support_role_name(),
                color=discord.Color.blurple(),
                mentionable=True,
            )

        category = self._ticket_category(guild)
        if not category:
            category = await guild.create_category(
                name=os.getenv("TICKET_CATEGORY", "Tickets"),
                overwrites={
                    guild.default_role: discord.PermissionOverwrite(view_channel=False),
                    guild.me: discord.PermissionOverwrite(view_channel=True, manage_channels=True),
                    support_role: discord.PermissionOverwrite(view_channel=True),
                },
            )

        existing = discord.utils.get(guild.text_channels, name="open-ticket")
        if existing:
            await existing.delete()

        ticket_channel = await guild.create_text_channel(
            name="open-ticket",
            category=category,
            overwrites={
                guild.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=False),
                guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            },
        )

        await self._send_panel(ticket_channel, guild)

        await msg.edit(content=(
            f"✅ Ticket system ready!\n"
            f"• Role: **{support_role.name}**\n"
            f"• Category: **{category.name}**\n"
            f"• Channel: {ticket_channel.mention}\n\n"
            f"💡 `!ticketpanel` — edit the panel message\n"
            f"💡 `!ticketmessage` — edit the ticket welcome message"
        ))
        log.info(f"Ticket system set up in {guild.name} by {ctx.author}")

    async def _send_panel(self, channel: discord.TextChannel, guild: discord.Guild):
        config = get_panel_message(guild.id)
        support_role_name = self._support_role_name()
        description = config["description"].replace("{support_role}", support_role_name)

        embed = discord.Embed(
            title=config["title"],
            description=description,
            color=config.get("color", 0x5865F2),
        )
        if config.get("footer"):
            embed.set_footer(text=config["footer"])

        await channel.send(embed=embed, view=OpenTicketView())

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def ticketpanel(self, ctx, *, args: str = None):
        """
        !ticketpanel                                          → show current
        !ticketpanel reset                                    → reset to default
        !ticketpanel title: ... | description: ... | footer: ...
        """
        guild_id = ctx.guild.id

        if not args:
            config = get_panel_message(guild_id)
            embed = discord.Embed(title="📋 Current Panel Message", color=config.get("color", 0x5865F2))
            embed.add_field(name="Title", value=config["title"], inline=False)
            embed.add_field(name="Description", value=config["description"], inline=False)
            embed.add_field(name="Footer", value=config.get("footer", "none"), inline=False)
            embed.set_footer(text="Use !ticketpanel title: ... | description: ... | footer: ...")
            await ctx.reply(embed=embed, mention_author=False)
            return

        if args.strip().lower() == "reset":
            reset_panel_message(guild_id)
            await ctx.reply("✅ Panel message reset to default.", mention_author=False)
            return

        updates = _parse_fields(args, ["title", "description", "footer"])
        if not updates:
            await ctx.reply(
                "⚠️ Usage: `!ticketpanel title: ... | description: ... | footer: ...`\n"
                "Use `{support_role}` as placeholder for the support role name.",
                mention_author=False,
            )
            return

        set_panel_message(guild_id, **updates)
        embed = discord.Embed(title="✅ Panel Message Updated", color=0x57F287)
        for k, v in updates.items():
            embed.add_field(name=k.capitalize(), value=v, inline=False)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def ticketmessage(self, ctx, *, args: str = None):
        """
        !ticketmessage                              → show current
        !ticketmessage reset                        → reset to default
        !ticketmessage title: ... | description: ...
        """
        guild_id = ctx.guild.id

        if not args:
            config = get_ticket_message(guild_id)
            embed = discord.Embed(title="📝 Current Ticket Message", color=config.get("color", 0x5865F2))
            embed.add_field(name="Title", value=config["title"], inline=False)
            embed.add_field(name="Description", value=config["description"], inline=False)
            embed.set_footer(text="Use {user} as placeholder for the member mention")
            await ctx.reply(embed=embed, mention_author=False)
            return

        if args.strip().lower() == "reset":
            reset_ticket_message(guild_id)
            await ctx.reply("✅ Ticket message reset to default.", mention_author=False)
            return

        updates = _parse_fields(args, ["title", "description"])
        if not updates:
            await ctx.reply(
                "⚠️ Usage: `!ticketmessage title: ... | description: ...`\n"
                "Use `{user}` as placeholder for the member mention.",
                mention_author=False,
            )
            return

        set_ticket_message(guild_id, **updates)
        embed = discord.Embed(title="✅ Ticket Message Updated", color=0x57F287)
        for k, v in updates.items():
            embed.add_field(name=k.capitalize(), value=v, inline=False)
        await ctx.reply(embed=embed, mention_author=False)

    async def open_ticket(self, guild: discord.Guild, user: discord.Member) -> discord.TextChannel | None:
        for channel in guild.text_channels:
            t = get_ticket(guild.id, channel.id)
            if t and t["user_id"] == user.id and t["status"] == "open":
                return None

        ticket_id = next_ticket_id(guild.id)
        category = self._ticket_category(guild)
        support_role = self._support_role(guild)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
        }
        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        channel = await guild.create_text_channel(
            name=f"ticket-{ticket_id:04d}",
            category=category,
            overwrites=overwrites,
            topic=f"Support ticket for {user} | ID #{ticket_id}",
        )

        create_ticket(guild.id, ticket_id, user.id, channel.id)

        config = get_ticket_message(guild.id)
        description = config["description"].replace("{user}", user.mention)

        embed = discord.Embed(
            title=config["title"],
            description=description,
            color=config.get("color", 0x5865F2),
        )
        embed.set_footer(text="github.com/safouane02")

        bot_msg = await channel.send(embed=embed, view=TicketActionsView())
        update_ticket(guild.id, channel.id, last_bot_msg_id=bot_msg.id)

        log.info(f"Ticket #{ticket_id} opened by {user} ({user.id})")
        return channel

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def ticket(self, ctx):
        channel = await self.open_ticket(ctx.guild, ctx.author)
        if channel is None:
            for ch in ctx.guild.text_channels:
                t = get_ticket(ctx.guild.id, ch.id)
                if t and t["user_id"] == ctx.author.id and t["status"] == "open":
                    await ctx.reply(f"⚠️ You already have an open ticket: {ch.mention}", mention_author=False)
                    return
        else:
            await ctx.reply(f"✅ Ticket opened: {channel.mention}", mention_author=False)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def close(self, ctx):
        await self._close_ticket(ctx.channel, ctx.author, ctx.guild)

    async def _close_ticket(self, channel: discord.TextChannel, closer: discord.Member, guild: discord.Guild):
        ticket = get_ticket(guild.id, channel.id)
        if not ticket or ticket["status"] == "closed":
            return

        is_owner = closer.id == ticket["user_id"]
        support_role = self._support_role(guild)
        is_staff = support_role and support_role in closer.roles

        if not (is_owner or is_staff or closer.guild_permissions.manage_channels):
            await channel.send("⛔ Only the ticket owner or staff can close this.")
            return

        transcript_text = await _build_transcript(channel)
        close_ticket(guild.id, channel.id, transcript_text)

        user = guild.get_member(ticket["user_id"])
        if user:
            try:
                file = discord.File(
                    io.StringIO(transcript_text),
                    filename=f"ticket-{ticket['id']:04d}-transcript.txt",
                )
                await user.send(
                    f"📄 Your ticket **#{ticket['id']:04d}** has been closed. Here's your transcript:",
                    file=file,
                )
                await user.send(
                    "⭐ How would you rate your support experience?",
                    view=RatingView(guild.id, channel.id),
                )
            except discord.Forbidden:
                pass

        embed = discord.Embed(
            title="🔒 Ticket Closed",
            description=f"Closed by {closer.mention}\nDeleting in 5 seconds...",
            color=0xED4245,
        )
        await channel.send(embed=embed)
        await asyncio.sleep(5)

        try:
            await channel.delete()
        except discord.NotFound:
            pass

        log.info(f"Ticket #{ticket['id']} closed by {closer}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def transcript(self, ctx):
        ticket = get_ticket(ctx.guild.id, ctx.channel.id)
        if not ticket:
            await ctx.reply("⚠️ This is not a ticket channel.", mention_author=False)
            return

        text = await _build_transcript(ctx.channel)
        file = discord.File(
            io.StringIO(text),
            filename=f"ticket-{ticket['id']:04d}-transcript.txt",
        )
        await ctx.send(f"📄 Transcript for ticket **#{ticket['id']:04d}**:", file=file)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def claim(self, ctx):
        ticket = get_ticket(ctx.guild.id, ctx.channel.id)
        if not ticket:
            await ctx.reply("⚠️ This is not a ticket channel.", mention_author=False)
            return

        support_role = self._support_role(ctx.guild)
        is_staff = support_role and support_role in ctx.author.roles

        if not (is_staff or ctx.author.guild_permissions.manage_channels):
            await ctx.reply("⛔ Only staff can claim tickets.", mention_author=False)
            return

        update_ticket(ctx.guild.id, ctx.channel.id, claimed_by=ctx.author.id)
        await ctx.send(f"✅ Ticket claimed by {ctx.author.mention}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def tadd(self, ctx, member: discord.Member):
        ticket = get_ticket(ctx.guild.id, ctx.channel.id)
        if not ticket:
            await ctx.reply("⚠️ This is not a ticket channel.", mention_author=False)
            return
        await ctx.channel.set_permissions(member, view_channel=True, send_messages=True)
        await ctx.send(f"✅ Added {member.mention} to the ticket.")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def ticketstats(self, ctx):
        stats = get_stats(ctx.guild.id)
        open_count = sum(
            1 for ch in ctx.guild.text_channels
            if (t := get_ticket(ctx.guild.id, ch.id)) and t["status"] == "open"
        )
        embed = discord.Embed(title="🎫 Ticket Statistics", color=0x5865F2)
        embed.add_field(name="Total", value=stats.get("total", 0), inline=True)
        embed.add_field(name="Closed", value=stats.get("closed", 0), inline=True)
        embed.add_field(name="Open Now", value=open_count, inline=True)
        await ctx.send(embed=embed)

    async def call_staff(self, interaction: discord.Interaction):
        ticket = get_ticket(interaction.guild.id, interaction.channel.id)
        if not ticket:
            await interaction.response.send_message("⚠️ This is not a ticket channel.", ephemeral=True)
            return

        if interaction.user.id != ticket["user_id"]:
            await interaction.response.send_message("⛔ Only the ticket owner can call staff.", ephemeral=True)
            return

        support_role = self._support_role(interaction.guild)
        mention = support_role.mention if support_role else f"@{self._support_role_name()}"

        embed = discord.Embed(
            title="📣 Staff Called",
            description=f"{interaction.user.mention} is requesting staff assistance.\n{mention} please help!",
            color=0xFFA500,
        )
        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        if message.content.startswith("!"):
            return

        ticket = get_ticket(message.guild.id, message.channel.id)
        if not ticket or ticket["status"] != "open":
            return

        if message.author.id != ticket["user_id"]:
            return

        last_bot_id = ticket.get("last_bot_msg_id")
        is_reply_to_bot = (
            message.reference is not None
            and message.reference.message_id == last_bot_id
        )

        if not is_reply_to_bot:
            return

        async with message.channel.typing():
            try:
                history = []
                async for msg in message.channel.history(limit=30, oldest_first=True):
                    if msg.author.id == message.author.id and msg.content and not msg.content.startswith("!"):
                        history.append({"role": "user", "content": msg.content})
                    elif msg.author.id == self.bot.user.id and msg.content:
                        history.append({"role": "assistant", "content": msg.content})

                response, should_escalate = await handle_ticket_message(history)

                if should_escalate:
                    support_role = self._support_role(message.guild)
                    mention = support_role.mention if support_role else f"@{self._support_role_name()}"
                    embed = discord.Embed(
                        title="👋 Staff Needed",
                        description=f"The AI couldn't resolve this.\n**Reason:** {response}\n\n{mention} please assist!",
                        color=0xFFA500,
                    )
                    bot_msg = await message.channel.send(embed=embed)
                else:
                    bot_msg = await message.reply(response, mention_author=False)

                update_ticket(message.guild.id, message.channel.id, last_bot_msg_id=bot_msg.id)

            except Exception as e:
                log.error(f"Ticket AI error: {e}")
                await message.channel.send("⚠️ Something went wrong. Please try again.")

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply("⛔ You don't have permission.", mention_author=False)
        elif isinstance(error, commands.MemberNotFound):
            await ctx.reply("⚠️ Member not found.", mention_author=False)
        else:
            log.error(f"Ticket error in {ctx.command}: {error}")



class OpenTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Open Ticket", style=discord.ButtonStyle.primary, emoji="🎫", custom_id="open_ticket_btn")
    async def open_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog: TicketCog = interaction.client.cogs.get("TicketCog")
        if not cog:
            return
        await interaction.response.defer(ephemeral=True)
        channel = await cog.open_ticket(interaction.guild, interaction.user)
        if channel is None:
            await interaction.followup.send("⚠️ You already have an open ticket.", ephemeral=True)
        else:
            await interaction.followup.send(f"✅ Ticket opened: {channel.mention}", ephemeral=True)


class TicketActionsView(discord.ui.View):
    """Buttons shown inside the ticket channel."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Call Staff", style=discord.ButtonStyle.primary, emoji="📣", custom_id="call_staff_btn")
    async def call_staff_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog: TicketCog = interaction.client.cogs.get("TicketCog")
        if cog:
            await cog.call_staff(interaction)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red, emoji="🔒", custom_id="close_ticket_btn")
    async def close_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog: TicketCog = interaction.client.cogs.get("TicketCog")
        if not cog:
            return
        await interaction.response.defer()
        await cog._close_ticket(interaction.channel, interaction.user, interaction.guild)


class RatingView(discord.ui.View):
    def __init__(self, guild_id: int, channel_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        self.channel_id = channel_id

    async def _rate(self, interaction: discord.Interaction, rating: int):
        set_rating(self.guild_id, self.channel_id, rating)
        await interaction.response.edit_message(
            content=f"Thanks for your rating: {'⭐' * rating} ({rating}/5)",
            view=None,
        )

    @discord.ui.button(label="1⭐", style=discord.ButtonStyle.grey)
    async def r1(self, i, b): await self._rate(i, 1)

    @discord.ui.button(label="2⭐", style=discord.ButtonStyle.grey)
    async def r2(self, i, b): await self._rate(i, 2)

    @discord.ui.button(label="3⭐", style=discord.ButtonStyle.grey)
    async def r3(self, i, b): await self._rate(i, 3)

    @discord.ui.button(label="4⭐", style=discord.ButtonStyle.primary)
    async def r4(self, i, b): await self._rate(i, 4)

    @discord.ui.button(label="5⭐", style=discord.ButtonStyle.success)
    async def r5(self, i, b): await self._rate(i, 5)


def _parse_fields(args: str, allowed: list[str]) -> dict:
    result = {}
    for part in args.split("|"):
        part = part.strip()
        for field in allowed:
            if part.lower().startswith(f"{field}:"):
                result[field] = part[len(field) + 1:].strip()
    return result


async def _build_transcript(channel: discord.TextChannel) -> str:
    lines = [
        "=== Ticket Transcript ===",
        f"Channel : #{channel.name}",
        f"Server  : {channel.guild.name}",
        f"Date    : {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
        "=" * 40,
        "",
    ]
    async for msg in channel.history(limit=500, oldest_first=True):
        if msg.content:
            ts = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
            lines.append(f"[{ts}] {msg.author.display_name}: {msg.content}")
    return "\n".join(lines)


async def setup(bot: commands.Bot):
    await bot.add_cog(TicketCog(bot))
