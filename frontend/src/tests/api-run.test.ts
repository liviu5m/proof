import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("@/libs/api", () => ({
  api: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

import { api } from "@/libs/api";
import { createRun, getRuns } from "../api/run";

const mockPost = vi.mocked(api.post);
const mockGet = vi.mocked(api.get);

describe("run API", () => {
  beforeEach(() => {
    mockPost.mockReset();
    mockGet.mockReset();
  });

  it("createRun posts run data to /api/runs/", async () => {
    mockPost.mockResolvedValueOnce({ data: { id: 1 } });

    const res = await createRun({
      dataset_id: 1,
      model: "gemini-3.5-flash-lite",
      system_prompt: "You are a judge.",
      judge_model: "gemini-3.5-flash-lite",
    });

    expect(mockPost).toHaveBeenCalledWith("/api/runs/", {
      dataset_id: 1,
      model: "gemini-3.5-flash-lite",
      system_prompt: "You are a judge.",
      judge_model: "gemini-3.5-flash-lite",
    });
    expect(res).toEqual({ id: 1 });
  });

  it("getRuns gets runs without params", async () => {
    mockGet.mockResolvedValueOnce({ data: [] });

    await getRuns();

    expect(mockGet).toHaveBeenCalledWith("/api/runs/", { params: {} });
  });

  it("getRuns gets runs with search param", async () => {
    mockGet.mockResolvedValueOnce({ data: [] });

    await getRuns("test");

    expect(mockGet).toHaveBeenCalledWith("/api/runs/", { params: { search: "test" } });
  });
});