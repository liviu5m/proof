"use client"

import * as React from "react"
import { useRouter } from "next/navigation"

export default function HomePage() {
  const router = useRouter()
  
  React.useEffect(() => {
    router.push("/auth/login")
  }, [router])

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-950 text-white space-y-4">
      <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-lime-400 to-lime-600 flex items-center justify-center shadow-lg shadow-lime-500/30 animate-bounce">
        <svg className="w-7 h-7 text-slate-950 font-bold" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
        </svg>
      </div>
      <div className="animate-pulse text-sm font-medium text-slate-400">Loading Proof...</div>
    </div>
  )
}