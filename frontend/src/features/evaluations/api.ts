import { apiClient } from "../../services/api/client";

export type EvaluationRunStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export type EvaluationRunMode = "default" | "advanced";

export type EvaluationType =
  | "text"
  | "rag"
  | "conversation"
  | "safety";

export interface EvaluationRun {
  id: string;
  dataset_version_id: string;
  model_id: string;
  name: string;
  status: EvaluationRunStatus;
  mode: EvaluationRunMode;
  evaluation_type: EvaluationType;
  configuration: Record<string, unknown> | null;
  total_cases: number;
  completed_cases: number;
  failed_cases: number;
  not_applicable_cases: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number | null;
}

export async function listEvaluationRuns(params?: {
  datasetVersionId?: string;
  modelId?: string;
}): Promise<EvaluationRun[]> {
  const response = await apiClient.get<EvaluationRun[]>(
    "/api/v1/evaluation-runs",
    {
      params: {
        dataset_version_id: params?.datasetVersionId,
        model_id: params?.modelId,
      },
    },
  );

  return response.data;
}

export interface EvaluationRunStatusResponse {
  id: string;
  status: EvaluationRunStatus;
  total_cases: number;
  completed_cases: number;
  failed_cases: number;
  not_applicable_cases: number;
  processed_cases: number;
  progress_percent: number;
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number | null;
}

export async function getEvaluationRun(
  evaluationId: string,
): Promise<EvaluationRun> {
  const response = await apiClient.get<EvaluationRun>(
    `/api/v1/evaluation-runs/${evaluationId}`,
  );

  return response.data;
}

export async function getEvaluationRunStatus(
  evaluationId: string,
): Promise<EvaluationRunStatusResponse> {
  const response = await apiClient.get<EvaluationRunStatusResponse>(
    `/api/v1/evaluation-runs/${evaluationId}/status`,
  );

  return response.data;
}