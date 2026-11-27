"use client";

import React, { useEffect, useState } from "react";
import { ChevronDown, FileText, GitBranch } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { getPromptRegistries, getPromptRegistry } from "@/api/prompts";
import { PromptVersion } from "@/types/prompts";

interface PromptSelectorProps {
  selectedRegistryId?: number;
  selectedVersionId?: number;
  onChange: (registryId: number, versionId: number) => void;
  disabled?: boolean;
  className?: string;
}

export function PromptSelector({
  selectedRegistryId,
  selectedVersionId,
  onChange,
  disabled = false,
  className = "",
}: PromptSelectorProps) {
  const [activeRegistryId, setActiveRegistryId] = useState<number | undefined>(
    selectedRegistryId,
  );
  const [registryOpen, setRegistryOpen] = useState(false);
  const [versionOpen, setVersionOpen] = useState(false);

  useEffect(() => {
    if (selectedRegistryId !== undefined) setActiveRegistryId(selectedRegistryId);
  }, [selectedRegistryId]);

  const { data: registries = [], isLoading: registriesLoading } = useQuery({
    queryKey: ["promptRegistries"],
    queryFn: getPromptRegistries,
  });

  const { data: detail, isLoading: detailLoading } = useQuery({
    queryKey: ["promptRegistry", activeRegistryId],
    queryFn: () => getPromptRegistry(activeRegistryId as number),
    enabled: Number.isFinite(activeRegistryId),
  });

  const activeRegistry = registries.find((r) => r.id === activeRegistryId);
  const versions = detail?.versions ?? [];
  const selectedVersion = versions.find((v: PromptVersion) => v.id === selectedVersionId);
  const currentVersion = detail?.current_version;

  const versionLabel = selectedVersion
    ? `${selectedVersion.content_hash.slice(0, 8)} (v${selectedVersion.version_number})`
    : currentVersion
      ? `${currentVersion.content_hash.slice(0, 8)} (current v${currentVersion.version_number})`
      : "Select version";

  if (registriesLoading) {
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        <div className="h-10 w-full animate-pulse rounded-lg bg-slate-800" />
      </div>
    );
  }

  return (
    <div className={`space-y-2 ${className}`}>
      {/* Registry */}
      <div className="relative">
        <Button
          type="button"
          variant="outline"
          className="h-10 w-full justify-between gap-2 border-slate-800 bg-slate-950/60 px-3 text-sm text-white hover:bg-slate-800/50"
          onClick={() => {
            setRegistryOpen((open) => !open);
            setVersionOpen(false);
          }}
          disabled={disabled || registries.length === 0}
        >
          <GitBranch className="h-4 w-4 shrink-0 text-slate-400" />
          <span className="flex-1 truncate text-left">
            {activeRegistry?.name ?? "Select prompt registry"}
          </span>
          <ChevronDown
            className={`h-4 w-4 shrink-0 text-slate-400 transition-transform ${registryOpen ? "rotate-180" : ""}`}
          />
        </Button>

        {registryOpen && (
          <div className="absolute z-50 mt-1 w-full overflow-hidden rounded-xl border border-slate-800 bg-slate-900 shadow-lg">
            {registries.length === 0 ? (
              <p className="px-4 py-3 text-sm text-slate-500">
                No prompt registries yet.
              </p>
            ) : (
              registries.map((registry) => (
                <button
                  key={registry.id}
                  type="button"
                  onClick={() => {
                    setActiveRegistryId(registry.id);
                    setRegistryOpen(false);
                    setVersionOpen(true);
                  }}
                  className={`w-full px-4 py-2.5 text-left transition-colors ${
                    activeRegistryId === registry.id
                      ? "bg-slate-800 text-white"
                      : "text-slate-300 hover:bg-slate-800 hover:text-white"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <GitBranch className="h-4 w-4 shrink-0 text-indigo-400" />
                    <span className="truncate text-sm">{registry.name}</span>
                  </div>
                  <p className="ml-6 truncate text-xs text-slate-500">
                    {registry.description || "No description"}
                  </p>
                </button>
              ))
            )}
          </div>
        )}
      </div>

      {/* Version */}
      <div className="relative">
        <Button
          type="button"
          variant="outline"
          className="h-10 w-full justify-between gap-2 border-slate-800 bg-slate-950/60 px-3 text-sm text-white hover:bg-slate-800/50"
          onClick={() => {
            setVersionOpen((open) => !open);
            setRegistryOpen(false);
          }}
          disabled={disabled || !activeRegistryId || versions.length === 0}
        >
          <FileText className="h-4 w-4 shrink-0 text-slate-400" />
          <span className="flex-1 truncate text-left font-mono text-xs">
            {versionLabel}
          </span>
          <ChevronDown
            className={`h-4 w-4 shrink-0 text-slate-400 transition-transform ${versionOpen ? "rotate-180" : ""}`}
          />
        </Button>

        {versionOpen && activeRegistryId && (
          <div className="absolute z-50 mt-1 w-full overflow-hidden rounded-xl border border-slate-800 bg-slate-900 shadow-lg">
            {detailLoading ? (
              <p className="px-4 py-3 text-sm text-slate-500">Loading versions...</p>
            ) : versions.length === 0 ? (
              <p className="px-4 py-3 text-sm text-slate-500">
                This registry has no versions.
              </p>
            ) : (
              <div className="max-h-64 overflow-y-auto">
                {versions.map((version: PromptVersion) => (
                  <button
                    key={version.id}
                    type="button"
                    onClick={() => {
                      onChange(activeRegistryId, version.id);
                      setVersionOpen(false);
                    }}
                    className={`w-full px-4 py-2.5 text-left transition-colors ${
                      selectedVersionId === version.id
                        ? "bg-emerald-500/10 text-emerald-400"
                        : "text-slate-300 hover:bg-slate-800 hover:text-white"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className="rounded bg-slate-800 px-2 py-0.5 font-mono text-xs">
                        {version.content_hash.slice(0, 8)}
                      </span>
                      <span className="text-sm font-medium">
                        v{version.version_number}
                      </span>
                      {version.is_current && (
                        <span className="ml-auto text-xs text-emerald-400">
                          current
                        </span>
                      )}
                    </div>
                    <p className="mt-1 truncate pl-0 text-xs text-slate-500">
                      {version.description || "No description"}
                    </p>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
