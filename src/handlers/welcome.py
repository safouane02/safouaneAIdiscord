import io
import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont

from src.services.welcome_config import get_config, update_config
from src.services.logger import get_logger

log = get_logger("welcome")


class WelcomeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── /setwelcome ────────────────────────────────────────
    @app_commands.command(name="setwelcome", description="Configure the welcome message")
    @app_commands.describe(
        channel="Channel to send welcome messages",
        message="Welcome message — use {user} {server} {count}",
        enabled="Enable or disable welcome messages",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setwelcome(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel = None,
        message: str = None,
        enabled: bool = None,
    ):
        updates = {}
        if channel:
            updates["channel_id"] = channel.id
        if message:
            updates["message"] = message
        if enabled is not None:
            updates["enabled"] = enabled

        update_config(interaction.guild.id, **updates)

        config = get_config(interaction.guild.id)
        ch = interaction.guild.get_channel(config["channel_id"]) if config["channel_id"] else "Not set"

        embed = discord.Embed(title="👋 Welcome Settings", color=0x57F287)
        embed.add_field(name="Status", value="✅ Enabled" if config["enabled"] else "❌ Disabled", inline=True)
        embed.add_field(name="Channel", value=str(ch), inline=True)
        embed.add_field(name="Message", value=config["message"], inline=False)
        embed.set_footer(text="Placeholders: {user} {server} {count}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── /testwelcome ───────────────────────────────────────
    @app_commands.command(name="testwelcome", description="Preview the welcome message")
    @app_commands.checks.has_permissions(administrator=True)
    async def testwelcome(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        file, embed = await _build_welcome(interaction.user, interaction.guild)
        await interaction.followup.send(embed=embed, file=file if file else discord.utils.MISSING, ephemeral=True)

    # ── member join event ──────────────────────────────────
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        config = get_config(member.guild.id)
        if not config["enabled"] or not config["channel_id"]:
            return

        channel = member.guild.get_channel(config["channel_id"])
        if not channel:
            return

        try:
            file, embed = await _build_welcome(member, member.guild)
            await channel.send(embed=embed, file=file if file else discord.utils.MISSING)
        except Exception as e:
            log.error(f"Welcome error for {member}: {e}")

    async def cog_app_command_error(self, interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("⛔ You need Administrator permission.", ephemeral=True)


async def _build_welcome(member: discord.Member, guild: discord.Guild) -> tuple:
    config = get_config(guild.id)

    text = (
        config["message"]
        .replace("{user}", member.mention)
        .replace("{server}", guild.name)
        .replace("{count}", str(guild.member_count))
    )

    embed = discord.Embed(description=text, color=0x5865F2)
    embed.set_author(name=str(member), icon_url=member.display_avatar.url)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=f"{guild.name} • {guild.member_count} members")

    # generate welcome card image
    file = None
    try:
        file = await _generate_card(member)
        embed.set_image(url="attachment://welcome.png")
    except Exception as e:
        log.warning(f"Could not generate welcome card: {e}")

    return file, embed


async def _generate_card(member: discord.Member) -> discord.File:
    width, height = 800, 250
    bg_color = (43, 45, 49)
    text_color = (255, 255, 255)
    accent_color = (88, 101, 242)

    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # background gradient strip
    for x in range(width):
        ratio = x / width
        r = int(43 + (88 - 43) * ratio * 0.3)
        g = int(45 + (101 - 45) * ratio * 0.3)
        b = int(49 + (242 - 49) * ratio * 0.3)
        draw.line([(x, 0), (x, height)], fill=(r, g, b))

    # fetch and paste avatar
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(str(member.display_avatar.url)) as resp:
                avatar_bytes = await resp.read()

        avatar_img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize((120, 120))
        mask = Image.new("L", (120, 120), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 120, 120), fill=255)
        avatar_img.putalpha(mask)
        img.paste(avatar_img, (65, 65), avatar_img)
    except Exception:
        pass

    # accent circle border
    draw.ellipse((60, 60, 190, 190), outline=accent_color, width=4)

    # text
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except Exception:
        font_large = ImageFont.load_default()
        font_small = font_large

    draw.text((220, 80), f"Welcome!", font=font_large, fill=accent_color)
    draw.text((220, 120), str(member.display_name), font=font_large, fill=text_color)
    draw.text((220, 165), f"Member #{member.guild.member_count}", font=font_small, fill=(180, 180, 180))

    buf = io.BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)
    return discord.File(buf, filename="welcome.png")


async def setup(bot: commands.Bot):
    await bot.add_cog(WelcomeCog(bot))
