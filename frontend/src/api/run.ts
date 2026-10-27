import { api } from "@/libs/api";
import { RunData } from "@/types";

export async function createRun(data: RunData) {
  const response = await api.post("/api/runs/", data);
  return response.data;
}

export async function getRuns(search?: string) {
  const response = await api.get("/api/runs/", { params: search ? { search } : {} });
  return response.data;
}
