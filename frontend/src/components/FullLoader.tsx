import React from "react";

interface FullScreenLoaderProps {
  size?: "sm" | "md" | "lg";
  text?: string;
  blur?: boolean;
}

const sizeClasses = {
  sm: "w-6 h-6 border-2",
  md: "w-10 h-10 border-3",
  lg: "w-16 h-16 border-4",
};

export default function FullScreenLoader({
  size = "md",
  text = "Loading...",
  blur = true,
}: FullScreenLoaderProps) {
  return (
    <div
      className={`
        fixed inset-0 z-50 
        flex flex-col items-center justify-center gap-3 
        bg-white/80 dark:bg-zinc-950/80 
        ${blur ? "backdrop-blur-sm" : ""}
        transition-opacity duration-300
      `}
      role="status"
      aria-label="Loading page"
    >
      <div
        className={`
          ${sizeClasses[size]}
          border-zinc-200 dark:border-zinc-800
          border-t-indigo-600 dark:border-t-indigo-500
          rounded-full
          animate-spin
        `}
      />

      {text && (
        <p className="text-sm font-medium text-zinc-600 dark:text-zinc-400 animate-pulse">
          {text}
        </p>
      )}
    </div>
  );
}
