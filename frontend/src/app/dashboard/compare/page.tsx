"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { GitCompare, Award, Search, ChevronDown, Check, PlayCircle } from "lucide-react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { getRuns } from "@/api/run";
import Loader from "@/components/Loader";
import { Run } from "@/types";

function SearchableSelect({
  value,
  onChange,
  allRuns,
}: {
  value: number | null;
  onChange: (id: number) => void;
  allRuns: Run[];
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState("");
  const dropdownRef = React.useRef<HTMLDivElement>(null);
  const inputRef = React.useRef<HTMLInputElement>(null);

  const { data: filteredRuns = [] } = useQuery({
    queryKey: ["runs", search],
    queryFn: () => getRuns(search),
  });

  const selectedRun = allRuns.find((r: Run) => r.id === value) || allRuns[0];

  React.useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  React.useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="bg-slate-950 border border-slate-800 rounded-lg text-xs text-white px-3 py-1.5 flex items-center gap-2 focus:outline-none focus:border-indigo-500 hover:border-slate-700 transition-colors"
      >
        <span>
          {selectedRun
            ? `${selectedRun.id} - ${selectedRun.model}`
            : "Select run..."}
        </span>
        <ChevronDown className="h-3 w-3 text-slate-400" />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-64 bg-slate-950 border border-slate-800 rounded-xl shadow-2xl z-50 overflow-hidden animate-in fade-in-50 zoom-in-95">
          <div className="p-2 border-b border-slate-800/80">
            <div className="relative flex items-center">
              <Search className="absolute left-2.5 h-3.5 w-3.5 text-slate-400" />
              <input
                ref={inputRef}
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search runs..."
                className="w-full bg-slate-900 border border-slate-800 rounded-lg text-xs text-white pl-8 pr-3 py-1.5 focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>
          <div className="max-h-60 overflow-y-auto p-1 space-y-1">
            {filteredRuns.length === 0 ? (
              <div className="px-3 py-2 text-xs text-slate-500 text-center">
                No runs found
              </div>
            ) : (
              filteredRuns.map((r: Run) => (
                <button
                  key={r.id}
                  type="button"
                  onClick={() => {
                    onChange(r.id);
                    setIsOpen(false);
                    setSearch("");
                  }}
                  className={`w-full text-left px-3 py-2 rounded-lg text-xs flex items-center justify-between transition-colors ${
                    r.id === value
                      ? "bg-indigo-600/20 text-indigo-300 font-medium border border-indigo-500/30"
                      : "text-slate-300 hover:bg-slate-900 hover:text-white"
                  }`}
                >
                  <div>
                    <div className="font-mono">{r.id}</div>
                    <div className="text-[10px] text-slate-400">
                      {r.model} {r.datasetName ? `(${r.datasetName})` : ""}
                    </div>
                  </div>
                  {r.id === value && (
                    <Check className="h-3.5 w-3.5 text-indigo-400" />
                  )}
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default function ComparePage() {
  const { data: runs, isLoading } = useQuery({
    queryKey: ["runs"],
    queryFn: () => getRuns(),
  });

  const [runA, setRunA] = useState<any>(null);
  const [runB, setRunB] = useState<any>(null);

  React.useEffect(() => {
    if (runs && runs.length > 0) {
      if (runA === null) setRunA(runs[0].id);
      if (runB === null) setRunB(runs.length > 1 ? runs[1].id : runs[0].id);
    }
  }, [runs, runA, runB]);

  if (isLoading) {
    return <Loader />;
  }

  if (!runs || runs.length === 0) {
    return (
      <div className="space-y-6 animate-in fade-in-50 duration-500">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center gap-3">
            <GitCompare className="h-8 w-8 text-lime-500" /> Compare Runs
          </h1>
          <p className="text-slate-400 mt-1">
            Side-by-side comparison of two evaluation runs to analyze score differences and prompt outputs.
          </p>
        </div>
        <Card className="bg-slate-900/80 border-slate-800/30 backdrop-blur-xl shadow-2xl rounded-2xl overflow-hidden">
          <CardContent className="flex flex-col items-center justify-center py-16 px-4 text-center space-y-4">
            <div className="bg-slate-800/50 p-4 rounded-full text-slate-400">
              <GitCompare className="h-8 w-8" />
            </div>
            <h3 className="text-lg font-semibold text-white">No runs available for comparison</h3>
            <p className="text-sm text-slate-400 max-w-sm">
              You need at least two completed evaluation runs to perform side-by-side comparisons.
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

  if (runs.length === 1) {
    return (
      <div className="space-y-6 animate-in fade-in-50 duration-500">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center gap-3">
            <GitCompare className="h-8 w-8 text-lime-500" /> Compare Runs
          </h1>
          <p className="text-slate-400 mt-1">
            Side-by-side comparison of two evaluation runs to analyze score differences and prompt outputs.
          </p>
        </div>
        <Card className="bg-slate-900/80 border-slate-800/30 backdrop-blur-xl shadow-2xl rounded-2xl overflow-hidden">
          <CardContent className="flex flex-col items-center justify-center py-16 px-4 text-center space-y-4">
            <div className="bg-slate-800/50 p-4 rounded-full text-slate-400">
              <GitCompare className="h-8 w-8" />
            </div>
            <h3 className="text-lg font-semibold text-white">Need one more run</h3>
            <p className="text-sm text-slate-400 max-w-sm">
              You have only 1 run ({runs[0].model}). Create a second evaluation run to compare results.
            </p>
            <Button
              asChild
              className="gap-2 bg-lime-500 hover:bg-lime-400 text-slate-950 font-semibold cursor-pointer"
            >
              <Link href="/dashboard/evaluate">
                <PlayCircle className="h-4 w-4" /> Create Another Run
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const selectedRunA = runs.find((r: Run) => r.id === runA) || runs[0];
  const selectedRunB = runs.find((r: Run) => r.id === runB) || (runs.length > 1 ? runs[1] : runs[0]);

  return (
    <div className="space-y-6 animate-in fade-in-50 duration-500">
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center gap-3">
          <GitCompare className="h-8 w-8 text-lime-500" /> Compare Runs
        </h1>
        <p className="text-slate-400 mt-1">
          Side-by-side comparison of two evaluation runs to analyze score differences and prompt outputs.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="bg-slate-900/80 border-slate-800/30 backdrop-blur-xl shadow-2xl rounded-2xl overflow-hidden">
          <CardHeader className="border-b border-slate-800/30 px-6 py-4 flex flex-row items-center justify-between">
            <CardTitle className="text-base font-semibold text-white">Run A ({selectedRunA.id})</CardTitle>
            <SearchableSelect value={runA} onChange={setRunA} allRuns={runs} />
          </CardHeader>
          <CardContent className="p-6 space-y-4">
            <div className="flex justify-between items-center bg-slate-950/60 p-4 rounded-xl border border-slate-800/60">
              <div>
                <p className="text-xs text-slate-400">Model</p>
                <p className="font-mono text-indigo-400 text-sm">{selectedRunA.model}</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-slate-400">Score</p>
                <p className="font-bold text-lime-400 text-lg">
                  ★ {selectedRunA.avg_score != null ? Number(selectedRunA.avg_score).toFixed(1) : "N/A"} / 5.0
                </p>
              </div>
            </div>

            <div className="space-y-3">
              {selectedRunA.results?.map((res: any, idx: number) => (
                <div key={idx} className="p-4 rounded-xl bg-slate-950/40 border border-slate-800 space-y-2">
                  <div className="flex justify-between items-center text-xs text-slate-400">
                    <span>Prompt #{res.id || idx + 1}</span>
                    <span className="text-lime-400 font-bold">Score: {res.score ?? "N/A"}</span>
                  </div>
                  <p className="text-xs text-white font-medium">{res.question || res.prompt}</p>
                  <p className="text-xs text-slate-300 bg-slate-900 p-2.5 rounded-lg border border-slate-800/80">{res.response}</p>
                  {res.reason && <p className="text-[11px] text-slate-400 italic">Judge: {res.reason}</p>}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-900/80 border-slate-800/30 backdrop-blur-xl shadow-2xl rounded-2xl overflow-hidden">
          <CardHeader className="border-b border-slate-800/30 px-6 py-4 flex flex-row items-center justify-between">
            <CardTitle className="text-base font-semibold text-white">Run B ({selectedRunB.id})</CardTitle>
            <SearchableSelect value={runB} onChange={setRunB} allRuns={runs} />
          </CardHeader>
          <CardContent className="p-6 space-y-4">
            <div className="flex justify-between items-center bg-slate-950/60 p-4 rounded-xl border border-slate-800/60">
              <div>
                <p className="text-xs text-slate-400">Model</p>
                <p className="font-mono text-indigo-400 text-sm">{selectedRunB.model}</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-slate-400">Score</p>
                <p className="font-bold text-lime-400 text-lg">
                  ★ {selectedRunB.avg_score != null ? Number(selectedRunB.avg_score).toFixed(1) : "N/A"} / 5.0
                </p>
              </div>
            </div>

            <div className="space-y-3">
              {selectedRunB.results?.map((res: any, idx: number) => (
                <div key={idx} className="p-4 rounded-xl bg-slate-950/40 border border-slate-800 space-y-2">
                  <div className="flex justify-between items-center text-xs text-slate-400">
                    <span>Prompt #{res.id || idx + 1}</span>
                    <span className="text-lime-400 font-bold">Score: {res.score ?? "N/A"}</span>
                  </div>
                  <p className="text-xs text-white font-medium">{res.question || res.prompt}</p>
                  <p className="text-xs text-slate-300 bg-slate-900 p-2.5 rounded-lg border border-slate-800/80">{res.response}</p>
                  {res.reason && <p className="text-[11px] text-slate-400 italic">Judge: {res.reason}</p>}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
