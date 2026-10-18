import React from "react";

interface LoaderProps {
  size?: "sm" | "md" | "lg";
  text?: string;
}

const sizeClasses = {
  sm: "w-4 h-4 border-2",
  md: "w-8 h-8 border-3",
  lg: "w-12 h-12 border-4",
};

export default function Loader({ size = "md", text }: LoaderProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 p-4">
      <div
        className={`
          ${sizeClasses[size]}
          border-zinc-200 dark:border-zinc-800
          border-t-indigo-600 dark:border-t-indigo-500
          rounded-full
          animate-spin
        `}
        role="status"
        aria-label="Loading"
      />
      {text && (
        <p className="text-sm font-medium text-zinc-600 dark:text-zinc-400 animate-pulse">
          {text}
        </p>
      )}
    </div>
  );
}
