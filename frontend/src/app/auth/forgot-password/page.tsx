"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Mail } from "lucide-react";
import { useMutation } from "@tanstack/react-query";
import { forgotPassword } from "@/api/user";
import { toast } from "sonner";

export default function ForgotPasswordPage() {
  const router = useRouter();
  const [email, setEmail] = React.useState("");

  const { mutate: sendReset, isPending } = useMutation({
    mutationKey: ["forgotPassword"],
    mutationFn: () => forgotPassword({ email }),
    onSuccess: () => {
      toast.success("If the email exists, a reset link has been sent");
      router.push("/auth/login");
    },
    onError: () => {
      toast.error("Failed to send reset email");
    },
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    sendReset();
  };

  return (
    <div className="w-full max-w-md mx-auto px-4 sm:px-6 py-8 sm:py-24 space-y-8 animate-in fade-in-50 duration-500">
      <div className="text-center space-y-3">
        <Link
          href="/"
          className="inline-flex items-center gap-2.5 mb-2 group cursor-pointer"
        >
          <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-lime-400 to-lime-600 flex items-center justify-center shadow-lg shadow-lime-500/25 group-hover:scale-105 transition-transform duration-200">
            <svg
              className="w-6 h-6 text-slate-950 font-bold"
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                fill="none"
              />
            </svg>
          </div>
          <span className="text-2xl font-bold tracking-tight text-white">
            Proof
          </span>
        </Link>
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
          Forgot password
        </h1>
        <p className="text-sm sm:text-base text-slate-400">
          Enter your email to reset your password
        </p>
      </div>

      <Card className="bg-[#0a0a0f] border border-slate-800 shadow-lg rounded-2xl">
        <CardContent className="p-6 sm:p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <Label htmlFor="email" className="text-slate-300 text-xs sm:text-sm font-medium">
                Email
              </Label>
              <div className="relative mt-1">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="pl-10 h-11 bg-slate-950/60 border-slate-800 text-white placeholder-slate-500 text-sm sm:text-base focus-visible:border-lime-500 focus-visible:ring-lime-500/20 transition-all"
                  required
                  disabled={isPending}
                />
              </div>
            </div>

            <Button
              type="submit"
              className="w-full h-11 bg-lime-500 hover:bg-lime-400 text-slate-950 font-semibold text-base transition-all duration-200 shadow-lg shadow-lime-500/20 hover:shadow-lime-500/30 active:scale-[0.99] cursor-pointer"
              disabled={isPending}
            >
              {isPending ? "Sending..." : "Send reset email"}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex flex-col gap-4 border-t border-slate-800/80 px-6 py-5 bg-[#0a0a0f]/50">
          <p className="text-center text-xs sm:text-sm text-slate-400">
            Remember your password?{" "}
            <Link
              href="/auth/login"
              className="text-lime-400 hover:text-lime-300 font-semibold transition-colors cursor-pointer"
            >
              Sign in
            </Link>
          </p>
        </CardFooter>
      </Card>
    </div>
  );
}