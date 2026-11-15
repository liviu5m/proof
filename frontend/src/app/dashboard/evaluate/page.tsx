"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  PlayCircle,
  Cpu,
  Database,
  Sparkles,
  Check,
  ChevronDown,
  Search,
  Upload,
  Filter,
  RefreshCw,
  Galaxy,
  Zap,
  Wand2,
} from "lucide-react";
import { toast } from "sonner";
import Loader from "@/components/Loader";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getDatasets } from "@/api/datasets";
import { Dataset } from "@/types";
import { createRun } from "@/api/run";
import { getModels, syncModels } from "@/api/models";
import { ModelCatalogItem } from "@/api/models";

const PROVIDER_OPTIONS = [
  { value: "google", label: "Google", color: "text-indigo-400", bg: "bg-indigo-500/10" },
  { value: "openai", label: "OpenAI", color: "text-slate-300", bg: "bg-slate-500/10" },
  { value: "anthropic", label: "Anthropic", color: "text-indigo-300", bg: "bg-indigo-500/10" },
  { value: "ollama", label: "Ollama", color: "text-emerald-400", bg: "bg-emerald-500/10" },
];

export default function EvaluatePage() {
  const [datasetSearch, setDatasetSearch] = useState("");
  const [selectedDataset, setSelectedDataset] = useState<number>(0);
  const queryClient = useQueryClient();
  const [modelName, setModelName] = useState("gemini-3.5-flash-lite");
  const [judgemodelName, setJudgeModelName] = useState("gemini-3.5-flash-lite");
  const [providerName, setProviderName] = useState("google");
  const [judgeProviderName, setJudgeProviderName] = useState("google");
  const [ollamaBaseUrl, setOllamaBaseUrl] = useState("http://localhost:11434");
  const [ollamaBaseUrlJudge, setOllamaBaseUrlJudge] = useState("http://localhost:11434");
  const [modelSearch, setModelSearch] = useState("");
  const [judgeModelSearch, setJudgeModelSearch] = useState("");
  const [systemPrompt, setSystemPrompt] = useState(
    "You are an expert AI judge evaluating responses based on accuracy, helpfulness, and tone.",
  );
  const [judgeSystemPrompt, setJudgeSystemPrompt] = useState(
    "You are an expert AI judge evaluating responses based on accuracy, helpfulness, and tone.",
  );

  const { data: datasets, isLoading: datasetsLoading, error: datasetsError } = useQuery({
    queryKey: ["datasets", datasetSearch],
    queryFn: () => getDatasets(datasetSearch),
  });

  const { data: allModels = [], isLoading: modelsLoading, refetch: refetchModels } = useQuery({
    queryKey: ["models"],
    queryFn: () => getModels(),
  });

  const syncMutation = useMutation({
    mutationFn: syncModels,
    onSuccess: (data) => {
      if (data.errors && data.errors.length > 0) {
        const errorMsg = data.errors
          .map((e: any) => Object.entries(e).map(([k, v]) => `${k}: ${v}`).join(", "))
          .join("; ");
        toast.warning(`Models synced (${data.count}). Some providers failed: ${errorMsg}`);
      } else {
        toast.success(`Models synced successfully (${data.count} models)`);
      }
      refetchModels();
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.error || "Failed to sync models");
    },
  });

  const filteredRunnerModels = allModels.filter((m: ModelCatalogItem) => {
    const matchesProvider = m.provider === providerName;
    const matchesSearch =
      m.name.toLowerCase().includes(modelSearch.toLowerCase()) ||
      m.id.toLowerCase().includes(modelSearch.toLowerCase());
    return matchesProvider && matchesSearch;
  });

  const filteredJudgeModels = allModels.filter((m: ModelCatalogItem) => {
    const matchesProvider = m.provider === judgeProviderName;
    const matchesSearch =
      m.name.toLowerCase().includes(judgeModelSearch.toLowerCase()) ||
      m.id.toLowerCase().includes(judgeModelSearch.toLowerCase());
    return matchesProvider && matchesSearch;
  });

  useEffect(() => {
    if (datasets && datasets.length > 0 && (!selectedDataset || !datasets.some((d: Dataset) => d.id === selectedDataset))) {
      setSelectedDataset(datasets[0].id);
    }
  }, [datasets, selectedDataset]);

  const { mutate: runEvaluation, isPending } = useMutation({
    mutationKey: ["runEvaluation"],
    mutationFn: () =>
      createRun({
        dataset_id: selectedDataset,
        model: modelName,
        system_prompt: systemPrompt,
        judge_model: judgemodelName,
        provider: providerName,
        judge_provider: judgeProviderName,
        ollama_base_url: providerName === "ollama" ? ollamaBaseUrl : undefined,
        ollama_base_url_judge: judgeProviderName === "ollama" ? ollamaBaseUrlJudge : undefined,
      }),
    onSuccess: (data) => {
      console.log(data);
      toast.success("Evaluation run started successfully!");
      queryClient.invalidateQueries({ queryKey: ["runs"] });
    },
    onError: (error: any) => {
      toast.error(
        error?.response?.data?.error || "Failed to start evaluation run",
      );
    },
  });

  return (
    <div className="space-y-6 animate-in fade-in-50 duration-500 max-w-5xl mx-auto">
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center gap-3">
          <Zap className="h-8 w-8 text-lime-500" /> Model Configuration
        </h1>
        <p className="text-slate-400 mt-1">
          Choose runner and judge models. Each can use a different provider.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Runner Model Card */}
        <Card className="bg-slate-900/80 border-slate-800/30 backdrop-blur-xl shadow-2xl rounded-2xl overflow-hidden">
          <CardHeader className="border-b border-slate-800/30 px-6 py-4">
            <CardTitle className="text-base font-semibold text-white flex items-center gap-2">
              <Cpu className="h-4 w-4 text-indigo-400" /> Runner Model
            </CardTitle>
            <CardDescription className="text-slate-500 text-sm">
              Model that generates answers
            </CardDescription>
          </CardHeader>
          <CardContent className="p-6 space-y-5">
            <div className="space-y-2">
              <Label className="text-slate-300 font-medium">Provider</Label>
              <div className="relative">
                <select
                  value={providerName}
                  onChange={(e) => setProviderName(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-950/60 border border-slate-800/60 rounded-xl text-white text-sm focus:outline-none focus:border-indigo-500 cursor-pointer"
                >
                  {PROVIDER_OPTIONS.map((p) => (
                    <option key={p.value} value={p.value} className={p.bg}>
                      {p.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {providerName === "ollama" && (
              <div className="space-y-2">
                <Label className="text-slate-300 font-medium">Ollama Base URL</Label>
                <div className="relative">
                  <Galaxy className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <Input
                    placeholder="http://localhost:11434"
                    value={ollamaBaseUrl}
                    onChange={(e) => setOllamaBaseUrl(e.target.value)}
                    className="bg-slate-950/60 border border-slate-800 text-white text-sm h-10"
                  />
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  Your local Ollama instance URL
                </p>
              </div>
            )}

            <div className="relative">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                value={modelSearch}
                onChange={(e) => setModelSearch(e.target.value)}
                placeholder="Search models..."
                className="pl-10 bg-slate-950 border-slate-800 text-white text-sm h-10"
              />
            </div>
            <div className="relative">
              <Galaxy className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <select
                value={modelName}
                onChange={(e) => setModelName(e.target.value)}
                className="w-full pl-10 pr-4 py-3 bg-slate-950/60 border border-slate-800/60 rounded-xl text-white text-sm focus:outline-none focus:border-indigo-500 cursor-pointer"
              >
                {filteredRunnerModels.length === 0 ? (
                  <option disabled value="" className="text-slate-500">
                    No models found. Sync models first.
                  </option>
                ) : (
                  filteredRunnerModels.map((m: ModelCatalogItem) => (
                    <option key={m.id} value={m.id} className="bg-slate-900 text-white">
                      {m.name} ({m.provider})
                    </option>
                  ))
                )}
              </select>
            </div>
            {filteredRunnerModels.length > 0 && (
              <p className="text-xs text-slate-500">
                {filteredRunnerModels.length} model{filteredRunnerModels.length !== 1 ? "s" : ""} available
              </p>
            )}
          </CardContent>
        </Card>

        {/* Judge Model Card */}
        <Card className="bg-slate-900/80 border-slate-800/30 backdrop-blur-xl shadow-2xl rounded-2xl overflow-hidden">
          <CardHeader className="border-b border-slate-800/30 px-6 py-4">
            <CardTitle className="text-base font-semibold text-white flex items-center gap-2">
              <Wand2 className="h-4 w-4 text-purple-400" /> Judge Model
            </CardTitle>
            <CardDescription className="text-slate-500 text-sm">
              Model that evaluates answers
            </CardDescription>
          </CardHeader>
          <CardContent className="p-6 space-y-5">
            <div className="space-y-2">
              <Label className="text-slate-300 font-medium">Provider</Label>
              <div className="relative">
                <select
                  value={judgeProviderName}
                  onChange={(e) => setJudgeProviderName(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-950/60 border border-slate-800/60 rounded-xl text-white text-sm focus:outline-none focus:border-indigo-500 cursor-pointer"
                >
                  {PROVIDER_OPTIONS.map((p) => (
                    <option key={p.value} value={p.value} className={p.bg}>
                      {p.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {judgeProviderName === "ollama" && (
              <div className="space-y-2">
                <Label className="text-slate-300 font-medium">Ollama Base URL</Label>
                <div className="relative">
                  <Galaxy className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <Input
                    placeholder="http://localhost:11434"
                    value={ollamaBaseUrlJudge}
                    onChange={(e) => setOllamaBaseUrlJudge(e.target.value)}
                    className="bg-slate-950/60 border border-slate-800 text-white text-sm h-10"
                  />
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  Your local Ollama instance URL
                </p>
              </div>
            )}

            <div className="relative">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                value={judgeModelSearch}
                onChange={(e) => setJudgeModelSearch(e.target.value)}
                placeholder="Search models..."
                className="pl-10 bg-slate-950 border-slate-800 text-white text-sm h-10"
              />
            </div>
            <div className="relative">
              <Galaxy className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <select
                value={judgemodelName}
                onChange={(e) => setJudgeModelName(e.target.value)}
                className="w-full pl-10 pr-4 py-3 bg-slate-950/60 border border-slate-800/60 rounded-xl text-white text-sm focus:outline-none focus:border-indigo-500 cursor-pointer"
              >
                {filteredJudgeModels.length === 0 ? (
                  <option disabled value="" className="text-slate-500">
                    No models found. Sync models first.
                  </option>
                ) : (
                  filteredJudgeModels.map((m: ModelCatalogItem) => (
                    <option key={m.id} value={m.id} className="bg-slate-900 text-white">
                      {m.name} ({m.provider})
                    </option>
                  ))
                )}
              </select>
            </div>
            {filteredJudgeModels.length > 0 && (
              <p className="text-xs text-slate-500">
                {filteredJudgeModels.length} model{filteredJudgeModels.length !== 1 ? "s" : ""} available
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="bg-slate-900/80 border-slate-800/30 backdrop-blur-xl shadow-2xl rounded-2xl overflow-hidden">
        <CardHeader className="border-b border-slate-800/30 px-6 py-4">
          <CardTitle className="text-base font-semibold text-white flex items-center gap-2">
            <Database className="h-4 w-4 text-lime-400" /> Dataset & Prompt
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6 space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="space-y-2">
              <Label className="text-slate-300 font-medium">Dataset</Label>
              <div className="relative">
                <button
                  className="w-full flex items-center justify-between pl-3 pr-4 py-2.5 bg-slate-950/60 border border-slate-800 rounded-xl text-white text-sm hover:bg-slate-800/50 focus:outline-none focus:border-indigo-500"
                >
                  <span>
                    {selectedDataset > 0
                      ? datasets?.find((d: Dataset) => d.id === selectedDataset)?.name || "Select dataset"
                      : "Select dataset"}
                  </span>
                  <ChevronDown className="h-4 w-4 text-slate-400" />
                </button>
              </div>
            </div>

            <div className="space-y-2">
              <Label className="text-slate-300 font-medium">System Prompt</Label>
              <Textarea
                value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
                className="bg-slate-950/60 border border-slate-800 text-white min-h-[120px] resize-none"
                placeholder="Enter system prompt for runner..."
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label className="text-slate-300 font-medium">AI Judge System Prompt</Label>
            <Textarea
              value={judgeSystemPrompt}
              onChange={(e) => setJudgeSystemPrompt(e.target.value)}
              className="bg-slate-950/60 border border-slate-800 text-white min-h-[100px] resize-none"
              placeholder="Enter judge rubric instructions..."
            />
          </div>
        </CardContent>
      </Card>

      <div className="pt-4 flex justify-end">
        <Button
          onClick={() => runEvaluation()}
          disabled={isPending}
          className="gap-2 bg-lime-500 hover:bg-lime-400 text-slate-950 font-bold px-8 py-3 shadow-lg shadow-lime-500/20 cursor-pointer transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isPending ? (
            <>
              <RefreshCw className="h-5 w-5 animate-spin" /> Processing...
            </>
          ) : (
            <>
              <PlayCircle className="h-5 w-5" /> Start Evaluation Run
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
