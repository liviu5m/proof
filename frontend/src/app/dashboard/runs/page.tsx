"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import {
  LayoutDashboard,
  Eye,
  ArrowUpRight,
  CheckCircle2,
  PlayCircle,
  DollarSign,
} from "lucide-react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { getRuns, getRunCost } from "@/api/run";
import { PromptVersionSummary, Result, Run, TokenUsage } from "@/types";
import Loader from "@/components/Loader";
import { format, parseISO } from "date-fns";
import { toast } from "sonner";

function PromptVersionBadge({
  version,
}: {
  version?: PromptVersionSummary | null;
}) {
  if (!version) {
    return <span className="text-xs text-slate-500">Manual</span>;
  }

  return (
    <Link
      href={`/dashboard/prompts/${version.registry_id}`}
      title={`Prompt ${version.content_hash}${version.deleted ? " (deleted version)" : ""}`}
      className="inline-flex items-center gap-1.5 rounded-md border border-slate-700 bg-slate-800/60 px-2 py-0.5 font-mono text-xs text-slate-300 transition-colors hover:border-indigo-500/40 hover:text-white"
    >
      v{version.version_number ?? "?"}
      <span className="text-slate-500">
        {version.content_hash.slice(0, 8)}
      </span>
      {version.deleted && <span className="text-rose-400">deleted</span>}
    </Link>
  );
}

async function fetchAllCosts(
  runIds: number[],
): Promise<Record<number, TokenUsage>> {
  const costs: Record<number, TokenUsage> = {};
  await Promise.all(
    runIds.map(async (id) => {
      try {
        costs[id] = await getRunCost(id);
      } catch {
        costs[id] = null as any;
      }
    }),
  );
  return costs;
}

