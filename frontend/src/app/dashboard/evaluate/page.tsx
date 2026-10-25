"use client";

import React, { useEffect, useState } from "react";
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
} from "lucide-react";
import { toast } from "sonner";
import Loader from "@/components/Loader";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getDatasets } from "@/api/datasets";
import { Dataset } from "@/types";
import { createRun } from "@/api/run";

const availableModels = [
  {
    id: "gemini-3.5-flash-lite",
    name: "Gemini 3.5 Flash Lite (Recommended)",
    provider: "Google",
  },
  { id: "gemini-1.5-pro", name: "Gemini 1.5 Pro", provider: "Google" },
  { id: "gpt-4o", name: "GPT-4o", provider: "OpenAI" },
  { id: "claude-3-5-sonnet", name: "Claude 3.5 Sonnet", provider: "Anthropic" },
];

export default function EvaluatePage() {
  const [datasetSearch, setDatasetSearch] = useState("");
  const { data: datasets, isLoading } = useQuery({
    queryKey: ["datasets"],
    queryFn: () => getDatasets(datasetSearch),
  });
  const [selectedDataset, setSelectedDataset] = useState(
    datasets ? datasets[0].id : "",
  );

  const queryClient = useQueryClient();
  const [isDatasetOpen, setIsDatasetOpen] = useState(false);
  const [modelName, setModelName] = useState("gemini-3.5-flash-lite");
  const [judgemodelName, setJudgeModelName] = useState("gemini-3.5-flash-lite");
  const [systemPrompt, setSystemPrompt] = useState(
    "You are an expert AI judge evaluating responses based on accuracy, helpfulness, and tone.",
  );

  const currentDatasetObj = datasets
    ? datasets.find((d: Dataset) => d.id === selectedDataset) || datasets[0]
    : "";

  useEffect(() => {
    if (datasets) {
      setSelectedDataset(datasets[0].id);
    }
  }, [datasets]);
  const { mutate: runEvaluation, isPending } = useMutation({
    mutationKey: ["runEvaluation"],
    mutationFn: () =>
      createRun({
        dataset_id: selectedDataset,
        model: modelName,
        system_prompt: systemPrompt,
        judge_model: judgemodelName,
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

  if (isPending) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-6">
        <Loader />
        <div className="text-center space-y-2">
          <h2 className="text-xl font-bold text-white">
            Running Evaluation...
          </h2>
          <p className="text-sm text-slate-400">
            Evaluating prompts against {modelName}
          </p>
        </div>
      </div>
    );
  }

  return isLoading ? (
    <Loader />
  ) : (
    <div className="space-y-6 animate-in fade-in-50 duration-500 max-w-4xl mx-auto">
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center gap-3">
          <PlayCircle className="h-8 w-8 text-lime-500" /> New Evaluation Run
        </h1>
        <p className="text-slate-400 mt-1">
          Configure dataset, model, and judge prompts to execute a new
          evaluation.
        </p>
      </div>

      <Card className="bg-slate-900/80 border-slate-800/30 backdrop-blur-xl shadow-2xl rounded-2xl overflow-hidden">
        <CardHeader className="border-b border-slate-800/30 px-6 py-5">
          <CardTitle className="text-lg font-semibold text-white flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-indigo-400" /> Evaluation
            Configuration
          </CardTitle>
          <CardDescription className="text-slate-400">
            Select inputs and parameters for your LLM benchmark run.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-6 space-y-6">
          <div className="space-y-2 relative">
            <Label className="text-slate-300 font-medium">Select Dataset</Label>
            <div
              onClick={() => setIsDatasetOpen(!isDatasetOpen)}
              className="w-full px-4 py-3 bg-slate-950/60 border border-slate-800/60 rounded-xl text-white text-sm flex items-center justify-between cursor-pointer hover:border-slate-700 transition-all"
            >
              <div className="flex items-center gap-3">
                <Database className="h-4 w-4 text-indigo-400" />
                <span className="font-medium">
                  {currentDatasetObj.name} ({currentDatasetObj.item_count}{" "}
                  items)
                </span>
              </div>
              <ChevronDown
                className={`h-4 w-4 text-slate-400 transition-transform ${isDatasetOpen ? "rotate-180" : ""}`}
              />
            </div>

            {isDatasetOpen && (
              <div className="absolute top-full left-0 right-0 mt-2 z-50 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl p-3 space-y-3 animate-in fade-in-50">
                <div className="relative">
                  <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <Input
                    value={datasetSearch}
                    onChange={(e) => setDatasetSearch(e.target.value)}
                    placeholder="Search datasets..."
                    className="pl-10 bg-slate-950 border-slate-800 text-white text-xs h-9"
                    autoFocus
                  />
                </div>
                <div className="max-h-60 overflow-y-auto space-y-1 pr-1">
                  {datasets.map((ds: Dataset) => (
                    <div
                      key={ds.id}
                      onClick={() => {
                        setSelectedDataset(ds.id);
                        setIsDatasetOpen(false);
                        setDatasetSearch("");
                      }}
                      className={`px-3 py-2.5 rounded-lg text-sm cursor-pointer flex items-center justify-between transition-all ${
                        selectedDataset === ds.id
                          ? "bg-indigo-950/60 text-indigo-300 font-semibold"
                          : "text-slate-300 hover:bg-slate-800/60 hover:text-white"
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <Database className="h-4 w-4 text-indigo-400" />
                        <span>{ds.name}</span>
                        <span className="text-xs text-slate-500">
                          ({ds.item_count} items)
                        </span>
                      </div>
                      {selectedDataset === ds.id && (
                        <Check className="h-4 w-4 text-lime-400" />
                      )}
                    </div>
                  ))}
                  {datasets.length === 0 && (
                    <p className="text-xs text-slate-500 text-center py-4">
                      No matching datasets found.
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>

          <div className="space-y-2">
            <Label className="text-slate-300 font-medium">
              Target LLM Model
            </Label>
            <div className="relative">
              <Cpu className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 z-10 pointer-events-none" />
              <select
                value={modelName}
                onChange={(e) => setModelName(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-slate-950/60 border border-slate-800/60 rounded-xl text-white text-sm focus:outline-none focus:border-indigo-500 cursor-pointer"
              >
                {availableModels.map((m) => (
                  <option
                    key={m.id}
                    value={m.id}
                    className="bg-slate-900 text-white"
                  >
                    {m.name} ({m.provider})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="space-y-2">
            <Label className="text-slate-300 font-medium">
              Target LLM Judge Model
            </Label>
            <div className="relative">
              <Cpu className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 z-10 pointer-events-none" />
              <select
                value={judgemodelName}
                onChange={(e) => setJudgeModelName(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-slate-950/60 border border-slate-800/60 rounded-xl text-white text-sm focus:outline-none focus:border-indigo-500 cursor-pointer"
              >
                {availableModels.map((m) => (
                  <option
                    key={m.id}
                    value={m.id}
                    className="bg-slate-900 text-white"
                  >
                    {m.name} ({m.provider})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="space-y-2">
            <Label className="text-slate-300 font-medium">
              AI Judge System Prompt
            </Label>
            <Textarea
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              className="bg-slate-950/60 border-slate-800/60 text-white min-h-[120px]"
              placeholder="Enter judge rubric instructions..."
            />
          </div>

          <div className="pt-4 flex justify-end">
            <Button
              onClick={() => runEvaluation()}
              className="gap-2 bg-lime-500 hover:bg-lime-400 text-slate-950 font-bold px-6 py-2.5 shadow-lg shadow-lime-500/20 cursor-pointer transition-all"
            >
              <PlayCircle className="h-5 w-5" /> Start Evaluation Run
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
