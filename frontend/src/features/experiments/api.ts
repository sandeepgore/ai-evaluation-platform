import { apiClient } from "../../services/api/client";

export interface Experiment {
  id: string;
  project_id: string | null;
  name: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
}

export interface CreateExperimentPayload {
  project_id: string;
  name: string;
  description?: string | null;
}

export interface ExperimentSnapshotRun {
  run: {
    name: string;
    model_id: string;
    dataset_version_id: string;
    status: string;
    total_cases: number;
    completed_cases: number;
    failed_cases: number;
    not_applicable_cases?: number;
    duration_ms: number | null;
  };
  summary: {
    overall_score: number;
    metrics: Record<string, number>;
    performance: Record<string, unknown>;
    feedback: Record<string, unknown>;
  };
}

export interface ExperimentSnapshot {
  id: string;
  experiment_id: string;
  run_ids: string[];
  run_results: Record<string, ExperimentSnapshotRun>;
  comparison: Record<string, unknown>;
  calculation_version: number;
  created_at: string;
}

export async function listExperiments(
  scope: "recent" | "all" = "all",
  projectId?: string,
) {
  const response = await apiClient.get<Experiment[]>("/api/v1/experiments", {
    params: { scope, project_id: projectId },
  });
  return response.data;
}

export async function getExperiment(experimentId: string) {
  const response = await apiClient.get<Experiment>(
    `/api/v1/experiments/${experimentId}`,
  );
  return response.data;
}

export async function createExperiment(payload: CreateExperimentPayload) {
  const response = await apiClient.post<Experiment>(
    "/api/v1/experiments",
    payload,
  );
  return response.data;
}

export async function deleteExperiment(experimentId: string) {
  await apiClient.delete(`/api/v1/experiments/${experimentId}`);
}

export async function listExperimentSnapshots(experimentId: string) {
  const response = await apiClient.get<ExperimentSnapshot[]>(
    `/api/v1/experiments/${experimentId}/snapshots`,
  );
  return response.data;
}

export async function createExperimentSnapshot(
  experimentId: string,
  runIds: string[],
) {
  const response = await apiClient.post<ExperimentSnapshot>(
    `/api/v1/experiments/${experimentId}/snapshots`,
    { run_ids: runIds },
  );
  return response.data;
}
