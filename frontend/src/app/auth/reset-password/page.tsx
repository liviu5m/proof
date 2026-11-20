import { Suspense } from "react";
import { ResetPasswordForm } from "./ResetPasswordForm";

export const dynamic = "force-dynamic";

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="w-full max-w-md mx-auto px-4 sm:px-6 py-8 sm:py-24">Loading...</div>}>
      <ResetPasswordForm />
    </Suspense>
  );
}
