import { render, screen, waitFor, fireEvent, queryClient } from "./test-utils";
import { describe, it, expect, vi, beforeEach } from "vitest";
import React from "react";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

vi.mock("@/libs/api", () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    interceptors: { request: { use: vi.fn() } },
  },
}));

import { api } from "@/libs/api";
import RunsPage from "../app/dashboard/runs/page";

const mockGet = vi.mocked(api.get);

const mockRuns = [
  {
    id: 1,
    dataset_id: 1,
    model: "gemini-3.5-flash-lite",
    system_prompt: "You are helpful",
    judge_model: "gemini-3.5-flash-lite",
    avg_score: 4.5,
    total: 2,
    status: "Completed",
    created_at: "2026-01-01T00:00:00Z",
    datasetName: "Test Dataset",
    results: [
      { id: 0, idx: 0, question: "What is 2+2?", expected: "4", response: "4", score: 5.0, reason: "Correct" },
      { id: 1, idx: 1, question: "Capital of France?", expected: "Paris", response: "Paris", score: 4.0, reason: "Good" },
    ],
  },
  {
    id: 2,
    dataset_id: 1,
    model: "gemini-1.5-pro",
    system_prompt: "You are helpful",
    judge_model: "gemini-3.5-flash-lite",
    avg_score: 3.8,
    total: 2,
    status: "Completed",
    created_at: "2026-01-02T00:00:00Z",
    datasetName: "Test Dataset",
    results: [
      { id: 0, idx: 0, question: "What is 2+2?", expected: "4", response: "5", score: 1.0, reason: "Wrong" },
      { id: 1, idx: 1, question: "Capital of France?", expected: "Paris", response: "Paris", score: 5.0, reason: "Correct" },
    ],
  },
];

describe("RunsPage", () => {
  beforeEach(() => {
    queryClient.clear();
    mockGet.mockReset();
  });

  it("shows loading state while fetching runs", () => {
    mockGet.mockReturnValue(new Promise(() => {}));
    render(<RunsPage />);
    const loadingTexts = screen.getAllByText(/loading.../i);
    expect(loadingTexts.length).toBeGreaterThan(0);
  });

  it("renders empty state when no runs exist", async () => {
    mockGet.mockResolvedValue({ data: [] });
    render(<RunsPage />);
    await waitFor(() =>
      expect(screen.getByText(/no runs created/i)).toBeInTheDocument()
    );
    await waitFor(() =>
      expect(screen.getByText(/go to evaluation/i)).toBeInTheDocument()
    );
  });

  it("runs list with data", async () => {
    mockGet.mockResolvedValue({ data: mockRuns });
    render(<RunsPage />);
    await waitFor(() => expect(screen.getByText(/evaluation runs/i)).toBeInTheDocument());
    await waitFor(() => expect(screen.getByText(/gemini-3.5-flash-lite/i)).toBeInTheDocument());
    await waitFor(() => expect(screen.getByText(/gemini-1.5-pro/i)).toBeInTheDocument());
  });

  it("displays run scores in table", async () => {
    mockGet.mockResolvedValue({ data: mockRuns });
    render(<RunsPage />);
    await waitFor(() => expect(screen.getByText(/4\.5/i)).toBeInTheDocument());
    await waitFor(() => expect(screen.getByText(/3\.8/i)).toBeInTheDocument());
  });

  it("opens run results modal when view button clicked", async () => {
    mockGet.mockResolvedValue({ data: mockRuns });
    render(<RunsPage />);
    await waitFor(() => expect(screen.getByText(/gemini-3.5-flash-lite/i)).toBeInTheDocument());
    const viewButtons = screen.getAllByTitle(/view results/i);
    expect(viewButtons.length).toBeGreaterThan(0);
    fireEvent.click(viewButtons[0]);
    await waitFor(() => expect(screen.getByText(/run results:/i)).toBeInTheDocument());
  });

  it("displays evaluated items in results modal", async () => {
    mockGet.mockResolvedValue({ data: mockRuns });
    render(<RunsPage />);
    await waitFor(() => expect(screen.getByText(/gemini-3.5-flash-lite/i)).toBeInTheDocument());
    const viewButtons = screen.getAllByTitle(/view results/i);
    fireEvent.click(viewButtons[0]);
    await waitFor(() => expect(screen.getByText(/evaluated items/i)).toBeInTheDocument());
    await waitFor(() => expect(screen.getByText(/what is 2\+2\?/i)).toBeInTheDocument());
  });
});
