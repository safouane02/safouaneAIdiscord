# safouane02.github

import time
import discord
from discord.ext import commands
from discord import app_commands

from src.services.groq_service import ask_groq
from src.services.history import clear_history, set_personality, get_personality_name
from src.services.rate_limiter import is_rate_limited, remaining_cooldown
from src.services.logger import get_logger
from src.config import PERSONALITIES

log = get_logger("commands")
_start_time = time.time()


class BotCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


    @commands.command()
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000)
        await ctx.reply(f"🏓 Pong! Latency: **{latency}ms**", mention_author=False)

    @commands.command()
    async def clear_chat(self, ctx):
        clear_history(ctx.author.id)
        await ctx.reply("🗑️ Conversation history cleared.", mention_author=False)

    @commands.command()
    async def ask(self, ctx, *, question: str = None):
        if not question:
            await ctx.reply("Usage: `!ask <question>`", mention_author=False)
            return
        if is_rate_limited(ctx.author.id):
            wait = remaining_cooldown(ctx.author.id)
            await ctx.reply(f"⏳ Try again in **{wait}s**.", mention_author=False)
            return
        async with ctx.typing():
            try:
                answer = await ask_groq(question)
                await ctx.reply(answer, mention_author=False)
            except Exception as e:
                log.error(f"!ask error: {e}")
                await ctx.reply("⚠️ Something went wrong.", mention_author=False)

    @commands.command()
    async def mode(self, ctx, name: str = None):
        available = ", ".join(f"`{p}`" for p in PERSONALITIES)
        if not name:
            current = get_personality_name(ctx.author.id)
            await ctx.reply(f"Current: **{current}**\nAvailable: {available}", mention_author=False)
            return
        if not set_personality(ctx.author.id, name.lower()):
            await ctx.reply(f"❌ Choose from: {available}", mention_author=False)
            return
        labels = {
            "default": "😊 Helpful & friendly",
            "sarcastic": "😏 Sarcastic & witty",
            "teacher": "📚 Patient teacher",
            "developer": "💻 Expert developer",
        }
        await ctx.reply(
            f"✅ Personality: **{name}** — {labels.get(name, '')}\n*History cleared.*",
            mention_author=False,
        )

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def info(self, ctx):
        uptime = _format_uptime(time.time() - _start_time)
        embed = discord.Embed(title="ℹ️ Bot Info", color=0x57F287)
        embed.add_field(name="Developer", value="[safouane02](https://github.com/safouane02)", inline=True)
        embed.add_field(name="Prefix", value="`!` (admin) / `/` (everyone)", inline=True)
        embed.add_field(name="Uptime", value=uptime, inline=True)
        embed.add_field(name="Servers", value=str(len(self.bot.guilds)), inline=True)
        embed.set_footer(text="github.com/safouane02")
        await ctx.reply(embed=embed, mention_author=False)


    @app_commands.command(name="help", description="Show all available commands")
    async def slash_help(self, interaction: discord.Interaction):
        is_admin = interaction.user.guild_permissions.administrator
        is_mod = interaction.user.guild_permissions.kick_members

        embed = discord.Embed(
            title="📖 Bot Commands",
            description="Use `/` for all commands • `!` is for admins only",
            color=0x5865F2,
        )

        embed.add_field(
            name="🤖 AI (Everyone)",
            value=(
                "`/ask` — سؤال مباشر\n"
                "`/mode` — تغيير شخصية البوت\n"
                "`/clearchat` — مسح سجل المحادثة\n"
                "💬 رد على رسالة البوت للمحادثة"
            ),
            inline=False,
        )

        embed.add_field(
            name="⭐ Levels (Everyone)",
            value=(
                "`/rank [@user]` — مستواك\n"
                "`/leaderboard` — أعلى 10 أعضاء"
            ),
            inline=False,
        )

        embed.add_field(
            name="ℹ️ Info (Everyone)",
            value="`/userinfo` `/serverinfo` `/rank`",
            inline=False,
        )

        if is_mod or is_admin:
            embed.add_field(
                name="🔨 Moderation (Mods)",
                value=(
                    "`/ban` `/kick` `/timeout` `/warn`\n"
                    "`/mute` `/unmute` `/warnings` `/history`"
                ),
                inline=False,
            )

        if is_admin:
            embed.add_field(
                name="⚙️ Admin Settings",
                value=(
                    "`/automod` — إعدادات الفلتر التلقائي\n"
                    "`/setlogchannel` — قناة السجلات\n"
                    "`/addword` `/removeword` `/bannedwords`\n"
                    "`!ticketsetup` — إعداد التكتات\n"
                    "`!xpsettings` — إعدادات XP\n"
                    "`!add` `/!remove` — DM whitelist"
                ),
                inline=False,
            )

        embed.add_field(
            name="🎫 Tickets",
            value=(
                "اضغط زر **Open Ticket** في قناة `#open-ticket`\n"
                "`/ticketstats` — إحصائيات التكتات"
            ),
            inline=False,
        )

        embed.add_field(
            name="🤖 AI Moderation",
            value="@البوت + منشن العضو بكلام طبيعي\nمثال: `@Bot اطرد @user لأنه يسبام`",
            inline=False,
        )

        embed.set_footer(text="github.com/safouane02")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="ask", description="Ask the AI a question")
    @app_commands.describe(question="Your question")
    async def slash_ask(self, interaction: discord.Interaction, question: str):
        if is_rate_limited(interaction.user.id):
            wait = remaining_cooldown(interaction.user.id)
            await interaction.response.send_message(f"⏳ Try again in **{wait}s**.", ephemeral=True)
            return
        await interaction.response.defer()
        try:
            answer = await ask_groq(question)
            await interaction.followup.send(answer)
        except Exception as e:
            log.error(f"/ask error: {e}")
            await interaction.followup.send("⚠️ Something went wrong.")

    @app_commands.command(name="mode", description="Change the AI personality")
    @app_commands.describe(personality="Choose a personality")
    @app_commands.choices(personality=[
        app_commands.Choice(name="😊 Default — Helpful & friendly", value="default"),
        app_commands.Choice(name="😏 Sarcastic — Witty & sarcastic", value="sarcastic"),
        app_commands.Choice(name="📚 Teacher — Patient & detailed", value="teacher"),
        app_commands.Choice(name="💻 Developer — Technical expert", value="developer"),
    ])
    async def slash_mode(self, interaction: discord.Interaction, personality: str):
        set_personality(interaction.user.id, personality)
        labels = {
            "default": "😊 Helpful & friendly",
            "sarcastic": "😏 Sarcastic & witty",
            "teacher": "📚 Patient teacher",
            "developer": "💻 Expert developer",
        }
        await interaction.response.send_message(
            f"✅ Personality set to **{personality}** — {labels[personality]}",
            ephemeral=True,
        )

    @app_commands.command(name="clearchat", description="Clear your AI conversation history")
    async def slash_clearchat(self, interaction: discord.Interaction):
        clear_history(interaction.user.id)
        await interaction.response.send_message("🗑️ Conversation history cleared.", ephemeral=True)

    @app_commands.command(name="leaderboard", description="Show the XP leaderboard")
    async def slash_leaderboard(self, interaction: discord.Interaction):
        from src.services.level_service import get_leaderboard
        rows = await get_leaderboard(interaction.guild.id, limit=10)
        if not rows:
            await interaction.response.send_message("No data yet. Start chatting!", ephemeral=True)
            return
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        lines = []
        for i, row in enumerate(rows, 1):
            user = interaction.guild.get_member(row["user_id"])
            name = user.display_name if user else f"Unknown"
            medal = medals.get(i, f"`#{i}`")
            lines.append(f"{medal} **{name}** — Level {row['level']} • {row['xp']:,} XP")
        embed = discord.Embed(
            title=f"🏆 {interaction.guild.name} Leaderboard",
            description="\n".join(lines),
            color=0xFFD700,
        )
        embed.set_footer(text="github.com/safouane02")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ticketstats", description="Show ticket statistics")
    async def slash_ticketstats(self, interaction: discord.Interaction):
        from src.services.ticket_store import get_stats, get_ticket
        stats = get_stats(interaction.guild.id)
        open_count = sum(
            1 for ch in interaction.guild.text_channels
            if (t := get_ticket(interaction.guild.id, ch.id)) and t["status"] == "open"
        )
        embed = discord.Embed(title="🎫 Ticket Statistics", color=0x5865F2)
        embed.add_field(name="Total", value=stats.get("total", 0), inline=True)
        embed.add_field(name="Closed", value=stats.get("closed", 0), inline=True)
        embed.add_field(name="Open Now", value=open_count, inline=True)
        await interaction.response.send_message(embed=embed)

    async def cog_app_command_error(self, interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("⛔ You don't have permission.", ephemeral=True)
        else:
            log.error(f"Slash error in commands: {error}")


def _format_uptime(seconds: float) -> str:
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    return f"{h}h {m}m {s}s"


async def setup(bot: commands.Bot):
    await bot.add_cog(BotCommands(bot))
