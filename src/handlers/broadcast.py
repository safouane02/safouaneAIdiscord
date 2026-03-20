import asyncio
import discord
from discord.ext import commands
from src.services.logger import get_logger

log = get_logger("broadcast")


class BroadcastCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def dm(self, ctx, target: str = None, *, message: str = None):
        from src.services.premium import get_plan, WEBSITE_URL

        plan = await get_plan(ctx.guild.id)
        tier = plan.get("name", "Free").lower()

        if tier not in ["basic", "pro", "elite"]:
            msg = "This command requires Basic plan or higher. Upgrade: " + WEBSITE_URL
            await ctx.reply(msg, mention_author=False)
            return

        if not target or not message:
            embed = discord.Embed(title="DM Broadcast", color=0x5865F2)
            embed.add_field(
                name="Usage",
                value=(
                    "`!dm all <message>` - DM everyone\n"
                    "`!dm @role <message>` - DM role members\n"
                    "`!dm humans <message>` - DM all non-bots"
                ),
                inline=False,
            )
            embed.add_field(name="Example", value="`!dm all Server maintenance at 10PM`", inline=False)
            await ctx.reply(embed=embed, mention_author=False)
            return

        guild = ctx.guild
        members = []

        if target.lower() in ("all", "humans"):
            members = [m for m in guild.members if not m.bot and m != ctx.author]

        elif target.startswith("<@&"):
            try:
                role_id = int(target.strip("<@&>"))
                role = guild.get_role(role_id)
                if not role:
                    await ctx.reply("Role not found.", mention_author=False)
                    return
                members = [m for m in role.members if not m.bot]
            except ValueError:
                await ctx.reply("Invalid role mention.", mention_author=False)
                return
        else:
            await ctx.reply("Invalid target. Use `all`, `humans`, or `@role`.", mention_author=False)
            return

        if not members:
            await ctx.reply("No members found.", mention_author=False)
            return

        embed = discord.Embed(
            title="Confirm Broadcast",
            description="Target: **" + str(len(members)) + "** members\nMessage: " + message[:200],
            color=0xFFA500,
        )
        embed.set_footer(text="This cannot be undone")

        view = ConfirmView()
        confirm_msg = await ctx.reply(embed=embed, view=view, mention_author=False)
        await view.wait()

        if not view.confirmed:
            await confirm_msg.edit(
                embed=discord.Embed(description="Broadcast cancelled.", color=0xED4245),
                view=None,
            )
            return

        await confirm_msg.edit(
            embed=discord.Embed(
                description="Sending to **" + str(len(members)) + "** members...",
                color=0x5865F2,
            ),
            view=None,
        )

        dm_embed = discord.Embed(description=message, color=0x5865F2)
        dm_embed.set_author(name=guild.name, icon_url=guild.icon.url if guild.icon else None)
        dm_embed.set_footer(text="Sent by " + str(ctx.author) + " - " + guild.name)

        sent = 0
        failed = 0

        for member in members:
            try:
                await member.send(embed=dm_embed)
                sent += 1
            except (discord.Forbidden, discord.HTTPException):
                failed += 1

            if (sent + failed) % 10 == 0:
                await asyncio.sleep(1)

        result_embed = discord.Embed(title="Broadcast Complete", color=0x57F287)
        result_embed.add_field(name="Sent", value=str(sent), inline=True)
        result_embed.add_field(name="Failed", value=str(failed), inline=True)
        await confirm_msg.edit(embed=result_embed)
        log.info("Broadcast by " + str(ctx.author) + " - " + str(sent) + " sent, " + str(failed) + " failed")

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply("You need Administrator permission.", mention_author=False)
        else:
            log.error("Broadcast error: " + str(error))


class ConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)
        self.confirmed = False

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success, emoji="✅")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = True
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, emoji="❌")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = False
        await interaction.response.defer()
        self.stop()

    async def on_timeout(self):
        self.confirmed = False
        self.stop()


async def setup(bot: commands.Bot):
    await bot.add_cog(BroadcastCog(bot))