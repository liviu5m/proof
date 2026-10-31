import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("@/libs/api", () => ({
  api: {
    post: vi.fn(),
    get: vi.fn(),
    delete: vi.fn(),
  },
}));

import { api } from "@/libs/api";
import { createDataset, getDatasets, downloadDataset, deleteDataset } from "../api/datasets";

const mockPost = vi.mocked(api.post);
const mockGet = vi.mocked(api.get);
const mockDelete = vi.mocked(api.delete);

describe("datasets API", () => {
  beforeEach(() => {
    mockPost.mockReset();
    mockGet.mockReset();
    mockDelete.mockReset();
  });

  it("createDataset posts form data to /api/dataset", async () => {
    const formData = new FormData();
    formData.append("file", new Blob([], { type: "text/csv" }), "test.csv");
    formData.append("name", "Test Dataset");
    mockPost.mockResolvedValueOnce({ data: { id: 1 } });

    const res = await createDataset(formData);

    expect(mockPost).toHaveBeenCalledWith(
      "/api/dataset",
      formData,
      expect.objectContaining({ headers: { "Content-Type": "multipart/form-data" } })
    );
    expect(res).toEqual({ id: 1 });
  });

  it("getDatasets gets with searchQuery param", async () => {
    mockGet.mockResolvedValueOnce({ data: [] });

    await getDatasets("search");

    expect(mockGet).toHaveBeenCalledWith("/api/dataset", {
      params: { searchQuery: "search" },
    });
  });

  it("downloadDataset gets download URL", async () => {
    mockGet.mockResolvedValueOnce({ data: { url: "https://example.com/file.csv" } });

    const res = await downloadDataset(1);

    expect(mockGet).toHaveBeenCalledWith("/api/dataset/1/download");
    expect(res).toEqual({ url: "https://example.com/file.csv" });
  });

  it("deleteDataset deletes by id", async () => {
    mockDelete.mockResolvedValueOnce({ data: { ok: true } });

    const res = await deleteDataset(1);

    expect(mockDelete).toHaveBeenCalledWith("/api/dataset/1");
    expect(res).toEqual({ ok: true });
  });
});