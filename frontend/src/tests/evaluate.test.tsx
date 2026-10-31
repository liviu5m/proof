import { render, screen, waitFor, act, queryClient } from "./test-utils";
import { describe, it, expect, vi, beforeEach } from "vitest";
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

import { getDatasets } from "@/api/datasets";
import EvaluatePage from "../app/dashboard/evaluate/page";

const mockGetDatasets = vi.mocked(getDatasets);

describe("EvaluatePage", () => {
  beforeEach(() => {
    queryClient.clear();
    mockGetDatasets.mockReset();
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
    mockGetDatasets.mockResolvedValue([
      {
        id: 1,
        name: "Test Dataset",
        item_count: 10,
        hash: "abc",
        createdAt: "2026-01-01",
      },
    ]);

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
    mockGetDatasets.mockResolvedValue([
      {
        id: 1,
        name: "Test Dataset",
        item_count: 10,
        hash: "abc",
        createdAt: "2026-01-01",
      },
    ]);

    render(<EvaluatePage />);
    await act(async () => {});
    await waitFor(() =>
      expect(screen.getByText(/ai judge system prompt/i)).toBeInTheDocument()
    );
  });

  it("renders start evaluation button", async () => {
    mockGetDatasets.mockResolvedValue([
      {
        id: 1,
        name: "Test Dataset",
        item_count: 10,
        hash: "abc",
        createdAt: "2026-01-01",
      },
    ]);

    render(<EvaluatePage />);
    await act(async () => {});
    await waitFor(() =>
      expect(screen.getByText(/start evaluation run/i)).toBeInTheDocument()
    );
  });
});
