"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { GitCompare, Award } from "lucide-react";
import { mockRuns } from "@/libs/mock-data";

export default function ComparePage() {
  const [runA, setRunA] = useState(mockRuns[0].id);
  const [runB, setRunB] = useState(mockRuns[1].id);

  const selectedRunA = mockRuns.find((r) => r.id === runA) || mockRuns[0];
  const selectedRunB = mockRuns.find((r) => r.id === runB) || mockRuns[1];

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
            <select
              value={runA}
              onChange={(e) => setRunA(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg text-xs text-white px-3 py-1.5 focus:outline-none focus:border-indigo-500"
            >
              {mockRuns.map((r) => (
                <option key={r.id} value={r.id}>{r.id} - {r.model}</option>
              ))}
            </select>
          </CardHeader>
          <CardContent className="p-6 space-y-4">
            <div className="flex justify-between items-center bg-slate-950/60 p-4 rounded-xl border border-slate-800/60">
              <div>
                <p className="text-xs text-slate-400">Model</p>
                <p className="font-mono text-indigo-400 text-sm">{selectedRunA.model}</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-slate-400">Score</p>
                <p className="font-bold text-lime-400 text-lg">★ {selectedRunA.score} / 5.0</p>
              </div>
            </div>

            <div className="space-y-3">
              {selectedRunA.results.map((res: any, idx: number) => (
                <div key={idx} className="p-4 rounded-xl bg-slate-950/40 border border-slate-800 space-y-2">
                  <div className="flex justify-between items-center text-xs text-slate-400">
                    <span>Prompt #{res.id}</span>
                    <span className="text-lime-400 font-bold">Score: {res.score}</span>
                  </div>
                  <p className="text-xs text-white font-medium">{res.prompt}</p>
                  <p className="text-xs text-slate-300 bg-slate-900 p-2.5 rounded-lg border border-slate-800/80">{res.response}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-900/80 border-slate-800/30 backdrop-blur-xl shadow-2xl rounded-2xl overflow-hidden">
          <CardHeader className="border-b border-slate-800/30 px-6 py-4 flex flex-row items-center justify-between">
            <CardTitle className="text-base font-semibold text-white">Run B ({selectedRunB.id})</CardTitle>
            <select
              value={runB}
              onChange={(e) => setRunB(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg text-xs text-white px-3 py-1.5 focus:outline-none focus:border-indigo-500"
            >
              {mockRuns.map((r) => (
                <option key={r.id} value={r.id}>{r.id} - {r.model}</option>
              ))}
            </select>
          </CardHeader>
          <CardContent className="p-6 space-y-4">
            <div className="flex justify-between items-center bg-slate-950/60 p-4 rounded-xl border border-slate-800/60">
              <div>
                <p className="text-xs text-slate-400">Model</p>
                <p className="font-mono text-indigo-400 text-sm">{selectedRunB.model}</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-slate-400">Score</p>
                <p className="font-bold text-lime-400 text-lg">★ {selectedRunB.score} / 5.0</p>
              </div>
            </div>

            <div className="space-y-3">
              {selectedRunB.results.map((res: any, idx: number) => (
                <div key={idx} className="p-4 rounded-xl bg-slate-950/40 border border-slate-800 space-y-2">
                  <div className="flex justify-between items-center text-xs text-slate-400">
                    <span>Prompt #{res.id}</span>
                    <span className="text-lime-400 font-bold">Score: {res.score}</span>
                  </div>
                  <p className="text-xs text-white font-medium">{res.prompt}</p>
                  <p className="text-xs text-slate-300 bg-slate-900 p-2.5 rounded-lg border border-slate-800/80">{res.response}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
