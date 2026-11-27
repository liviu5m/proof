"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import Swal from "sweetalert2";
import {
  Eye,
  GitBranch,
  Pencil,
  Plus,
  Search,
  Trash2,
} from "lucide-react";

import { Button } from "@/components/ui/button";
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
import { formatDate } from "@/libs/utils";
import {
  createPromptRegistry,
  deletePromptRegistry,
  getPromptRegistries,
  updatePromptRegistry,
} from "@/api/prompts";
import { PromptRegistry } from "@/types/prompts";

export default function PromptsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [createDraft, setCreateDraft] = useState({
    open: false,
    name: "",
    description: "",
    content: "",
  });
  const [editDraft, setEditDraft] = useState<{
    open: boolean;
    id: number | null;
    name: string;
    description: string;
  }>({ open: false, id: null, name: "", description: "" });

  const {
    data: registries,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["promptRegistries"],
    queryFn: getPromptRegistries,
  });

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ["promptRegistries"] });
  };

  const failed = (fallback: string) => (error: any) =>
    toast.error(error?.response?.data?.error || fallback);

  const createRegistry = useMutation({
    mutationFn: createPromptRegistry,
    onSuccess: () => {
      toast.success("Prompt registry created");
      setCreateDraft({ open: false, name: "", description: "", content: "" });
      refresh();
    },
    onError: failed("Failed to create registry"),
  });

  const editRegistry = useMutation({
    mutationFn: (data: { id: number; name: string; description: string }) =>
      updatePromptRegistry(data.id, {
        name: data.name,
        description: data.description,
      }),
    onSuccess: (_, variables) => {
      toast.success("Registry updated");
      setEditDraft({ open: false, id: null, name: "", description: "" });
      refresh();
      queryClient.invalidateQueries({ queryKey: ["promptRegistry", variables.id] });
    },
    onError: failed("Failed to update registry"),
  });

  const removeRegistry = useMutation({
    mutationFn: (id: number) => deletePromptRegistry(id),
    onSuccess: () => {
      toast.success("Registry deleted");
      refresh();
    },
    onError: failed("Failed to delete registry"),
  });

  const confirmDelete = async (registry: PromptRegistry) => {
    const result = await Swal.fire({
      title: "Delete registry?",
      text: `Delete "${registry.name}" and its ${registry.version_count} version(s)? This cannot be undone.`,
      icon: "warning",
      showCancelButton: true,
      confirmButtonColor: "#ef4444",
      cancelButtonColor: "#334155",
      confirmButtonText: "Delete registry",
      background: "#0f172a",
      color: "#f8fafc",
    });
    if (result.isConfirmed) removeRegistry.mutate(registry.id);
  };

  const query = search.trim().toLowerCase();
  const visible = (registries ?? []).filter(
    (registry) =>
      registry.name.toLowerCase().includes(query) ||
      (registry.description ?? "").toLowerCase().includes(query),
  );

  return (
    <div className="mx-auto max-w-5xl space-y-6 animate-in fade-in-50 duration-500">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold text-white">
            <GitBranch className="h-5 w-5 text-indigo-400" />
            Prompt registry
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Manage versioned prompts. Versions are immutable; edits create new ones.
          </p>
        </div>
        <Button
          className="gap-2 bg-lime-500 font-semibold text-slate-950 hover:bg-lime-400"
          onClick={() =>
            setCreateDraft({ open: true, name: "", description: "", content: "" })
          }
        >
          <Plus className="h-4 w-4" /> New registry
        </Button>
      </div>

      <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/70">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 px-5 py-4">
          <div>
            <h2 className="text-base font-semibold text-white">
              Registries ({registries?.length ?? 0})
            </h2>
            <p className="text-xs text-slate-500">
              {visible.length} shown
              {query ? ` for "${search.trim()}"` : ""}
            </p>
          </div>
          <div className="relative w-full sm:w-64">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
            <Input
              placeholder="Search registries..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="border-slate-800 bg-slate-950 pl-9 text-white placeholder-slate-500 focus-visible:border-indigo-500"
            />
          </div>
        </div>

        {error ? (
          <p className="px-5 py-10 text-center text-sm text-red-400">
            Failed to load registries.
          </p>
        ) : isLoading ? (
          <div className="px-5 py-10">
            <Loader />
          </div>
        ) : visible.length === 0 ? (
          <div className="px-5 py-14 text-center">
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-slate-800 text-slate-400">
              <GitBranch className="h-5 w-5" />
            </div>
            <p className="text-sm font-medium text-white">
              {registries?.length ? "No matching registries" : "No registries yet"}
            </p>
            <p className="mt-1 text-xs text-slate-500">
              {registries?.length
                ? "Try a different search term."
                : "Create your first prompt registry to start tracking versions."}
            </p>
            {!registries?.length && (
              <Button
                className="mt-5 gap-2 bg-lime-500 font-semibold text-slate-950 hover:bg-lime-400"
                onClick={() =>
                  setCreateDraft({ open: true, name: "", description: "", content: "" })
                }
              >
                <Plus className="h-4 w-4" /> New registry
              </Button>
            )}
          </div>
        ) : (
          <div>
            {visible.map((registry) => (
              <div
                key={registry.id}
                className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-4 border-t border-slate-800/60 px-5 py-4 transition-colors hover:bg-slate-800/40"
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="truncate font-medium text-white">
                      {registry.name}
                    </p>
                    <span className="shrink-0 rounded-md border border-slate-700 bg-slate-800 px-2 py-0.5 font-mono text-xs text-slate-300">
                      v{registry.current_version_position ?? 1}
                    </span>
                  </div>
                  <p className="mt-0.5 truncate text-sm text-slate-500">
                    {registry.description || "No description"}
                  </p>
                  <p className="mt-1 text-xs text-slate-600">
                    {registry.version_count} version
                    {registry.version_count === 1 ? "" : "s"} · updated{" "}
                    {formatDate(registry.updated_at)}
                  </p>
                </div>

                <div className="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    title="View versions"
                    className="h-8 w-8 text-slate-400 hover:bg-slate-800 hover:text-white"
                    onClick={() => router.push(`/dashboard/prompts/${registry.id}`)}
                  >
                    <Eye className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    title="Edit registry"
                    className="h-8 w-8 text-slate-400 hover:bg-slate-800 hover:text-white"
                    onClick={() =>
                      setEditDraft({
                        open: true,
                        id: registry.id,
                        name: registry.name,
                        description: registry.description ?? "",
                      })
                    }
                  >
                    <Pencil className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    title="Delete registry"
                    className="h-8 w-8 text-slate-400 hover:bg-slate-800 hover:text-rose-400"
                    disabled={removeRegistry.isPending}
                    onClick={() => confirmDelete(registry)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <Dialog
        open={createDraft.open}
        onOpenChange={(open) => setCreateDraft((d) => ({ ...d, open }))}
      >
        <DialogContent className="max-w-2xl border-slate-800 bg-slate-900 text-white">
          <DialogHeader>
            <DialogTitle>New prompt registry</DialogTitle>
            <DialogDescription className="text-slate-400">
              A registry starts with an initial version (v1).
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="registry-name" className="text-slate-300">
                Name
              </Label>
              <Input
                id="registry-name"
                placeholder="Customer support QA"
                className="border-slate-800 bg-slate-950 text-white placeholder-slate-500"
                value={createDraft.name}
                onChange={(e) =>
                  setCreateDraft((d) => ({ ...d, name: e.target.value }))
                }
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="registry-description" className="text-slate-300">
                Description (optional)
              </Label>
              <Input
                id="registry-description"
                placeholder="What this prompt is used for"
                className="border-slate-800 bg-slate-950 text-white placeholder-slate-500"
                value={createDraft.description}
                onChange={(e) =>
                  setCreateDraft((d) => ({ ...d, description: e.target.value }))
                }
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="registry-content" className="text-slate-300">
                Initial prompt content
              </Label>
              <Textarea
                id="registry-content"
                placeholder="Enter the initial prompt content..."
                className="min-h-[200px] resize-none border-slate-800 bg-slate-950 font-mono text-sm text-white placeholder-slate-500"
                value={createDraft.content}
                onChange={(e) =>
                  setCreateDraft((d) => ({ ...d, content: e.target.value }))
                }
              />
            </div>
          </div>

          <DialogFooter className="gap-2">
            <Button
              variant="outline"
              className="border-slate-700 bg-transparent text-slate-300 hover:bg-slate-800 hover:text-white"
              onClick={() =>
                setCreateDraft({ open: false, name: "", description: "", content: "" })
              }
            >
              Cancel
            </Button>
            <Button
              className="bg-lime-500 font-semibold text-slate-950 hover:bg-lime-400"
              onClick={() =>
                createRegistry.mutate({
                  name: createDraft.name,
                  description: createDraft.description,
                  initial_content: createDraft.content,
                })
              }
              disabled={
                createRegistry.isPending ||
                !createDraft.name.trim() ||
                !createDraft.content.trim()
              }
            >
              {createRegistry.isPending ? "Creating..." : "Create registry"}
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
              <Label htmlFor="edit-registry-name" className="text-slate-300">
                Name
              </Label>
              <Input
                id="edit-registry-name"
                className="border-slate-800 bg-slate-950 text-white placeholder-slate-500"
                value={editDraft.name}
                onChange={(e) =>
                  setEditDraft((d) => ({ ...d, name: e.target.value }))
                }
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-registry-description" className="text-slate-300">
                Description
              </Label>
              <Textarea
                id="edit-registry-description"
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
              onClick={() =>
                setEditDraft({ open: false, id: null, name: "", description: "" })
              }
            >
              Cancel
            </Button>
            <Button
              className="bg-indigo-500 font-semibold text-white hover:bg-indigo-400"
              onClick={() => {
                if (editDraft.id === null) return;
                editRegistry.mutate({
                  id: editDraft.id,
                  name: editDraft.name,
                  description: editDraft.description,
                });
              }}
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
