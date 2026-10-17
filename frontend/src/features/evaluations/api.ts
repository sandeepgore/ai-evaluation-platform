import axios from "axios";
import { apiClient } from "../../services/api/client";

async function downloadLogArchive(path: string): Promise<Blob> {
  try {
    const response = await apiClient.get<Blob>(path, { responseType: "blob" });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.data instanceof Blob) {
      let body: { detail?: unknown } | null = null;
      try {
        body = JSON.parse(await error.response.data.text()) as { detail?: unknown };
      } catch {
        body = null;
      }
      if (typeof body?.detail === "string") throw new Error(body.detail);
    }
    throw error;
  }
}

export function downloadEvaluationRunLogs(runId: string): Promise<Blob> {
  return downloadLogArchive(`/api/v1/evaluation-runs/${runId}/logs`);
}

export function downloadSchedulerLogs(): Promise<Blob> {
  return downloadLogArchive("/api/v1/evaluation-scheduler/logs");
}

export async function getEvaluationRunLogsAvailability(
  runId: string,
): Promise<boolean> {
  const response = await apiClient.get<{ available: boolean }>(
    `/api/v1/evaluation-runs/${runId}/logs/availability`,
  );
  return response.data.available;
}

export async function getSchedulerLogsAvailability(): Promise<boolean> {
  const response = await apiClient.get<{ available: boolean }>(
    "/api/v1/evaluation-scheduler/logs/availability",
  );
  return response.data.available;
}

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

export interface EvaluatorMetadata {
  name: string;
  category: string;
  description: string;
  required_inputs: string[];
  requires_reference: boolean;
  requires_context: boolean;
  requires_llm: boolean;
  applicable_to: string[];
  tags: string[];
}

export async function listEvaluators(): Promise<EvaluatorMetadata[]> {
  const response = await apiClient.get<{
    evaluators: EvaluatorMetadata[];
    total: number;
  }>("/api/v1/evaluators");

  return response.data.evaluators;
}

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

export interface CreateEvaluationRunPayload {
  dataset_version_id: string;
  model_id: string;
  name: string;
  evaluation_type: EvaluationType;
  mode: EvaluationRunMode;
  configuration?: Record<string, unknown> | null;
}

export interface CreateEvaluationSchedulePayload extends CreateEvaluationRunPayload {
  schedule_type: "one_time" | "recurring";
  schedule_expression?: string | null;
  timezone: string;
  next_run_at?: string | null;
}

