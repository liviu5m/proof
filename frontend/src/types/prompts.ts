export interface PromptRegistry {
  id: number;
  name: string;
  description: string | null;
  user_id: number;
  current_version_id: number | null;
  current_version_position: number | null;
  version_count: number;
  created_at: string;
  updated_at: string;
}

export interface PromptVersion {
  id: number;
  registry_id: number;
  content_hash: string;
  content: string;
  description: string | null;
  is_current: boolean;
  version_number: number;
  created_at: string;
}

export interface PromptRegistryDetail extends PromptRegistry {
  current_version: PromptVersion | null;
  versions: PromptVersion[];
}

export interface PromptComparison {
  v1: PromptVersion;
  v2: PromptVersion;
  diff: string; // unified diff format
}

export interface CreateRegistryData {
  name: string;
  description?: string;
  initial_content: string;
}

// Mirrors backend PromptRegistryUpdate
export interface UpdateRegistryData {
  name?: string;
  description?: string;
}

export interface CreateVersionData {
  content: string;
  description?: string;
}
