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
const mockPost = vi.mocked(api.post);
const mockDelete = vi.mocked(api.delete);

describe("DatasetsPage", () => {
  beforeEach(() => {
    queryClient.clear();
    mockGet.mockReset();
    mockPost.mockReset();
    mockDelete.mockReset();
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
});