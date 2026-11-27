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

vi.mock("@/api/models", () => ({
  getModels: vi.fn(),
  syncModels: vi.fn(),
}));

import { getDatasets } from "@/api/datasets";
import { createRun } from "@/api/run";
import { getModels, syncModels } from "@/api/models";
import EvaluatePage from "../app/dashboard/evaluate/page";

const mockGetDatasets = vi.mocked(getDatasets);
const mockCreateRun = vi.mocked(createRun);
const mockGetModels = vi.mocked(getModels);
const mockSyncModels = vi.mocked(syncModels);

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

const mockModels = [
  { id: "1", name: "gemini-3.5-flash-lite", provider: "google", supports_json_mode: true, supports_system_prompt: true, max_tokens: 8192, input_cost_per_1m: 1.0, output_cost_per_1m: 4.0 },
  { id: "2", name: "gpt-4", provider: "openai", supports_json_mode: true, supports_system_prompt: true, max_tokens: 8192, input_cost_per_1m: 30.0, output_cost_per_1m: 60.0 },
  { id: "3", name: "claude-3", provider: "anthropic", supports_json_mode: true, supports_system_prompt: true, max_tokens: 4096, input_cost_per_1m: 15.0, output_cost_per_1m: 75.0 },
];

describe("EvaluatePage", () => {
  beforeEach(() => {
    queryClient.clear();
    mockGetDatasets.mockReset();
    mockCreateRun.mockReset();
    mockGetModels.mockReset();
    mockSyncModels.mockReset();
    mockGetModels.mockResolvedValue(mockModels);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("renders without crashing", async () => {
    mockGetDatasets.mockResolvedValue([]);
    render(<EvaluatePage />);
    await act(async () => {});
    await waitFor(() =>
      expect(screen.getByText(/Select dataset/i)).toBeInTheDocument()
    );
  });

  it("renders model selection dropdowns", async () => {
    mockGetDatasets.mockResolvedValue(mockDatasets);
    render(<EvaluatePage />);
    // Wait for models query to resolve by checking for model options
    await waitFor(() => {
      expect(screen.getByText(/Runner Model/i)).toBeInTheDocument();
    }, { timeout: 3000 });
    await waitFor(() => {
      expect(screen.getByText(/Model that evaluates answers/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it("renders system prompt textarea", async () => {
    mockGetDatasets.mockResolvedValue(mockDatasets);
    render(<EvaluatePage />);
    await act(async () => {});
    await waitFor(() =>
      expect(screen.getByText(/AI Judge System Prompt/i)).toBeInTheDocument()
    );
  });

  it("renders start evaluation button", async () => {
    mockGetDatasets.mockResolvedValue(mockDatasets);
    render(<EvaluatePage />);
    await act(async () => {});
    await waitFor(() =>
      expect(screen.getByText(/Start Evaluation Run/i)).toBeInTheDocument()
    );
  });

  it("calls createRun on start evaluation", async () => {
    mockGetDatasets.mockResolvedValue(mockDatasets);
    mockCreateRun.mockResolvedValue({ data: { run_id: 1 } });
    render(<EvaluatePage />);
    await act(async () => {});
    await waitFor(() =>
      expect(screen.getByText(/Start Evaluation Run/i)).toBeInTheDocument()
    );
    const buttons = screen.getAllByText(/Start Evaluation Run/i);
    fireEvent.click(buttons[0]);
    await waitFor(() => expect(mockCreateRun).toHaveBeenCalled());
  });
});
