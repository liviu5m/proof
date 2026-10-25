import { api } from "@/libs/api";
import { RunData } from "@/types";

export async function createRun(data: RunData) {
  const response = await api.post("/api/runs/", data);
  return response.data;
}

export async function getRuns() {
  const response = await api.get("/api/runs/");
  return response.data;
}
