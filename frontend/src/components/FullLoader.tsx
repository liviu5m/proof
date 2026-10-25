import React from "react";

interface FullScreenLoaderProps {
  size?: "sm" | "md" | "lg";
  text?: string;
  blur?: boolean;
}

export default function FullScreenLoader({
  text = "Loading...",
  blur = true,
}: FullScreenLoaderProps) {
  return (
    <div
      className={`
        fixed inset-0 z-50 
        flex flex-col items-center justify-center gap-4 
        bg-slate-950/80 
        ${blur ? "backdrop-blur-md" : ""}
        transition-opacity duration-300
      `}
      role="status"
      aria-label="Loading page"
    >
      <div className="inline-flex scale-125" role="status" aria-label="loading">
        <span
          className="flex h-6 items-center justify-center gap-1"
          aria-hidden="true"
        >
          <span className="h-2.5 w-1 rounded-full bg-indigo-500 origin-center [animation:spinner-wave_0.9s_ease-in-out_infinite_0s]" />
          <span className="h-3.5 w-1 rounded-full bg-indigo-500 origin-center [animation:spinner-wave_0.9s_ease-in-out_infinite_0.12s]" />
          <span className="h-4.5 w-1 rounded-full bg-indigo-500 origin-center [animation:spinner-wave_0.9s_ease-in-out_infinite_0.24s]" />
          <span className="h-3.5 w-1 rounded-full bg-indigo-500 origin-center [animation:spinner-wave_0.9s_ease-in-out_infinite_0.36s]" />
          <span className="h-2.5 w-1 rounded-full bg-indigo-500 origin-center [animation:spinner-wave_0.9s_ease-in-out_infinite_0.48s]" />
        </span>
        <span className="sr-only">Loading...</span>
      </div>

      {text && (
        <p className="text-xs font-bold text-slate-300 uppercase tracking-widest animate-pulse mt-2">
          {text}
        </p>
      )}
    </div>
  );
}
