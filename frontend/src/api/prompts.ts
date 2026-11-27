import { api } from "@/libs/api";
import {
  PromptRegistry,
  PromptRegistryDetail,
  PromptVersion,
  PromptComparison,
  CreateRegistryData,
  CreateVersionData,
  UpdateRegistryData,
} from "@/types/prompts";

export async function getPromptRegistries(): Promise<PromptRegistry[]> {
  const response = await api.get<PromptRegistry[]>("/api/prompts/");
  return response.data;
}

export async function getPromptRegistry(
  id: number,
): Promise<PromptRegistryDetail | null> {
  const response = await api.get<PromptRegistryDetail>(`/api/prompts/${id}`);
  return response.data;
}

export async function createPromptRegistry(
  data: CreateRegistryData,
): Promise<PromptRegistry> {
  const response = await api.post<PromptRegistry>("/api/prompts/", {
    name: data.name,
    description: data.description,
    initial_content: data.initial_content,
  });
  return response.data;
}

export async function updatePromptRegistry(
  registryId: number,
  data: UpdateRegistryData,
): Promise<PromptRegistry> {
  const response = await api.patch<PromptRegistry>(
    `/api/prompts/${registryId}`,
    data,
  );
  return response.data;
}

export async function createPromptVersion(
  registryId: number,
  data: CreateVersionData,
): Promise<PromptVersion> {
  const response = await api.post<PromptVersion>(
    `/api/prompts/${registryId}/versions`,
    {
      content: data.content,
      description: data.description,
    },
  );
  return response.data;
}

export async function activatePromptVersion(
  registryId: number,
  versionId: number,
): Promise<PromptRegistry> {
  const response = await api.post<PromptRegistry>(
    `/api/prompts/${registryId}/versions/${versionId}/activate`,
  );
  return response.data;
}

export async function comparePromptVersions(
  registryId: number,
  v1Id: number,
  v2Id: number,
): Promise<PromptComparison> {
  const response = await api.get<PromptComparison>(
    `/api/prompts/${registryId}/compare`,
    { params: { v1: v1Id, v2: v2Id } },
  );
  return response.data;
}

export async function deletePromptVersion(
  registryId: number,
  versionId: number,
): Promise<void> {
  await api.delete(`/api/prompts/${registryId}/versions/${versionId}`);
}

export async function rollbackPromptVersion(
  registryId: number,
  versionId: number,
): Promise<PromptRegistry> {
  return activatePromptVersion(registryId, versionId);
}

export async function deletePromptRegistry(registryId: number): Promise<void> {
  await api.delete(`/api/prompts/${registryId}`);
}
