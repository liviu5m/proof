import { api } from "@/libs/api";

export interface ModelCatalogItem {
  id: string;
  name: string;
  provider: string;
  supports_json_mode: boolean;
  supports_system_prompt: boolean;
  max_tokens: number | null;
  cost_per_1k_tokens: number | null;
}

export async function getModels(): Promise<ModelCatalogItem[]> {
  const response = await api.get("/api/models/");
  return response.data;
}

export async function syncModels(): Promise<{ synced: any[]; count: number; errors: any[] }> {
  const response = await api.post("/api/models/sync");
  return response.data;
}