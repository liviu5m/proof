"use client";
import * as React from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { CheckCircle2, Mail } from "lucide-react";
import { useMutation } from "@tanstack/react-query";
import { resendVerification } from "@/api/user";
import { toast } from "sonner";

export default function VerifyEmailSentPage() {
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return null;
  }

  const router = useRouter();
  const searchParams = useSearchParams();
  const email = searchParams.get("email") || "";

  const { mutate: resend, isPending } = useMutation({
    mutationKey: ["resendVerification"],
    mutationFn: () => resendVerification({ email }),
    onSuccess: () => {
      toast.success("Verification email sent again");
    },
    onError: () => {
      toast.error("Failed to resend verification email");
    },
  });

  const handleResend = () => {
    if (!email) {
      toast.error("No email found. Please register again.");
      router.push("/auth/signup");
      return;
    }
    resend();
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
          Account created
        </h1>
        <p className="text-sm sm:text-base text-slate-400">
          Check your inbox to verify your email address
        </p>
      </div>

      <Card className="bg-[#0a0a0f] border border-slate-800 shadow-lg rounded-2xl">
        <CardHeader className="text-center space-y-2">
          <div className="flex items-center justify-center w-12 h-12 bg-green-100 rounded-full mx-auto mb-4">
            <CheckCircle2 className="w-6 h-6 text-green-600" />
          </div>
          <CardTitle className="text-2xl font-bold text-white">Verify your email</CardTitle>
          <CardDescription className="text-slate-400">
            We&apos;ve sent a verification link to <strong className="text-white font-medium">{email}</strong>. Please open your inbox and click the link to activate your account before logging in.
          </CardDescription>
        </CardHeader>

        <CardContent className="text-center space-y-6 pt-0">
          <div className="flex flex-col items-center gap-2">
            <Mail className="w-10 h-10 text-slate-500" />
            <p className="text-sm text-slate-500">
              Check {email || "your email"}
            </p>
          </div>
          <Button
            onClick={handleResend}
            disabled={isPending || !email}
            className="w-full h-11 bg-lime-500 hover:bg-lime-400 text-slate-950 font-semibold text-base transition-all duration-200 shadow-lg shadow-lime-500/20 hover:shadow-lime-500/30 active:scale-[0.99] cursor-pointer"
          >
            {isPending ? (
              <>
                <svg className="w-4 h-4 mr-2 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Sending...
              </>
            ) : (
              "Resend verification email"
            )}
          </Button>
        </CardContent>

        <CardFooter className="flex flex-col gap-4 border-t border-slate-800/80 px-6 py-5 bg-[#0a0a0f]/50">
          <Button
            variant="outline"
            onClick={() => router.push("/auth/login")}
            className="w-full h-11 border-slate-700 hover:border-lime-400 text-slate-300 hover:text-white font-medium transition-colors cursor-pointer"
          >
            Back to login
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}