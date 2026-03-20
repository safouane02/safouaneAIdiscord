/**
 * SF Bot API Client — Next.js Integration
 * ضعه في: lib/bot-api.ts
 */

const API_URL = process.env.NEXT_PUBLIC_BOT_API_URL || "http://localhost:8000"
const API_SECRET = process.env.BOT_API_SECRET || ""

// ── Types ───────────────────────────────────────────────

export interface BotStats {
  guilds: number
  users: number
  latency_ms: number
  status: "online" | "offline"
}

export interface Guild {
  id: string
  name: string
  icon: string | null
  member_count: number
  plan: string
  plan_emoji: string
}

export interface GuildDashboard {
  guild: {
    id: string
    name: string
    icon: string | null
    member_count: number
    channels: number
    roles: number
  }
  premium: {
    tier: string
    plan: string
    emoji: string
    expires_at: string | null
    tokens_used_today: number
    daily_limit: number
  }
  tickets: {
    total: number
    closed: number
  }
  leaderboard: Array<{
    rank: number
    user_id: string
    name: string
    avatar: string | null
    level: number
    xp: number
  }>
  settings: {
    log_channel: string | null
    log_channel_name: string | null
  }
}

export interface Plan {
  name: string
  emoji: string
  price: string
  daily_tokens: number
  ai_model: string
  xp_boost: number
  features: {
    custom_welcome: boolean
    automod: boolean
    max_level_roles: number
    reaction_roles: number
  }
}

// ── Auth ────────────────────────────────────────────────

export async function loginWithDiscord(code: string, redirectUri: string) {
  const res = await fetch(`${API_URL}/auth/discord`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code, redirect_uri: redirectUri }),
  })

  if (!res.ok) throw new Error("Discord login failed")
  return res.json() as Promise<{ token: string; user: { id: string; username: string; avatar: string } }>
}

export async function getMe(token: string) {
  const res = await fetch(`${API_URL}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) throw new Error("Not authenticated")
  return res.json()
}

// ── Dashboard ───────────────────────────────────────────

export async function getUserGuilds(token: string): Promise<{ guilds: Guild[] }> {
  const res = await fetch(`${API_URL}/dashboard/guilds`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) throw new Error("Failed to fetch guilds")
  return res.json()
}

export async function getGuildDashboard(guildId: string, token: string): Promise<GuildDashboard> {
  const res = await fetch(`${API_URL}/dashboard/guild/${guildId}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) throw new Error("Failed to fetch guild dashboard")
  return res.json()
}

export async function updateGuildSettings(
  guildId: string,
  token: string,
  settings: Record<string, unknown>
) {
  const res = await fetch(`${API_URL}/dashboard/guild/${guildId}/settings`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(settings),
  })
  if (!res.ok) throw new Error("Failed to update settings")
  return res.json()
}

// ── Premium ─────────────────────────────────────────────

export async function setGuildPremium(guildId: string, tier: string, days: number) {
  const res = await fetch(`${API_URL}/guild/${guildId}/premium`, {
    method: "POST",
    headers: {
      "x-api-secret": API_SECRET,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ tier, days }),
  })
  if (!res.ok) throw new Error("Failed to set premium")
  return res.json()
}

// ── Public ───────────────────────────────────────────────

export async function getBotStats(): Promise<BotStats> {
  const res = await fetch(`${API_URL}/stats`)
  if (!res.ok) throw new Error("Failed to fetch stats")
  return res.json()
}

export async function getPlans(): Promise<Record<string, Plan>> {
  const res = await fetch(`${API_URL}/plans`)
  if (!res.ok) throw new Error("Failed to fetch plans")
  return res.json()
}

// ── Discord OAuth URL ────────────────────────────────────

export function getDiscordOAuthUrl(redirectUri: string) {
  const params = new URLSearchParams({
    client_id: process.env.NEXT_PUBLIC_DISCORD_CLIENT_ID || "",
    redirect_uri: redirectUri,
    response_type: "code",
    scope: "identify guilds",
  })
  return `https://discord.com/api/oauth2/authorize?${params}`
}
