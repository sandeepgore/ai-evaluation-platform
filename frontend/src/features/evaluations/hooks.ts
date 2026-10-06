import { useQuery } from "@tanstack/react-query";

import { config } from "../../config";
import {
  getEvaluationRun,
  getEvaluationRunStatus,
  listEvaluationRuns,
} from "./api";

const evaluationKeys = {
  all: ["evaluations"] as const,
  list: (datasetVersionId?: string, modelId?: string) =>
    ["evaluations", "list", datasetVersionId, modelId] as const,
  detail: (evaluationId: string) =>
    ["evaluations", "detail", evaluationId] as const,
  status: (evaluationId: string) =>
    ["evaluations", "status", evaluationId] as const,
};

export function useEvaluationRuns(params?: {
  datasetVersionId?: string;
  modelId?: string;
}) {
  return useQuery({
    queryKey: evaluationKeys.list(
      params?.datasetVersionId,
      params?.modelId,
    ),
    queryFn: () => listEvaluationRuns(params),
  });
}

export function useEvaluationRun(evaluationId: string | undefined) {
  return useQuery({
    queryKey: evaluationId
      ? evaluationKeys.detail(evaluationId)
      : ["evaluations", "detail", "disabled"],
    queryFn: () => getEvaluationRun(evaluationId!),
    enabled: Boolean(evaluationId),
  });
}

export function useEvaluationRunStatus(
  evaluationId: string | undefined,
  enabled: boolean,
) {
  return useQuery({
    queryKey: evaluationId
      ? evaluationKeys.status(evaluationId)
      : ["evaluations", "status", "disabled"],
    queryFn: () => getEvaluationRunStatus(evaluationId!),
    enabled: Boolean(evaluationId) && enabled,
    refetchInterval: (query) =>
      query.state.data?.status === "running"
        ? config.evaluation.statusPollIntervalMs
        : false,
  });
}