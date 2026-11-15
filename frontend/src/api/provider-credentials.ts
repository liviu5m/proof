import { api } from "@/libs/api";
import { ProviderCredential } from "@/types";

export async function getProviderCredentials(): Promise<ProviderCredential[]> {
  const response = await api.get("/api/provider-credentials/");
  return response.data;
}

export async function upsertProviderCredential(data: {
  provider: string;
  api_key: string;
  base_url?: string;
}): Promise<ProviderCredential> {
  const response = await api.post("/api/provider-credentials/", data);
  return response.data;
}

export async function deleteProviderCredential(id: number): Promise<void> {
  await api.delete(`/api/provider-credentials/${id}`);
}