import { render, screen, waitFor, queryClient } from "./test-utils";
import { describe, it, expect, vi, beforeEach } from "vitest";
import React from "react";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  useSearchParams: () => ({ get: vi.fn() }),
}));

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

vi.mock("sweetalert2", () => ({
  default: { fire: vi.fn() },
}));

vi.mock("@/libs/api", () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
    interceptors: { request: { use: vi.fn() } },
  },
}));

import { api } from "@/libs/api";
import DatasetsPage from "../app/dashboard/datasets/page";

const mockGet = vi.mocked(api.get);

const mockDatasets = [
  {
    id: 1,
    name: "Test Dataset",
    source_path: "user1/file.csv",
    item_count: 10,
    hash: "abc123",
    user_id: 1,
    createdAt: "2026-01-01T00:00:00Z",
  },
  {
    id: 2,
    name: "Another Dataset",
    source_path: "user1/file2.csv",
    item_count: 5,
    hash: "def456",
    user_id: 1,
    createdAt: "2026-01-02T00:00:00Z",
  },
];

describe("DatasetsPage", () => {
  beforeEach(() => {
    queryClient.clear();
    mockGet.mockReset();
  });

  it("shows loading state while fetching datasets", () => {
    mockGet.mockReturnValue(new Promise(() => {}));
    render(<DatasetsPage />);
    const loadingTexts = screen.getAllByText(/loading.../i);
    expect(loadingTexts.length).toBeGreaterThan(0);
  });

  it("renders without crashing", async () => {
    mockGet.mockResolvedValue({ data: [] });
    render(<DatasetsPage />);
    await waitFor(() =>
      expect(screen.getByText(/^datasets$/i)).toBeInTheDocument()
    );
  });

  it("renders no datasets message when list is empty", async () => {
    mockGet.mockResolvedValue({ data: [] });
    render(<DatasetsPage />);
    await waitFor(() =>
      expect(screen.getByText(/no datasets found/i)).toBeInTheDocument()
    );
  });

  it("renders dataset list with data", async () => {
    mockGet.mockResolvedValue({ data: mockDatasets });
    render(<DatasetsPage />);
    await waitFor(() => expect(screen.getByText(/test dataset/i)).toBeInTheDocument());
    await waitFor(() => expect(screen.getByText(/another dataset/i)).toBeInTheDocument());
  });

  it("renders table headers", async () => {
    mockGet.mockResolvedValue({ data: mockDatasets });
    render(<DatasetsPage />);
    await waitFor(() => expect(screen.getByText(/name/i)).toBeInTheDocument());
  });

  it("renders dataset table rows", async () => {
    mockGet.mockResolvedValue({ data: mockDatasets });
    render(<DatasetsPage />);
    await waitFor(() => expect(screen.getByText(/test dataset/i)).toBeInTheDocument());
  });
});
