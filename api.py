"""
SF Bot API — للوحة التحكم Next.js
─────────────────────────────────
Auth:
  POST /auth/discord          → exchange Discord code → JWT token
  GET  /auth/me               → get current user info

Dashboard:
  GET  /dashboard/guilds      → سيرفرات المستخدم التي فيها البوت
  GET  /dashboard/guild/{id}  → معلومات سيرفر كاملة
  POST /dashboard/guild/{id}/settings  → تعديل إعدادات السيرفر

Premium (يحتاج API_SECRET):
  GET  /guild/{id}/premium    → خطة السيرفر
  POST /guild/{id}/premium    → تفعيل خطة

Public:
  GET  /stats                 → إحصائيات البوت
  GET  /plans                 → قائمة الخطط
"""

import os
import jwt
import time
import aiohttp
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.services.premium import get_premium_info, set_tier, PLANS, get_token_usage
from src.services.level_service import get_leaderboard, get_user
from src.services.ticket_store import get_stats as get_ticket_stats
from src.services.log_service import get_log_channel

app = FastAPI(title="SF Bot API", version="1.0.0")

WEBSITE_URL = os.getenv("WEBSITE_URL", "http://localhost:3000")
API_SECRET = os.getenv("API_SECRET", "changeme")
JWT_SECRET = os.getenv("JWT_SECRET", "jwt_secret_changeme")
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "")

_bot_ref = None


def set_bot(bot):
    global _bot_ref
    _bot_ref = bot


