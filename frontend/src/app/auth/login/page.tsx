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
import { Separator } from "@/components/ui/separator";
import { cn } from "@/libs/utils";
import { Mail, Lock, Eye, EyeOff, Globe } from "lucide-react";
import { useMutation } from "@tanstack/react-query";
import { loginUser } from "@/api/user";
import { AxiosError } from "axios";
import { toast } from "sonner";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [showPassword, setShowPassword] = React.useState(false);

  const { mutate: login, isPending: isLoading } = useMutation({
    mutationKey: ["loginUser"],
    mutationFn: () =>
      loginUser({
        email,
        password,
      }),
    onSuccess: (data) => {
      console.log(data);
      setEmail("");
      setPassword("");
      setShowPassword(false);
      router.push("/dashboard/datasets");
    },
    onError: (error: AxiosError) => {
      const errorMessage =
        error?.response?.data?.detail ||
        error?.message ||
        "An unexpected error occurred";
      toast.error(errorMessage);
      console.log(error);
    },
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    login();
  };

  const handleGoogleSignIn = () => {
    alert("Google OAuth would redirect here");
  };

  return (
    <div className="w-full max-w-md mx-auto px-4 sm:px-6 py-8 sm:py-16 space-y-8 animate-in fade-in-50 duration-500">
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
          Welcome back
        </h1>
        <p className="text-sm sm:text-base text-slate-400">
          Sign in to your account to continue
        </p>
      </div>

      <Card className="bg-slate-900/80 border-slate-800/80 backdrop-blur-xl shadow-2xl shadow-black/40 rounded-2xl overflow-hidden">
        <CardHeader className="text-center px-6 pt-8 pb-4 space-y-1">
          <CardTitle className="text-xl sm:text-2xl font-semibold text-white tracking-tight">
            Sign in
          </CardTitle>
          <CardDescription className="text-xs sm:text-sm text-slate-400">
            Enter your credentials to access your dashboard
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5 px-6">
          <Button
            variant="outline"
            className="w-full h-11 gap-2.5 bg-slate-800/50 hover:bg-slate-800 border-slate-700/80 text-white font-medium transition-all duration-200 hover:border-slate-600 shadow-sm cursor-pointer"
            onClick={handleGoogleSignIn}
            disabled={isLoading}
          >
            <Globe className="h-4 w-4 text-lime-400" />
            Continue with Google
          </Button>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <Separator className="border-slate-800" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-slate-900 px-3 text-slate-500 font-medium tracking-wider">
                Or continue with email
              </span>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label
                htmlFor="email"
                className="text-slate-300 text-xs sm:text-sm font-medium"
              >
                Email
              </Label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="pl-10 h-11 bg-slate-950/60 border-slate-800 text-white placeholder-slate-500 text-sm sm:text-base focus-visible:border-lime-500 focus-visible:ring-lime-500/20 transition-all"
                  required
                  disabled={isLoading}
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label
                  htmlFor="password"
                  className="text-slate-300 text-xs sm:text-sm font-medium"
                >
                  Password
                </Label>
                <Link
                  href="/auth/forgot-password"
                  className="text-xs sm:text-sm text-lime-400 hover:text-lime-300 transition-colors font-medium cursor-pointer"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pl-10 pr-10 h-11 bg-slate-950/60 border-slate-800 text-white placeholder-slate-500 text-sm sm:text-base focus-visible:border-lime-500 focus-visible:ring-lime-500/20 transition-all"
                  required
                  disabled={isLoading}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-2 top-1/2 -translate-y-1/2 h-9 w-9 text-slate-400 hover:text-white hover:bg-slate-800/50 cursor-pointer"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>

            <Button
              type="submit"
              className="w-full h-11 bg-lime-500 hover:bg-lime-400 text-slate-950 font-semibold text-base transition-all duration-200 shadow-lg shadow-lime-500/20 hover:shadow-lime-500/30 active:scale-[0.99] cursor-pointer"
              disabled={isLoading}
            >
              {isLoading ? "Signing in..." : "Sign in"}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex flex-col gap-4 border-t border-slate-800/80 px-6 py-5 bg-slate-950/20">
          <p className="text-center text-xs sm:text-sm text-slate-400">
            Don&apos;t have an account?{" "}
            <Link
              href="/auth/signup"
              className="text-lime-400 hover:text-lime-300 font-semibold transition-colors cursor-pointer"
            >
              Sign up
            </Link>
          </p>
          <p className="text-center text-xs text-slate-500 leading-relaxed">
            By continuing, you agree to our{" "}
            <Link
              href="/terms"
              className="underline hover:text-lime-400 transition-colors cursor-pointer"
            >
              Terms of Service
            </Link>{" "}
            and{" "}
            <Link
              href="/privacy"
              className="underline hover:text-lime-400 transition-colors cursor-pointer"
            >
              Privacy Policy
            </Link>
          </p>
        </CardFooter>
      </Card>
    </div>
  );
}
