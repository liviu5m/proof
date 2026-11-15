"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Plus, Trash2, ShieldCheck, Key } from "lucide-react";
import Swal from "sweetalert2";
import { toast } from "sonner";
import Loader from "@/components/Loader";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  getProviderCredentials,
  upsertProviderCredential,
  deleteProviderCredential,
} from "@/api/provider-credentials";
import { ProviderCredential } from "@/types";

const PROVIDERS = [
  { value: "google", label: "Google" },
  { value: "openai", label: "OpenAI" },
  { value: "anthropic", label: "Anthropic" },
  { value: "ollama", label: "Ollama (Local)" },
];

export default function SettingsPage() {
  const [isOpen, setIsOpen] = useState(false);
  const [formProvider, setFormProvider] = useState("");
  const [formApiKey, setFormApiKey] = useState("");
  const [formBaseUrl, setFormBaseUrl] = useState("");

  const {
    data: credentials,
    isLoading,
    refetch,
  } = useQuery({
    queryKey: ["provider-credentials"],
    queryFn: () => getProviderCredentials(),
  });

  const upsertMutation = useMutation({
    mutationFn: upsertProviderCredential,
    onSuccess: () => {
      toast.success("API key saved successfully");
      refetch();
      setIsOpen(false);
      setFormProvider("");
      setFormApiKey("");
      setFormBaseUrl("");
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.error || "Failed to save API key");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteProviderCredential,
    onSuccess: () => {
      toast.success("API key removed");
      refetch();
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.error || "Failed to remove API key");
    },
  });

  if (isLoading) return <Loader />;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    upsertMutation.mutate({
      provider: formProvider,
      api_key: formApiKey,
      base_url: formBaseUrl || undefined,
    });
  };

  const handleDelete = async (id: number) => {
    const result = await Swal.fire({
      title: "Are you sure?",
      text: "Delete this API key? This cannot be undone.",
      icon: "warning",
      showCancelButton: true,
      confirmButtonColor: "#ef4444",
      cancelButtonColor: "#334155",
      confirmButtonText: "Yes, delete it!",
      background: "#0f172a",
      color: "#f8fafc",
    });
    if (result.isConfirmed) {
      deleteMutation.mutate(id);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in-50 duration-500">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center gap-3">
            <ShieldCheck className="h-8 w-8 text-lime-500" /> Provider Settings
          </h1>
          <p className="text-slate-400 mt-1">
            Manage your API keys for different LLM providers. Keys are encrypted
            and stored securely.
          </p>
        </div>
        <Button
          onClick={() => {
            setIsOpen(true);
            setFormProvider("");
            setFormApiKey("");
            setFormBaseUrl("");
          }}
          className="gap-2 bg-lime-500 hover:bg-lime-400 text-slate-950 font-semibold shadow-lg shadow-lime-500/20 cursor-pointer transition-all"
        >
          <Plus className="h-4 w-4" /> Add API Key
        </Button>
      </div>

      <Card className="bg-slate-900/80 border-slate-800/30 backdrop-blur-xl shadow-2xl rounded-2xl overflow-hidden">
        <CardHeader className="border-b border-slate-800/30 px-6 py-4">
          <CardTitle className="text-base font-semibold text-white flex items-center gap-2">
            <Key className="h-4 w-4" /> Stored Provider Credentials
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          {!credentials || credentials.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 px-4 text-center space-y-4">
              <div className="bg-slate-800/50 p-4 rounded-full text-slate-400">
                <Key className="h-8 w-8" />
              </div>
              <h3 className="text-lg font-semibold text-white">
                No API keys stored
              </h3>
              <p className="text-sm text-slate-400 max-w-sm">
                Add an API key for a provider to use it in evaluation runs.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {credentials.map((cred: ProviderCredential) => (
                <div
                  key={cred.id}
                  className="flex items-center justify-between p-4 rounded-xl bg-slate-950/60 border border-slate-800/60"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-slate-800/50">
                      <Key className="h-4 w-4 text-slate-300" />
                    </div>
                    <div>
                      <p className="font-medium text-white">{cred.provider}</p>
                      <p className="text-xs text-slate-500">
                        {cred.base_url || "Default endpoint"}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-mono text-slate-400">
                      ••••••••
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(cred.id)}
                      className="text-slate-400 hover:text-red-400 hover:bg-red-500/10"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm animate-in fade-in-0 duration-200">
          <div className="absolute top-4 left-1/2 -translate-x-1/2 z-50" />
          <Card className="w-full max-w-md mx-4 bg-slate-900 border-slate-800 shadow-2xl rounded-2xl overflow-hidden">
            <CardHeader className="border-b border-slate-800/30 px-6 py-4">
              <CardTitle className="text-base font-semibold text-white">
                Add API Key
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6 space-y-4">
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label>Provider</Label>
                  <select
                    value={formProvider}
                    onChange={(e) => setFormProvider(e.target.value)}
                    className="w-full pl-3 pr-4 py-2.5 bg-slate-950/60 border border-slate-800 rounded-xl text-white text-sm focus:outline-none focus:border-indigo-500 cursor-pointer"
                  >
                    <option value="">Select provider</option>
                    {PROVIDERS.map((p) => (
                      <option key={p.value} value={p.value}>
                        {p.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-2">
                  <Label>API Key</Label>
                  <Input
                    type="password"
                    placeholder="sk-... or your provider API key"
                    value={formApiKey}
                    onChange={(e) => setFormApiKey(e.target.value)}
                    className="bg-slate-950/60 border border-slate-800 text-white"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Base URL (optional)</Label>
                  <Input
                    placeholder="e.g. http://localhost:11434 for Ollama"
                    value={formBaseUrl}
                    onChange={(e) => setFormBaseUrl(e.target.value)}
                    className="bg-slate-950/60 border border-slate-800 text-white"
                  />
                </div>

                <div className="pt-4 flex justify-end gap-2">
                  <Button
                    type="button"
                    onClick={() => setIsOpen(false)}
                    className="bg-slate-800 hover:bg-slate-700 text-slate-200 cursor-pointer"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    disabled={
                      upsertMutation.isPending || !formProvider || !formApiKey
                    }
                    className="gap-2 bg-lime-500 hover:bg-lime-400 text-slate-950 font-semibold shadow-lg shadow-lime-500/20 cursor-pointer transition-all"
                  >
                    {upsertMutation.isPending ? "Saving..." : "Save Key"}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
