"use client";
import { useState } from "react";
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
import { Mail, Lock, Eye, EyeOff, Globe, User } from "lucide-react";
import { useMutation } from "@tanstack/react-query";
import { registerUser } from "@/api/user";
import { toast } from "sonner";
import { AxiosError } from "axios";

export default function SignupPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const { mutate: signup, isPending:isLoading } = useMutation({
    mutationKey: ["registerUser"],
    mutationFn: () =>
      registerUser({
        name,
        email,
        password,
        passwordConfirmation: confirmPassword,
      }),
    onSuccess: (data) => {
      console.log(data);
      setName("");
      setEmail("");
      setPassword("");
      setConfirmPassword("");

      router.push("/auth/login");
    },
    onError: (error: AxiosError) => {
      const errorMessage =
        error?.response?.data?.detail ||
        error?.message ||
        "An unexpected error occurred";
      toast.error(errorMessage);
    },
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    signup();
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
          Create your account
        </h1>
        <p className="text-sm sm:text-base text-slate-400">
          Start evaluating your LLMs today
        </p>
      </div>

      <Card className="bg-slate-900/80 border-slate-800/80 backdrop-blur-xl shadow-2xl shadow-black/40 rounded-2xl overflow-hidden">
        <CardHeader className="text-center px-6 pt-8 pb-4 space-y-1">
          <CardTitle className="text-xl sm:text-2xl font-semibold text-white tracking-tight">
            Sign up
          </CardTitle>
          <CardDescription className="text-xs sm:text-sm text-slate-400">
            Create your free Proof account
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
                htmlFor="name"
                className="text-slate-300 text-xs sm:text-sm font-medium"
              >
                Full Name
              </Label>
              <div className="relative">
                <User className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  id="name"
                  type="text"
                  placeholder="John Doe"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="pl-10 h-11 bg-slate-950/60 border-slate-800 text-white placeholder-slate-500 text-sm sm:text-base focus-visible:border-lime-500 focus-visible:ring-lime-500/20 transition-all"
                  required
                  disabled={isLoading}
                />
              </div>
            </div>

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
              <Label
                htmlFor="password"
                className="text-slate-300 text-xs sm:text-sm font-medium"
              >
                Password
              </Label>
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
                  minLength={8}
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

            <div className="space-y-2">
              <Label
                htmlFor="confirmPassword"
                className="text-slate-300 text-xs sm:text-sm font-medium"
              >
                Confirm Password
              </Label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  id="confirmPassword"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="pl-10 h-11 bg-slate-950/60 border-slate-800 text-white placeholder-slate-500 text-sm sm:text-base focus-visible:border-lime-500 focus-visible:ring-lime-500/20 transition-all"
                  required
                  disabled={isLoading}
                />
              </div>
            </div>

            <Button
              type="submit"
              className="w-full h-11 bg-lime-500 hover:bg-lime-400 text-slate-950 font-semibold text-base transition-all duration-200 shadow-lg shadow-lime-500/20 hover:shadow-lime-500/30 active:scale-[0.99] cursor-pointer"
              disabled={isLoading}
            >
              {isLoading ? "Creating account..." : "Create account"}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex flex-col gap-4 border-t border-slate-800/80 px-6 py-5 bg-slate-950/20">
          <p className="text-center text-xs sm:text-sm text-slate-400">
            Already have an account?{" "}
            <Link
              href="/auth/login"
              className="text-lime-400 hover:text-lime-300 font-semibold transition-colors cursor-pointer"
            >
              Sign in
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