export interface EvaluationSchedule {
  id: string;
  dataset_version_id: string;
  model_id: string;
  name: string;
  evaluation_type: EvaluationType;
  mode: EvaluationRunMode;
  configuration: Record<string, unknown> | null;
  schedule_type: "one_time" | "recurring";
  schedule_expression: string | null;
  timezone: string;
  next_run_at: string | null;
  last_run_at: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export async function createEvaluationSchedule(
  payload: CreateEvaluationSchedulePayload,
): Promise<EvaluationSchedule> {
  const response = await apiClient.post<EvaluationSchedule>(
    "/api/v1/evaluation-schedules",
    payload,
  );
  return response.data;
}

export async function listEvaluationSchedules(): Promise<EvaluationSchedule[]> {
  const response = await apiClient.get<EvaluationSchedule[]>(
    "/api/v1/evaluation-schedules",
  );
  return response.data;
}

export async function updateEvaluationSchedule(
  scheduleId: string,
  payload: Partial<Pick<EvaluationSchedule, "name" | "mode" | "configuration" | "schedule_expression" | "timezone" | "is_active">>,
): Promise<EvaluationSchedule> {
  const response = await apiClient.patch<EvaluationSchedule>(
    `/api/v1/evaluation-schedules/${scheduleId}`,
    payload,
  );
  return response.data;
}

export async function deleteEvaluationSchedule(scheduleId: string): Promise<void> {
  await apiClient.delete(`/api/v1/evaluation-schedules/${scheduleId}`);
}

export async function createEvaluationRun(
  payload: CreateEvaluationRunPayload,
): Promise<EvaluationRun> {
  const response = await apiClient.post<EvaluationRun>(
    "/api/v1/evaluation-runs",
    payload,
  );

  return response.data;
}

export async function executeEvaluationRun(
  evaluationId: string,
): Promise<void> {
  await apiClient.post(
    `/api/v1/evaluation-runs/${evaluationId}/execute`,
  );
}

export async function listEvaluationRuns(params?: {
  datasetVersionId?: string;
  modelId?: string;
  projectId?: string;
}): Promise<EvaluationRun[]> {
  const response = await apiClient.get<EvaluationRun[]>(
    "/api/v1/evaluation-runs",
    {
      params: {
        dataset_version_id: params?.datasetVersionId,
        model_id: params?.modelId,
        project_id: params?.projectId,
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


// -----------------------------------------------------------------------------
// Evaluation Summary
// -----------------------------------------------------------------------------

export interface EvaluationRunSummaryModel {
  id: string;
  name: string;
  provider: string;
  model_identifier: string;
}

export interface EvaluationRunFinalFeedback {
  overall: string;
  strengths: string[];
  weaknesses: string[];
  patterns: string[];
  recommendations: string[];
  evaluator_feedback?: string[];
}

export interface EvaluationRunCost {
  input_cost: number;
  output_cost: number;
  total_cost: number;
  currency: string;
}

export interface EvaluationRunPerformance {
  duration_ms?: number | null;
  total_model_latency_ms: number;
  avg_model_latency_ms?: number | null;
  min_model_latency_ms?: number | null;
  p50_model_latency_ms?: number | null;
  p95_model_latency_ms?: number | null;
  p99_model_latency_ms?: number | null;
  max_model_latency_ms?: number | null;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  throughput_cases_per_second?: number | null;
  total_results: number;
  completed_cases: number;
  failed_cases: number;
  not_applicable_cases: number;
  cost: EvaluationRunCost;
}

export interface EvaluationRunSummary {
  model?: EvaluationRunSummaryModel | null;
  overall_score: number;
  metrics: Record<string, number>;
  feedback: EvaluationRunFinalFeedback;
  total_results: number;
  completed_cases: number;
  failed_cases: number;
  not_applicable_cases: number;
  performance: EvaluationRunPerformance;
}

export async function getEvaluationRunSummary(
  evaluationId: string,
): Promise<EvaluationRunSummary> {
  const response = await apiClient.get<EvaluationRunSummary>(
    `/api/v1/evaluation-runs/${evaluationId}/summary`,
  );

  return response.data;
}

// -----------------------------------------------------------------------------
// Individual Evaluation Results
// -----------------------------------------------------------------------------

export type EvaluationResultStatus = string;

export interface EvaluationResult {
  id: string;
  evaluation_run_id: string;
  dataset_case_id: string;
  status: EvaluationResultStatus;
  actual_output?: string | null;
  expected_output?: string | null;
  scores?: Record<string, unknown> | null;
  feedback?: string | null;
  trace?: Record<string, unknown> | null;
  latency_ms?: number | null;
  input_tokens?: number | null;
  output_tokens?: number | null;
  total_tokens?: number | null;
  error_message?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface EvaluationResultListResponse {
  items: EvaluationResult[];
  total: number;
}

export interface EvaluationResultStatistics {
  total: number;
  completed: number;
  failed: number;
  pending: number;
  not_applicable: number;
}

export interface ListEvaluationResultsParams {
  evaluationRunId: string;
  status?: string;
  offset?: number;
  limit?: number;
}

export async function listEvaluationResults(
  params: ListEvaluationResultsParams,
): Promise<EvaluationResultListResponse> {
  const response = await apiClient.get<EvaluationResultListResponse>(
    "/api/v1/evaluation-results",
    {
      params: {
        evaluation_run_id: params.evaluationRunId,
        status: params.status,
        offset: params.offset ?? 0,
        limit: params.limit ?? 20,
      },
    },
  );

  return response.data;
}

export async function getEvaluationResult(
  resultId: string,
): Promise<EvaluationResult> {
  const response = await apiClient.get<EvaluationResult>(
    `/api/v1/evaluation-results/${resultId}`,
  );

  return response.data;
}

export async function getEvaluationResultStatistics(
  evaluationRunId: string,
): Promise<EvaluationResultStatistics> {
  const response = await apiClient.get<EvaluationResultStatistics>(
    `/api/v1/evaluation-results/run/${evaluationRunId}/statistics`,
  );

  return response.data;
}

export async function cancelEvaluationRun(
  evaluationId: string,
): Promise<EvaluationRun> {
  const response = await apiClient.post<EvaluationRun>(
    `/api/v1/evaluation-runs/${evaluationId}/cancel`,
  );

  return response.data;
}
