import { render, screen, waitFor, queryClient } from "./test-utils";
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
import ComparePage from "../app/dashboard/compare/page";

const mockGet = vi.mocked(api.get);

describe("ComparePage", () => {
  beforeEach(() => {
    queryClient.clear();
    mockGet.mockReset();
  });

  it("shows loading state while fetching runs", () => {
    mockGet.mockReturnValue(new Promise(() => {}));
    render(<ComparePage />);
    const loadingTexts = screen.getAllByText(/loading.../i);
    expect(loadingTexts.length).toBeGreaterThan(0);
  });

  it("renders without crashing", async () => {
    mockGet.mockResolvedValue({ data: [] });
    render(<ComparePage />);
    await waitFor(() =>
      expect(screen.getByText(/no runs available for comparison/i)).toBeInTheDocument()
    );
  });
});