export default function RunsPage() {
  const [selectedRun, setSelectedRun] = useState<Run | null>(null);

  const {
    data: runs,
    isLoading,
    error: runsError,
  } = useQuery({
    queryKey: ["runs"],
    queryFn: () => getRuns(),
  });

  // Fetch costs for all runs
  const { data: costsMap } = useQuery({
    queryKey: ["run-costs", runs?.map((r: Run) => r.id)],
    queryFn: () => fetchAllCosts(runs?.map((r: Run) => r.id) || []),
    enabled: !!runs && runs.length > 0,
  });

  if (runsError) {
    toast.error(
      (runsError as any)?.response?.data?.error || "Failed to load runs",
    );
  }

  if (isLoading) {
    return <Loader />;
  }

  if (!runs || runs.length === 0) {
    return (
      <div className="space-y-6 animate-in fade-in-50 duration-500">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center gap-3">
              <LayoutDashboard className="h-8 w-8 text-lime-500" /> Evaluation
              Runs
            </h1>
            <p className="text-slate-400 mt-1">
              Review history, scores, and detailed item evaluations for all
              benchmark runs.
            </p>
          </div>
          <Link href="/dashboard/evaluate">
            <Button className="gap-2 bg-lime-500 hover:bg-lime-400 text-slate-950 font-semibold shadow-lg shadow-lime-500/20 cursor-pointer transition-all">
              <ArrowUpRight className="h-4 w-4" /> New Run
            </Button>
          </Link>
        </div>
        <Card className="bg-slate-900/80 border-slate-800/30 backdrop-blur-xl shadow-2xl rounded-2xl overflow-hidden">
          <CardContent className="flex flex-col items-center justify-center py-16 px-4 text-center space-y-4">
            <div className="bg-slate-800/50 p-4 rounded-full text-slate-400">
              <LayoutDashboard className="h-8 w-8" />
            </div>
            <h3 className="text-lg font-semibold text-white">
              No runs created
            </h3>
            <p className="text-sm text-slate-400 max-w-sm">
              You haven't executed any evaluation runs yet. Run your first
              benchmark to track performance.
            </p>
            <Button
              asChild
              className="gap-2 bg-lime-500 hover:bg-lime-400 text-slate-950 font-semibold cursor-pointer"
            >
              <Link href="/dashboard/evaluate">
                <PlayCircle className="h-4 w-4" /> Go to Evaluation
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in-50 duration-500">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center gap-3">
            <LayoutDashboard className="h-8 w-8 text-lime-500" /> Evaluation
            Runs
          </h1>
          <p className="text-slate-400 mt-1">
            Review history, scores, and detailed item evaluations for all
            benchmark runs.
          </p>
        </div>
        <Link href="/dashboard/evaluate">
          <Button className="gap-2 bg-lime-500 hover:bg-lime-400 text-slate-950 font-semibold shadow-lg shadow-lime-500/20 cursor-pointer transition-all">
            <ArrowUpRight className="h-4 w-4" /> New Run
          </Button>
        </Link>
      </div>

      <Card className="bg-slate-900/80 border-slate-800/30 backdrop-blur-xl shadow-2xl rounded-2xl overflow-hidden">
        <CardHeader className="px-6 py-5 border-b border-slate-800/30">
          <CardTitle className="text-lg font-semibold text-white">
            Past Runs ({runs.length})
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader className="bg-slate-950/40">
                <TableRow className="border-slate-800/30 hover:bg-transparent">
                  <TableHead className="text-xs font-semibold text-slate-400 uppercase tracking-wider pl-6">
                    Run ID
                  </TableHead>
                  <TableHead className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Dataset
                  </TableHead>
                  <TableHead className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Prompt
                  </TableHead>
                  <TableHead className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Model
                  </TableHead>
                  <TableHead className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Score (1-5)
                  </TableHead>
                  <TableHead className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Cost
                  </TableHead>
                  <TableHead className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Status
                  </TableHead>
                  <TableHead className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Created
                  </TableHead>
                  <TableHead className="text-right text-xs font-semibold text-slate-400 uppercase tracking-wider pr-6">
                    Actions
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {runs.map((run: Run) => {
                  const cost = costsMap?.[run.id];
                  return (
                    <TableRow
                      key={run.id}
                      className="border-slate-800/20 hover:bg-slate-800/40 transition-colors"
                    >
                      <TableCell className="font-mono text-sm text-slate-300 pl-6">
                        {run.id}
                      </TableCell>
                      <TableCell className="font-medium text-white">
                        {run.datasetName}
                      </TableCell>
                      <TableCell>
                        <PromptVersionBadge version={run.prompt_version} />
                      </TableCell>
                      <TableCell className="font-mono text-xs text-indigo-400">
                        {run.model}
                      </TableCell>
                      <TableCell>
                        <Badge className="bg-lime-500/10 text-lime-400 border-lime-500/20 font-bold">
                          ★{" "}
                          {run.avg_score != null
                            ? Number(run.avg_score).toFixed(1)
                            : "N/A"}{" "}
                          / 5.0
                        </Badge>
                      </TableCell>
                      <TableCell className="font-mono text-xs">
                        {!cost ? (
                          <span className="text-slate-500">—</span>
                        ) : cost.cost_usd === null ? (
                          <span className="text-slate-500">n/a</span>
                        ) : (
                          <span className="flex items-center gap-1 text-lime-400">
                            <DollarSign className="h-3 w-3" />$
                            {cost.cost_usd.toFixed(4)}
                            <span className="text-[10px] text-slate-500">
                              ({cost.pricing})
                            </span>
                          </span>
                        )}
                      </TableCell>
                      <TableCell>
                        {run.status === "Completed" ? (
                          <span className="inline-flex items-center gap-1.5 text-xs font-medium text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/20">
                            <CheckCircle2 className="h-3.5 w-3.5" /> Completed
                          </span>
                        ) : run.status === "Running" ||
                          run.status === "Pending" ? (
                          <span className="inline-flex items-center gap-1.5 text-xs font-medium text-amber-400 bg-amber-500/10 px-2.5 py-1 rounded-full border border-amber-500/20 animate-pulse">
                            ⏳ {run.status}
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1.5 text-xs font-medium text-red-400 bg-red-500/10 px-2.5 py-1 rounded-full border border-red-500/20">
                            ❌ {run.status || "Failed"}
                          </span>
                        )}
                      </TableCell>
                      <TableCell className="text-sm text-slate-400">
                        {run.created_at
                          ? format(
                              parseISO(run.created_at),
                              "MMM d, yyyy h:mm a",
                            )
                          : ""}
                      </TableCell>
                      <TableCell className="text-right pr-6">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => setSelectedRun(run)}
                          className="h-8 w-8 text-slate-400 hover:text-white hover:bg-slate-800 cursor-pointer"
                          title="View Results"
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {selectedRun && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm animate-in fade-in-0 duration-200">
          <Card className="w-full max-w-2xl mx-4 bg-slate-900 border-slate-800 shadow-2xl max-h-[85vh] flex flex-col">
            <CardHeader className="border-b border-slate-800">
              <CardTitle className="text-xl font-semibold text-white">
                Run Results: {selectedRun.id} ({selectedRun.datasetName})
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6 overflow-y-auto space-y-4 flex-1">
              {(() => {
                const cost = costsMap?.[selectedRun.id];
                return (
                  <div className="grid grid-cols-2 gap-4 text-sm bg-slate-950/60 p-4 rounded-xl border border-slate-800/60">
                    <div>
                      <span className="text-slate-400 block">Model:</span>
                      <span className="font-mono text-indigo-400">
                        {selectedRun.model}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">
                        Average Score:
                      </span>
                      <span className="font-bold text-lime-400">
                        {selectedRun.avg_score != null
                          ? Number(selectedRun.avg_score).toFixed(1)
                          : "N/A"}{" "}
                        / 5.0
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Prompt version:</span>
                      <PromptVersionBadge version={selectedRun.prompt_version} />
                    </div>
                    <div>
                      <span className="text-slate-400 block">Cost:</span>
                      {!cost ? (
                        <span className="text-slate-500">—</span>
                      ) : cost.cost_usd === null ? (
                        <span className="text-slate-500">n/a</span>
                      ) : (
                        <span className="flex items-center gap-1 text-lime-400">
                          <DollarSign className="h-3 w-3" />$
                          {cost.cost_usd.toFixed(4)}
                          <span className="text-[10px] text-slate-500">
                            ({cost.pricing})
                          </span>
                        </span>
                      )}
                    </div>
                    <div>
                      <span className="text-slate-400 block">Tokens:</span>
                      {!cost ? (
                        <span className="text-slate-500">—</span>
                      ) : (
                        <span className="font-mono text-slate-300">
                          {cost.prompt_tokens + cost.completion_tokens} total
                          <span className="text-slate-500">
                            {" "}
                            ({cost.prompt_tokens} in / {cost.completion_tokens}{" "}
                            out)
                          </span>
                        </span>
                      )}
                    </div>
                  </div>
                );
              })()}

              <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider pt-2">
                Evaluated Items
              </h3>
              <div className="space-y-3">
                {(selectedRun.results ?? []).map((res: Result) => (
                  <div
                    key={res.id}
                    className="p-4 rounded-xl bg-slate-950/40 border border-slate-800 space-y-2"
                  >
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-mono text-indigo-400">
                        Prompt #{res.id}
                      </span>
                      <Badge className="bg-lime-500/10 text-lime-400 border-lime-500/20 font-bold">
                        Score: {Number(res.score).toFixed(1)}
                      </Badge>
                    </div>
                    <p className="text-sm font-medium text-white">
                      Q: {res.question}
                    </p>
                    <p className="text-xs text-slate-300 bg-slate-900 p-2.5 rounded-lg border border-slate-800/80">
                      A: {res.response}
                    </p>
                    <p className="text-xs text-slate-400 italic">
                      Judge: {res.reason}
                    </p>
                  </div>
                ))}
              </div>

              <div className="pt-4 flex justify-end">
                <Button
                  onClick={() => setSelectedRun(null)}
                  className="bg-slate-800 hover:bg-slate-700 text-slate-200 cursor-pointer"
                >
                  Close
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
