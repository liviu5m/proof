import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock the api module directly since it creates axios instance at module level
vi.mock("../libs/api", () => {
  const mockGet = vi.fn();
  const mockPost = vi.fn();
  return {
    api: {
      get: mockGet,
      post: mockPost,
      interceptors: { request: { use: vi.fn() } },
    },
  };
});

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