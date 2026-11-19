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
import { CheckCircle2, Loader2, Mail, XCircle } from "lucide-react";
import { useMutation } from "@tanstack/react-query";
import { verifyEmail } from "@/api/user";
import { toast } from "sonner";

export default function VerifyEmailPage() {
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return null;
  }

  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";

  const [status, setStatus] = React.useState<"idle" | "success" | "error">(
    "idle"
  );

  const { mutate: verify, isPending } = useMutation({
    mutationKey: ["verifyEmail"],
    mutationFn: () => verifyEmail({ token }),
    onSuccess: () => {
      setStatus("success");
      toast.success("Email verified successfully");
      router.push("/auth/login");
    },
    onError: () => {
      setStatus("error");
      toast.error("Invalid or expired verification link");
    },
  });

  React.useEffect(() => {
    if (!token) {
      setStatus("error");
      toast.error("No verification token found in the link");
      return;
    }
    verify();
  }, [token, verify]);

  if (status === "idle") {
    return (
      <div className="w-full max-w-md mx-auto px-4 sm:px-6 py-8 sm:py-24 animate-in fade-in-50 duration-500">
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
            Verifying email
          </h1>
          <p className="text-sm sm:text-base text-slate-400">
            Please wait while we verify your account
          </p>
        </div>

        <Card className="bg-[#0a0a0f] border border-slate-800 shadow-lg rounded-2xl">
          <CardContent className="text-center p-8">
            <Loader2 className="w-8 h-8 text-lime-500 animate-spin mx-auto mb-4" />
            <p className="text-slate-500">Verifying your email...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const isSuccess = status === "success";
  const isError = status === "error";

  return (
    <div className="w-full max-w-md mx-auto px-4 sm:px-6 py-8 sm:py-24 animate-in fade-in-50 duration-500">
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
        {isSuccess ? (
          <>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
              Email verified
            </h1>
            <p className="text-sm sm:text-base text-slate-400">
              Your email address has been confirmed
            </p>
          </>
        ) : (
          <>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
              Verification failed
            </h1>
            <p className="text-sm sm:text-base text-slate-400">
              The link is invalid or has expired
            </p>
          </>
        )}
      </div>

      <Card className="bg-[#0a0a0f] border border-slate-800 shadow-lg rounded-2xl">
        <CardHeader className={`text-center space-y-2 border-b-2 ${isSuccess ? "border-green-500/30" : "border-red-500/30"}`}>
          <div className={`flex items-center justify-center w-12 h-12 rounded-full mx-auto mb-4 ${
            isSuccess ? "bg-green-500/10" : "bg-red-500/10"
          }`}>
            {isSuccess ? (
              <CheckCircle2 className="w-6 h-6 text-green-400" />
            ) : (
              <XCircle className="w-6 h-6 text-red-400" />
            )}
          </div>
          <CardTitle className="text-xl font-bold text-white">
            {isSuccess ? "Success!" : "Oops!"}
          </CardTitle>
          <CardDescription className="text-slate-400">
            {isSuccess
              ? "Your email address has been verified. You can now log in."
              : "This verification link is no longer valid. Request a new one below."}
          </CardDescription>
        </CardHeader>

        <CardContent className="text-center space-y-6 pt-0">
          {isSuccess ? (
            <>
              <Mail className="w-10 h-10 text-green-400 mx-auto mb-2" />
              <p className="text-sm text-slate-500">
                You can now sign in with your credentials.
              </p>
            </>
          ) : (
            <>
              <p className="text-sm text-slate-500">
                Didn&apos;t receive the email? Request a new verification link.
              </p>
              <Button
                onClick={() => router.push("/auth/resend-verification")}
                className="w-full h-11 bg-lime-500 hover:bg-lime-400 text-slate-950 font-semibold text-base transition-all duration-200 shadow-lg shadow-lime-500/20 hover:shadow-lime-500/30 active:scale-[0.99] cursor-pointer"
              >
                Send new verification email
              </Button>
            </>
          )}
        </CardContent>

        <CardFooter className="flex flex-col gap-4 border-t border-slate-800/80 px-6 py-5 bg-[#0a0a0f]/50">
          <Button
            variant="outline"
            onClick={() => router.push("/auth/login")}
            className="w-full h-11 border-slate-700 hover:border-lime-400 text-slate-300 hover:text-white font-medium transition-colors cursor-pointer"
          >
            Go to login
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}