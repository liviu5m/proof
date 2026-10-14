"use client"

import * as React from "react"
import { useRouter } from "next/navigation"

export default function HomePage() {
  const router = useRouter()
  
  React.useEffect(() => {
    router.push("/auth/login")
  }, [router])

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-pulse text-muted-foreground">Redirecting...</div>
    </div>
  )
}