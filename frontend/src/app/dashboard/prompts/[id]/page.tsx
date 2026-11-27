"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import Swal from "sweetalert2";
import {
  ArrowLeft,
  Copy,
  Eye,
  GitBranch,
  GitCompare,
  Pencil,
  Plus,
  RotateCcw,
  Trash2,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import Loader from "@/components/Loader";
import { cn, formatDate } from "@/libs/utils";
import {
  activatePromptVersion,
  comparePromptVersions,
  createPromptVersion,
  deletePromptVersion,
  getPromptRegistry,
  updatePromptRegistry,
} from "@/api/prompts";
import {
  PromptComparison,
  PromptVersion,
} from "@/types/prompts";

function DiffView({ diff }: { diff: string }) {
  const lines = diff.split("\n");
  if (!diff.trim()) {
    return <p className="text-sm text-slate-500">No differences between these versions.</p>;
  }

  return (
    <pre className="max-h-96 overflow-auto rounded-xl border border-slate-800 bg-slate-950 py-2 font-mono text-xs leading-relaxed">
      {lines.map((line, i) => {
        const tone =
          line.startsWith("@@")
            ? "text-indigo-300"
            : line.startsWith("+++") || line.startsWith("---")
              ? "text-slate-500"
              : line.startsWith("+")
                ? "bg-emerald-500/[0.07] text-emerald-400"
                : line.startsWith("-")
                  ? "bg-rose-500/[0.07] text-rose-400"
                  : "text-slate-400";
        return (
          <div key={i} className={cn("whitespace-pre-wrap break-words px-4", tone)}>
            {line || " "}
          </div>
        );
      })}
    </pre>
  );
}

export default function PromptDetailPage() {
  const params = useParams();
  const queryClient = useQueryClient();
  const registryId = Number(params.id);

  const [selected, setSelected] = useState<number[]>([]);
  const [viewing, setViewing] = useState<PromptVersion | null>(null);
  const [comparison, setComparison] = useState<PromptComparison | null>(null);
  const [versionDraft, setVersionDraft] = useState({
    open: false,
    content: "",
    description: "",
  });
  const [editDraft, setEditDraft] = useState({
    open: false,
    name: "",
    description: "",
  });

  const {
    data: registry,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["promptRegistry", registryId],
    queryFn: () => getPromptRegistry(registryId),
    enabled: Number.isFinite(registryId),
  });

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ["promptRegistry", registryId] });
    queryClient.invalidateQueries({ queryKey: ["promptRegistries"] });
  };

  const failed = (fallback: string) => (error: any) =>
    toast.error(error?.response?.data?.error || fallback);

  const createVersion = useMutation({
    mutationFn: async (data: { content: string; description: string }) => {
      const version = await createPromptVersion(registryId, data);
      await activatePromptVersion(registryId, version.id);
      return version;
    },
    onSuccess: (version) => {
      toast.success(`v${version.version_number} saved and activated`);
      setVersionDraft({ open: false, content: "", description: "" });
      refresh();
    },
    onError: failed("Failed to create version"),
  });

  const activateVersion = useMutation({
    mutationFn: (versionId: number) => activatePromptVersion(registryId, versionId),
    onSuccess: () => {
      toast.success("Version activated");
      refresh();
    },
    onError: failed("Failed to activate version"),
  });

  const removeVersion = useMutation({
    mutationFn: (versionId: number) => deletePromptVersion(registryId, versionId),
    onSuccess: () => {
      toast.success("Version deleted");
      setSelected([]);
      setComparison(null);
      refresh();
    },
    onError: failed("Failed to delete version"),
  });

  const compare = useMutation({
    mutationFn: (ids: number[]) =>
      comparePromptVersions(registryId, ids[0], ids[1]),
    onSuccess: (result) => setComparison(result),
    onError: failed("Failed to compare versions"),
  });

  const editRegistry = useMutation({
    mutationFn: (data: { name: string; description: string }) =>
      updatePromptRegistry(registryId, data),
    onSuccess: () => {
      toast.success("Registry updated");
      setEditDraft({ open: false, name: "", description: "" });
      refresh();
    },
    onError: failed("Failed to update registry"),
  });

  const toggleCompare = (versionId: number) => {
    setComparison(null);
    setSelected((prev) => {
      if (prev.includes(versionId)) return prev.filter((id) => id !== versionId);
      if (prev.length >= 2) return prev;
      return [...prev, versionId];
    });
  };

  const clearCompare = () => {
    setSelected([]);
    setComparison(null);
  };

  const confirmDelete = async (version: PromptVersion) => {
    const result = await Swal.fire({
      title: `Delete v${version.version_number}?`,
      text: "The version is archived and removed from the registry. This cannot be undone.",
      icon: "warning",
      showCancelButton: true,
      confirmButtonColor: "#ef4444",
      cancelButtonColor: "#334155",
      confirmButtonText: "Delete version",
      background: "#0f172a",
      color: "#f8fafc",
    });
    if (result.isConfirmed) removeVersion.mutate(version.id);
  };

  if (!Number.isFinite(registryId)) {
    return (
      <div className="flex h-[50vh] items-center justify-center text-slate-400">
        Invalid registry id.
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-[50vh] flex-col items-center justify-center gap-3">
        <h1 className="text-xl font-semibold text-red-400">Failed to load registry</h1>
        <Link href="/dashboard/prompts">
          <Button variant="outline" className="border-slate-700 text-slate-300">
            Back to registries
          </Button>
        </Link>
      </div>
    );
  }

  if (isLoading || !registry) return <Loader />;

  const versions = registry.versions;
  const current = registry.current_version;
  const busy =
    createVersion.isPending ||
    activateVersion.isPending ||
    removeVersion.isPending;

  const stats = [
    {
      label: "Current version",
      value: current ? `v${current.version_number}` : "—",
      hint: current ? current.content_hash.slice(0, 10) : "No active version",
    },
    {
      label: "Versions",
      value: String(registry.version_count),
      hint: "immutable snapshots",
    },
    {
      label: "Last updated",
      value: formatDate(registry.updated_at),
      hint: `Created ${formatDate(registry.created_at)}`,
    },
  ];

  return (
    <div className="mx-auto max-w-5xl space-y-6 animate-in fade-in-50 duration-500">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <Link
            href="/dashboard/prompts"
            className="inline-flex items-center gap-2 text-sm text-slate-400 transition-colors hover:text-white"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to registries
          </Link>
          <h1 className="mt-3 flex items-center gap-2 truncate text-2xl font-bold text-white">
            <GitBranch className="h-5 w-5 shrink-0 text-indigo-400" />
            {registry.name}
          </h1>
          <p className="mt-1 line-clamp-2 text-sm text-slate-400">
            {registry.description || "No description"}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            className="gap-2 border-slate-700 bg-transparent text-slate-300 hover:bg-slate-800 hover:text-white"
            onClick={() =>
              setEditDraft({
                open: true,
                name: registry.name,
                description: registry.description ?? "",
              })
            }
          >
            <Pencil className="h-4 w-4" /> Edit
          </Button>
          <Button
            className="gap-2 bg-lime-500 font-semibold text-slate-950 hover:bg-lime-400"
            onClick={() =>
              setVersionDraft({ open: true, content: "", description: "" })
            }
          >
            <Plus className="h-4 w-4" /> New version
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {stats.map((stat) => (
          <div
            key={stat.label}
            className="rounded-2xl border border-slate-800 bg-slate-900/70 px-5 py-4"
          >
            <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
              {stat.label}
            </p>
            <p className="mt-1.5 truncate text-xl font-semibold text-white">
              {stat.value}
            </p>
            <p className="mt-0.5 truncate font-mono text-xs text-slate-500">
              {stat.hint}
            </p>
          </div>
        ))}
      </div>

      <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/70">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 px-5 py-4">
          <div>
            <h2 className="text-base font-semibold text-white">Versions</h2>
            <p className="text-xs text-slate-500">
              Select two versions to compare. New versions are never mutated.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500">{selected.length}/2 selected</span>
            <Button
              size="sm"
              variant="ghost"
              className="text-slate-400 hover:bg-slate-800 hover:text-white"
              onClick={clearCompare}
              disabled={selected.length === 0 && !comparison}
            >
              Clear
            </Button>
            <Button
              size="sm"
              className="gap-2 bg-indigo-500 font-medium text-white hover:bg-indigo-400 disabled:bg-slate-800 disabled:text-slate-500"
              onClick={() => compare.mutate(selected)}
              disabled={selected.length !== 2 || compare.isPending}
            >
              <GitCompare className="h-4 w-4" />
              {compare.isPending ? "Comparing..." : "Compare"}
            </Button>
          </div>
        </div>

        {versions.length === 0 ? (
          <p className="px-5 py-10 text-center text-sm text-slate-500">
            No versions yet.
          </p>
        ) : (
          <div>
            {versions.map((version) => {
              const isCurrent = version.id === registry.current_version_id;
              const isSelected = selected.includes(version.id);
              const isCompared =
                comparison?.v1.id === version.id || comparison?.v2.id === version.id;

              return (
                <div
                  key={version.id}
                  className={cn(
                    "grid grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-4 border-t border-slate-800/60 px-5 py-3.5 transition-colors",
                    isCurrent && "bg-emerald-500/[0.06]",
                    isCompared && "bg-indigo-500/[0.06]",
                    !isCurrent && !isCompared && "hover:bg-slate-800/40",
                  )}
                >
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => toggleCompare(version.id)}
                      disabled={selected.length >= 2 && !isSelected}
                      aria-label={`Select v${version.version_number} for comparison`}
                      className="h-4 w-4 cursor-pointer rounded border-slate-600 bg-slate-950 accent-indigo-500 disabled:cursor-not-allowed disabled:opacity-40"
                    />
                    <span className="font-mono text-sm font-medium text-white">
                      v{version.version_number}
                    </span>
                    {isCurrent ? (
                      <Badge className="border-emerald-500/30 bg-emerald-500/10 text-emerald-400">
                        Current
                      </Badge>
                    ) : (
                      <Badge
                        variant="secondary"
                        className="border-slate-700 bg-slate-800 text-slate-400"
                      >
                        Archived
                      </Badge>
                    )}
                  </div>

                  <div className="min-w-0">
                    <p className="truncate text-sm text-slate-200">
                      {version.description || "No description"}
                    </p>
                    <p className="mt-0.5 truncate font-mono text-xs text-slate-500">
                      {version.content_hash.slice(0, 12)} ·{" "}
                      {formatDate(version.created_at)}
                    </p>
                  </div>

                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      title="View content"
                      className="h-8 w-8 text-slate-400 hover:bg-slate-800 hover:text-white"
                      onClick={() => setViewing(version)}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      title="Duplicate as new version"
                      className="h-8 w-8 text-slate-400 hover:bg-slate-800 hover:text-white"
                      disabled={busy}
                      onClick={() =>
                        setVersionDraft({
                          open: true,
                          content: version.content,
                          description: `Copy of v${version.version_number}`,
                        })
                      }
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                    {!isCurrent && (
                      <Button
                        variant="ghost"
                        size="icon"
                        title="Activate this version"
                        className="h-8 w-8 text-slate-400 hover:bg-slate-800 hover:text-emerald-400"
                        disabled={busy}
                        onClick={() => activateVersion.mutate(version.id)}
                      >
                        <RotateCcw className="h-4 w-4" />
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="icon"
                      title={
                        versions.length === 1
                          ? "Cannot delete the only version"
                          : "Delete version"
                      }
                      className="h-8 w-8 text-slate-400 hover:bg-slate-800 hover:text-rose-400"
                      disabled={busy || versions.length === 1}
                      onClick={() => confirmDelete(version)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {comparison && (
        <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/70">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 px-5 py-4">
            <div>
              <h2 className="text-base font-semibold text-white">
                v{comparison.v1.version_number} → v{comparison.v2.version_number}
              </h2>
              <p className="font-mono text-xs text-slate-500">
                {comparison.v1.content_hash.slice(0, 10)} →{" "}
                {comparison.v2.content_hash.slice(0, 10)}
              </p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="text-slate-400 hover:bg-slate-800 hover:text-white"
              onClick={clearCompare}
            >
              Clear
            </Button>
          </div>
          <div className="p-5">
            <DiffView diff={comparison.diff} />
          </div>
        </div>
      )}

      {viewing && (
        <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/70">
          <div className="flex items-center justify-between gap-3 border-b border-slate-800 px-5 py-4">
            <div className="min-w-0">
              <h2 className="text-base font-semibold text-white">
                v{viewing.version_number} content
              </h2>
              <p className="truncate text-xs text-slate-500">
                {viewing.description || "No description"} ·{" "}
                {viewing.content_hash.slice(0, 12)}
              </p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="text-slate-400 hover:bg-slate-800 hover:text-white"
              onClick={() => setViewing(null)}
            >
              Close
            </Button>
          </div>
          <pre className="max-h-96 overflow-auto whitespace-pre-wrap break-words p-5 font-mono text-sm text-slate-300">
            {viewing.content}
          </pre>
        </div>
      )}

      <Dialog
        open={versionDraft.open}
        onOpenChange={(open) => setVersionDraft((d) => ({ ...d, open }))}
      >
        <DialogContent className="max-w-2xl border-slate-800 bg-slate-900 text-white">
          <DialogHeader>
            <DialogTitle>New version</DialogTitle>
            <DialogDescription className="text-slate-400">
              Saving creates an immutable snapshot and makes it the current version.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="version-description" className="text-slate-300">
                Description (optional)
              </Label>
              <Input
                id="version-description"
                placeholder="What changed in this version?"
                className="border-slate-800 bg-slate-950 text-white placeholder-slate-500"
                value={versionDraft.description}
                onChange={(e) =>
                  setVersionDraft((d) => ({ ...d, description: e.target.value }))
                }
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="version-content" className="text-slate-300">
                Prompt content
              </Label>
              <Textarea
                id="version-content"
                placeholder="Enter the prompt content..."
                className="min-h-[200px] resize-none border-slate-800 bg-slate-950 font-mono text-sm text-white placeholder-slate-500"
                value={versionDraft.content}
                onChange={(e) =>
                  setVersionDraft((d) => ({ ...d, content: e.target.value }))
                }
              />
            </div>
          </div>

          <DialogFooter className="gap-2">
            <Button
              variant="outline"
              className="border-slate-700 bg-transparent text-slate-300 hover:bg-slate-800 hover:text-white"
              onClick={() => setVersionDraft({ open: false, content: "", description: "" })}
            >
              Cancel
            </Button>
            <Button
              className="bg-lime-500 font-semibold text-slate-950 hover:bg-lime-400"
              onClick={() =>
                createVersion.mutate({
                  content: versionDraft.content,
                  description: versionDraft.description,
                })
              }
              disabled={createVersion.isPending || !versionDraft.content.trim()}
            >
              {createVersion.isPending ? "Saving..." : "Save & activate"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog
        open={editDraft.open}
        onOpenChange={(open) => setEditDraft((d) => ({ ...d, open }))}
      >
        <DialogContent className="border-slate-800 bg-slate-900 text-white">
          <DialogHeader>
            <DialogTitle>Edit registry</DialogTitle>
            <DialogDescription className="text-slate-400">
              Rename the registry or change its description. Versions are unaffected.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="registry-name" className="text-slate-300">
                Name
              </Label>
              <Input
                id="registry-name"
                className="border-slate-800 bg-slate-950 text-white placeholder-slate-500"
                value={editDraft.name}
                onChange={(e) =>
                  setEditDraft((d) => ({ ...d, name: e.target.value }))
                }
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="registry-description" className="text-slate-300">
                Description
              </Label>
              <Textarea
                id="registry-description"
                className="min-h-[90px] resize-none border-slate-800 bg-slate-950 text-white placeholder-slate-500"
                value={editDraft.description}
                onChange={(e) =>
                  setEditDraft((d) => ({ ...d, description: e.target.value }))
                }
              />
            </div>
          </div>

          <DialogFooter className="gap-2">
            <Button
              variant="outline"
              className="border-slate-700 bg-transparent text-slate-300 hover:bg-slate-800 hover:text-white"
              onClick={() => setEditDraft({ open: false, name: "", description: "" })}
            >
              Cancel
            </Button>
            <Button
              className="bg-indigo-500 font-semibold text-white hover:bg-indigo-400"
              onClick={() =>
                editRegistry.mutate({
                  name: editDraft.name,
                  description: editDraft.description,
                })
              }
              disabled={editRegistry.isPending || !editDraft.name.trim()}
            >
              {editRegistry.isPending ? "Saving..." : "Save changes"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
