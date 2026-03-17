import time
import discord
from discord.ext import commands

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
    async def help(self, ctx):
        embed = discord.Embed(
            title="📖 Bot Commands",
            description="Prefix: `!`",
            color=0x5865F2,
        )
        embed.add_field(
            name="🤖 AI",
            value=(
                "`!ask <question>` — سؤال مباشر\n"
                "`!mode <n>` — تغيير شخصية البوت\n"
                "`!clear_chat` — مسح سجل المحادثة\n"
                "💬 رد على رسالة البوت للمحادثة"
            ),
            inline=False,
        )
        embed.add_field(
            name="⭐ Levels",
            value=(
                "`!rank [@user]` — عرض الرانك والـ XP\n"
                "`!leaderboard` — أفضل الأعضاء\n"
                "`!levelroles` — عرض رتب الليفل\n"
                "`!setlevelrole <lvl> @role` — تعيين رتبة للفل\n"
                "`!removelevelrole <lvl>` — حذف رتبة ليفل\n"
                "`!levelsettings` — إعدادات نظام اللفل\n"
                "`!setlevelupchannel #ch` `!setlevelupmsg` `!setxpboost` `!setxp` `!resetxp`"
            ),
            inline=False,
        )
        embed.add_field(
            name="🔨 Moderation",
            value=(
                "`!ban` `!unban` `!kick` `!softban` `!massban`\n"
                "`!timeout <@user> <duration>` `!untimeout`\n"
                "`!mute` `!unmute` `!warn` `!warnings` `!history`"
            ),
            inline=False,
        )
        embed.add_field(
            name="🛠️ Management",
            value=(
                "`!clear <amount>` `!nuke` `!lock` `!unlock`\n"
                "`!nick` `!move` `!disconnect` `!role_add` `!role_remove`"
            ),
            inline=False,
        )
        embed.add_field(
            name="📢 Utility",
            value=(
                "`!dm all/humans/@role <msg>` — رسائل جماعية\n"
                "`!announce <#ch> <msg>` `!say` `!embed_cmd`\n"
                "`!snipe` `!editsnipe` `!steal_emoji` `!invite`"
            ),
            inline=False,
        )
        embed.add_field(
            name="🎫 Tickets",
            value=(
                "`!ticketsetup` — إعداد نظام التكتات\n"
                "`!ticketpanel` `!ticketmessage` — تخصيص الرسائل\n"
                "`!ticket` `!close` `!claim` `!tadd` `!transcript` `!ticketstats`"
            ),
            inline=False,
        )
        embed.add_field(
            name="ℹ️ Info",
            value="`!serverinfo` `!userinfo` `!whois` `!channelinfo`\n`!avatar` `!banner` `!servericon` `!membercount`",
            inline=False,
        )
        embed.add_field(
            name="🔐 Admin",
            value="`!add @user` `!remove @user` `!whitelist` `!info`",
            inline=False,
        )
        embed.add_field(
            name="🤖 AI Moderation",
            value="@البوت + منشن العضو بكلام طبيعي\n`@Bot اطرد @user لأنه يسبام`",
            inline=False,
        )
        embed.set_footer(text="github.com/safouane02")
        await ctx.reply(embed=embed, mention_author=False)

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
            await ctx.reply(f"❌ Unknown personality. Choose: {available}", mention_author=False)
            return

        labels = {
            "default": "😊 Helpful & friendly",
            "sarcastic": "😏 Sarcastic & witty",
            "teacher": "📚 Patient teacher",
            "developer": "💻 Expert developer",
        }
        await ctx.reply(
            f"✅ Personality set to **{name}** — {labels.get(name, '')}\n*History cleared.*",
            mention_author=False,
        )

    @commands.command()
    async def info(self, ctx):
        uptime = _format_uptime(time.time() - _start_time)
        embed = discord.Embed(title="ℹ️ Bot Info", color=0x57F287)
        embed.add_field(name="Developer", value="[safouane02](https://github.com/safouane02)", inline=True)
        embed.add_field(name="Prefix", value="`!`", inline=True)
        embed.add_field(name="Uptime", value=uptime, inline=True)
        embed.add_field(name="Your Personality", value=get_personality_name(ctx.author.id), inline=True)
        embed.set_footer(text="github.com/safouane02")
        await ctx.reply(embed=embed, mention_author=False)


def _format_uptime(seconds: float) -> str:
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    return f"{h}h {m}m {s}s"


async def setup(bot: commands.Bot):
    await bot.add_cog(BotCommands(bot))