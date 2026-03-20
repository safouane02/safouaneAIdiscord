/**
 * Dashboard Page — مثال بسيط
 * ضعه في: app/dashboard/page.tsx
 */

"use client"

import { useEffect, useState } from "react"
import { getUserGuilds, getGuildDashboard, type Guild, type GuildDashboard } from "@/lib/bot-api"

export default function Dashboard() {
  const [guilds, setGuilds] = useState<Guild[]>([])
  const [selected, setSelected] = useState<GuildDashboard | null>(null)
  const [loading, setLoading] = useState(true)

  const token = typeof window !== "undefined" ? localStorage.getItem("bot_token") || "" : ""

  useEffect(() => {
    if (!token) return
    getUserGuilds(token)
      .then((data) => setGuilds(data.guilds))
      .finally(() => setLoading(false))
  }, [token])

  async function openGuild(guildId: string) {
    setLoading(true)
    const data = await getGuildDashboard(guildId, token)
    setSelected(data)
    setLoading(false)
  }

  if (loading) return <p>Loading...</p>

  if (selected) {
    return (
      <div className="p-6">
        <button onClick={() => setSelected(null)} className="mb-4 text-sm text-blue-400">
          ← Back
        </button>
        <h1 className="text-2xl font-bold">{selected.guild.name}</h1>
        <p className="text-gray-400">{selected.guild.member_count.toLocaleString()} members</p>

        {/* Premium Card */}
        <div className="mt-4 p-4 bg-gray-800 rounded-lg">
          <h2 className="font-semibold">
            {selected.premium.emoji} {selected.premium.plan} Plan
          </h2>
          <p className="text-sm text-gray-400 mt-1">
            Tokens today: {selected.premium.tokens_used_today.toLocaleString()} /{" "}
            {selected.premium.daily_limit === 999999
              ? "∞"
              : selected.premium.daily_limit.toLocaleString()}
          </p>
        </div>

        {/* Leaderboard */}
        <div className="mt-4 p-4 bg-gray-800 rounded-lg">
          <h2 className="font-semibold mb-3">🏆 Leaderboard</h2>
          {selected.leaderboard.map((entry) => (
            <div key={entry.user_id} className="flex items-center gap-3 py-2">
              <span className="text-gray-400 w-6">#{entry.rank}</span>
              {entry.avatar && (
                <img src={entry.avatar} className="w-8 h-8 rounded-full" alt="" />
              )}
              <span>{entry.name}</span>
              <span className="ml-auto text-sm text-gray-400">
                Lv.{entry.level} — {entry.xp.toLocaleString()} XP
              </span>
            </div>
          ))}
        </div>

        {/* Tickets */}
        <div className="mt-4 p-4 bg-gray-800 rounded-lg">
          <h2 className="font-semibold">🎫 Tickets</h2>
          <p className="text-sm text-gray-400 mt-1">
            Total: {selected.tickets.total} | Closed: {selected.tickets.closed}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Your Servers</h1>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {guilds.map((guild) => (
          <button
            key={guild.id}
            onClick={() => openGuild(guild.id)}
            className="p-4 bg-gray-800 rounded-lg text-left hover:bg-gray-700 transition"
          >
            <div className="flex items-center gap-3">
              {guild.icon ? (
                <img src={guild.icon} className="w-10 h-10 rounded-full" alt="" />
              ) : (
                <div className="w-10 h-10 rounded-full bg-gray-600 flex items-center justify-center">
                  {guild.name[0]}
                </div>
              )}
              <div>
                <p className="font-medium">{guild.name}</p>
                <p className="text-sm text-gray-400">
                  {guild.plan_emoji} {guild.plan} •{" "}
                  {guild.member_count.toLocaleString()} members
                </p>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
