import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock axios so no real network request is made.
// vi.mock is hoisted to the top of the file by Vitest, so the factory runs
// before any top-level `const` is initialized. We therefore create the mocks
// lazily inside the factory and grab them from the imported `api` below.
vi.mock("axios", () => ({
  default: {
    create: vi.fn(() => ({
      get: vi.fn(),
      interceptors: { request: { use: vi.fn() } },
    })),
  },
}));

import { api } from "../libs/api";

const mockGet = vi.mocked(api.get);

describe("api client", () => {
  beforeEach(() => {
    mockGet.mockReset();
  });

  it("GET /datasets returns the response data", async () => {
    mockGet.mockResolvedValueOnce({ data: [{ id: 1, name: "Core" }] });

    const { data } = await api.get("/datasets");

    expect(mockGet).toHaveBeenCalledWith("/datasets");
    expect(data).toEqual([{ id: 1, name: "Core" }]);
  });

  it("propagates GET errors", async () => {
    mockGet.mockRejectedValueOnce(new Error("Network error"));

    await expect(api.get("/datasets")).rejects.toThrow("Network error");
  });
});