import { render, screen, waitFor, act, fireEvent, queryClient } from "./test-utils";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import React from "react";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  useSearchParams: () => ({ get: vi.fn() }),
}));

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

vi.mock("@/api/datasets", () => ({
  getDatasets: vi.fn(),
}));

vi.mock("@/api/run", () => ({
  createRun: vi.fn(),
}));

import { getDatasets } from "@/api/datasets";
import { createRun } from "@/api/run";
import EvaluatePage from "../app/dashboard/evaluate/page";

const mockGetDatasets = vi.mocked(getDatasets);
const mockCreateRun = vi.mocked(createRun);

const mockDatasets = [
  {
    id: 1,
    name: "Test Dataset",
    item_count: 10,
    hash: "abc",
    createdAt: "2026-01-01",
  },
  {
    id: 2,
    name: "Another Dataset",
    item_count: 5,
    hash: "def",
    createdAt: "2026-01-02",
  },
];

describe("EvaluatePage", () => {
  beforeEach(() => {
    queryClient.clear();
    mockGetDatasets.mockReset();
    mockCreateRun.mockReset();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading state while fetching datasets", () => {
    mockGetDatasets.mockReturnValue(new Promise(() => {}));
    render(<EvaluatePage />);
    const loadingTexts = screen.getAllByText(/loading.../i);
    expect(loadingTexts.length).toBeGreaterThan(0);
  });

  it("renders without crashing", async () => {
    mockGetDatasets.mockResolvedValue([]);
    render(<EvaluatePage />);
    await act(async () => {});
    await waitFor(() =>
      expect(screen.getByText(/no datasets available/i)).toBeInTheDocument()
    );
  });

  it("renders model selection dropdowns", async () => {
    mockGetDatasets.mockResolvedValue(mockDatasets);
    render(<EvaluatePage />);
    await act(async () => {});
    await waitFor(() =>
      expect(screen.getByText(/target llm model/i)).toBeInTheDocument()
    );
    await waitFor(() =>
      expect(screen.getByText(/target llm judge model/i)).toBeInTheDocument()
    );
  });

  it("renders system prompt textarea", async () => {
    mockGetDatasets.mockResolvedValue(mockDatasets);
    render(<EvaluatePage />);
    await act(async () => {});
    await waitFor(() =>
      expect(screen.getByText(/ai judge system prompt/i)).toBeInTheDocument()
    );
  });

  it("renders start evaluation button", async () => {
    mockGetDatasets.mockResolvedValue(mockDatasets);
    render(<EvaluatePage />);
    await act(async () => {});
    await waitFor(() =>
      expect(screen.getByText(/start evaluation/i)).toBeInTheDocument()
    );
  });

  it("calls createRun on start evaluation", async () => {
    mockGetDatasets.mockResolvedValue(mockDatasets);
    mockCreateRun.mockResolvedValue({ data: { run_id: 1 } });
    render(<EvaluatePage />);
    await act(async () => {});
    await waitFor(() =>
      expect(screen.getByText(/start evaluation/i)).toBeInTheDocument()
    );
    const buttons = screen.getAllByText(/start evaluation/i);
    fireEvent.click(buttons[0]);
    await waitFor(() => expect(mockCreateRun).toHaveBeenCalled());
  });
});