app.add_middleware(
    CORSMiddleware,
    allow_origins=[WEBSITE_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helpers ────────────────────────────────────────────────

def _verify_api_secret(secret: str):
    if secret != API_SECRET:
        raise HTTPException(status_code=401, detail="Invalid API secret")


def _create_jwt(user_id: str, username: str, avatar: str) -> str:
    payload = {
        "user_id": user_id,
        "username": username,
        "avatar": avatar,
        "exp": int(time.time()) + 86400 * 7,  # 7 days
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def _verify_jwt(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def _get_user_from_header(authorization: str = None) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    return _verify_jwt(authorization.replace("Bearer ", ""))


async def _fetch_discord(endpoint: str, token: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://discord.com/api/v10{endpoint}",
            headers={"Authorization": f"Bearer {token}"},
        ) as resp:
            if resp.status != 200:
                raise HTTPException(status_code=resp.status, detail="Discord API error")
            return await resp.json()


# ══════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════

class DiscordCodeBody(BaseModel):
    code: str
    redirect_uri: str


@app.post("/auth/discord")
async def discord_oauth(body: DiscordCodeBody):
    """
    Exchange Discord OAuth2 code for JWT.
    Frontend sends the code after user logs in with Discord.
    """
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://discord.com/api/v10/oauth2/token",
            data={
                "client_id": DISCORD_CLIENT_ID,
                "client_secret": DISCORD_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": body.code,
                "redirect_uri": body.redirect_uri,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        ) as resp:
            if resp.status != 200:
                raise HTTPException(status_code=400, detail="Invalid Discord code")
            token_data = await resp.json()

    discord_token = token_data["access_token"]
    user = await _fetch_discord("/users/@me", discord_token)

    avatar_url = None
    if user.get("avatar"):
        avatar_url = f"https://cdn.discordapp.com/avatars/{user['id']}/{user['avatar']}.png"

    jwt_token = _create_jwt(user["id"], user["username"], avatar_url or "")

    return {
        "token": jwt_token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "avatar": avatar_url,
        },
    }


@app.get("/auth/me")
async def get_me(authorization: str = Header(None)):
    user = _get_user_from_header(authorization)
    return {
        "id": user["user_id"],
        "username": user["username"],
        "avatar": user["avatar"],
    }


# ══════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════

@app.get("/dashboard/guilds")
async def get_user_guilds(authorization: str = Header(None)):
    """Returns guilds where the user is admin AND the bot is present."""
    user = _get_user_from_header(authorization)

    if not _bot_ref:
        raise HTTPException(status_code=503, detail="Bot offline")

    bot_guild_ids = {g.id for g in _bot_ref.guilds}
    result = []

    for guild in _bot_ref.guilds:
        member = guild.get_member(int(user["user_id"]))
        if not member:
            continue
        if not member.guild_permissions.administrator:
            continue

        premium_info = await get_premium_info(guild.id)

        result.append({
            "id": str(guild.id),
            "name": guild.name,
            "icon": str(guild.icon.url) if guild.icon else None,
            "member_count": guild.member_count,
            "plan": premium_info["plan"]["name"],
            "plan_emoji": premium_info["plan"]["emoji"],
        })

    return {"guilds": result}


@app.get("/dashboard/guild/{guild_id}")
async def get_guild_dashboard(guild_id: int, authorization: str = Header(None)):
    """Full guild dashboard data."""
    user = _get_user_from_header(authorization)

    if not _bot_ref:
        raise HTTPException(status_code=503, detail="Bot offline")

    guild = _bot_ref.get_guild(guild_id)
    if not guild:
        raise HTTPException(status_code=404, detail="Guild not found or bot not in guild")

    member = guild.get_member(int(user["user_id"]))
    if not member or not member.guild_permissions.administrator:
        raise HTTPException(status_code=403, detail="Not an admin in this guild")

    premium_info = await get_premium_info(guild_id)
    ticket_stats = get_ticket_stats(guild_id)
    leaderboard = await get_leaderboard(guild_id, limit=5)
    log_channel_id = await get_log_channel(guild_id)
    log_channel = guild.get_channel(log_channel_id) if log_channel_id else None

    lb_data = []
    for i, row in enumerate(leaderboard, 1):
        m = guild.get_member(row["user_id"])
        lb_data.append({
            "rank": i,
            "user_id": str(row["user_id"]),
            "name": m.display_name if m else "Unknown",
            "avatar": str(m.display_avatar.url) if m else None,
            "level": row["level"],
            "xp": row["xp"],
        })

    return {
        "guild": {
            "id": str(guild.id),
            "name": guild.name,
            "icon": str(guild.icon.url) if guild.icon else None,
            "member_count": guild.member_count,
            "channels": len(guild.text_channels),
            "roles": len(guild.roles),
        },
        "premium": {
            "tier": premium_info["tier"],
            "plan": premium_info["plan"]["name"],
            "emoji": premium_info["plan"]["emoji"],
            "expires_at": premium_info["expires_at"],
            "tokens_used_today": premium_info["tokens_used_today"],
            "daily_limit": premium_info["plan"]["daily_tokens"],
        },
        "tickets": ticket_stats,
        "leaderboard": lb_data,
        "settings": {
            "log_channel": str(log_channel_id) if log_channel_id else None,
            "log_channel_name": f"#{log_channel.name}" if log_channel else None,
        },
    }


@app.post("/dashboard/guild/{guild_id}/settings")
async def update_guild_settings(guild_id: int, request: Request, authorization: str = Header(None)):
    """Update guild settings from dashboard."""
    user = _get_user_from_header(authorization)

    if not _bot_ref:
        raise HTTPException(status_code=503, detail="Bot offline")

    guild = _bot_ref.get_guild(guild_id)
    if not guild:
        raise HTTPException(status_code=404, detail="Guild not found")

    member = guild.get_member(int(user["user_id"]))
    if not member or not member.guild_permissions.administrator:
        raise HTTPException(status_code=403, detail="Not an admin")

    body = await request.json()
    updated = []

    if "log_channel_id" in body:
        from src.services.log_service import set_log_channel
        await set_log_channel(guild_id, int(body["log_channel_id"]))
        updated.append("log_channel")

    if "xp_per_msg" in body:
        from src.services.level_service import update_settings
        await update_settings(guild_id, xp_per_msg=int(body["xp_per_msg"]))
        updated.append("xp_per_msg")

    if "xp_cooldown" in body:
        from src.services.level_service import update_settings
        await update_settings(guild_id, xp_cooldown=int(body["xp_cooldown"]))
        updated.append("xp_cooldown")

    return {"success": True, "updated": updated}


# ══════════════════════════════════════════════════════════
# PREMIUM (API Secret protected)
# ══════════════════════════════════════════════════════════

class SetPremiumBody(BaseModel):
    tier: str
    days: int = 30


@app.get("/guild/{guild_id}/premium")
async def get_guild_premium(guild_id: int, x_api_secret: str = Header(None)):
    _verify_api_secret(x_api_secret)
    return await get_premium_info(guild_id)


@app.post("/guild/{guild_id}/premium")
async def set_guild_premium(guild_id: int, body: SetPremiumBody, x_api_secret: str = Header(None)):
    _verify_api_secret(x_api_secret)

    if body.tier not in PLANS:
        raise HTTPException(status_code=400, detail=f"Invalid tier: {list(PLANS.keys())}")

    days = body.days if body.days > 0 else None
    await set_tier(guild_id, body.tier, days)

    return {"success": True, "guild_id": guild_id, "tier": body.tier, "days": body.days}


# ══════════════════════════════════════════════════════════
# PUBLIC
# ══════════════════════════════════════════════════════════

@app.get("/stats")
async def get_bot_stats():
    if not _bot_ref:
        return {"guilds": 0, "users": 0, "status": "offline"}
    return {
        "guilds": len(_bot_ref.guilds),
        "users": sum(g.member_count for g in _bot_ref.guilds),
        "latency_ms": round(_bot_ref.latency * 1000),
        "status": "online",
    }


@app.get("/plans")
async def get_plans():
    return {
        tier: {
            "name": plan["name"],
            "emoji": plan["emoji"],
            "price": plan["price"],
            "daily_tokens": plan["daily_tokens"],
            "ai_model": plan["ai_model"],
            "xp_boost": plan["xp_boost"],
            "features": {
                "custom_welcome": plan["custom_welcome"],
                "automod": plan["automod"],
                "max_level_roles": plan["max_level_roles"],
                "reaction_roles": plan["reaction_roles"],
            },
        }
        for tier, plan in PLANS.items()
    }