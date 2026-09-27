import { apiClient } from "../../services/api/client";

export type ModelProvider =
  | "mock"
  | "openai"
  | "anthropic"
  | "google"
  | "ollama"
  | "huggingface"
  | "azure_openai"
  | "custom";

export type ModelType =
  | "chat"
  | "completion"
  | "embedding"
  | "reranker"
  | "custom";

export interface Model {
  id: string;
  project_id: string;
  name: string;
  provider: ModelProvider;
  model_identifier: string;
  model_type: ModelType;
  configuration: Record<string, unknown> | null;
  input_price_per_million: number;
  output_price_per_million: number;
  pricing_currency: string;
  is_active: boolean;
}

export interface CreateModelPayload {
  project_id: string;
  name: string;
  provider: ModelProvider;
  model_identifier: string;
  model_type: ModelType;
  configuration?: Record<string, unknown> | null;
  input_price_per_million?: number;
  output_price_per_million?: number;
  pricing_currency?: string;
}

export interface UpdateModelPayload {
  name?: string;
  provider?: ModelProvider;
  model_identifier?: string;
  model_type?: ModelType;
  configuration?: Record<string, unknown> | null;
  input_price_per_million?: number;
  output_price_per_million?: number;
  pricing_currency?: string;
}

export async function listModels(projectId: string): Promise<Model[]> {
  const response = await apiClient.get<Model[]>("/api/v1/models", {
    params: {
      project_id: projectId,
    },
  });

  return response.data;
}

export async function createModel(
  payload: CreateModelPayload,
): Promise<Model> {
  const response = await apiClient.post<Model>(
    "/api/v1/models",
    payload,
  );

  return response.data;
}

export async function getModel(modelId: string): Promise<Model> {
  const response = await apiClient.get<Model>(
    `/api/v1/models/${modelId}`,
  );

  return response.data;
}

export async function updateModel(
  modelId: string,
  payload: UpdateModelPayload,
): Promise<Model> {
  const response = await apiClient.patch<Model>(
    `/api/v1/models/${modelId}`,
    payload,
  );

  return response.data;
}

export async function deleteModel(modelId: string): Promise<void> {
  await apiClient.delete(`/api/v1/models/${modelId}`);
}
