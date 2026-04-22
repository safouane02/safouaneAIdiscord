// safouane02.github

"use client"

import { useEffect } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { loginWithDiscord } from "@/lib/bot-api"

export default function AuthCallback() {
  const router = useRouter()
  const searchParams = useSearchParams()

  useEffect(() => {
    const code = searchParams.get("code")
    if (!code) {
      router.push("/")
      return
    }

    const redirectUri = `${window.location.origin}/auth/callback`

    loginWithDiscord(code, redirectUri)
      .then(({ token, user }) => {
        localStorage.setItem("bot_token", token)
        localStorage.setItem("bot_user", JSON.stringify(user))
        router.push("/dashboard")
      })
      .catch(() => router.push("/?error=login_failed"))
  }, [])

  return (
    <div className="flex items-center justify-center min-h-screen">
      <p className="text-gray-400">Logging you in...</p>
    </div>
  )
}
