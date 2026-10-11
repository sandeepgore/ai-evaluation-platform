import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import { config } from "../../config";
import { useNotification } from "../../components/common/NotificationProvider";
import {
  createEvaluationRun,
  executeEvaluationRun,
  getEvaluationRun,
  getEvaluationRunStatus,
  listEvaluationRuns,
  getEvaluationRunSummary,
  listEvaluationResults,
  getEvaluationResult,
  getEvaluationResultStatistics,
  type CreateEvaluationRunPayload,
  type ListEvaluationResultsParams,
} from "./api";

const evaluationKeys = {
  all: ["evaluations"] as const,

  list: (datasetVersionId?: string, modelId?: string) =>
    ["evaluations", "list", datasetVersionId, modelId] as const,

  detail: (evaluationId: string) =>
    ["evaluations", "detail", evaluationId] as const,

  status: (evaluationId: string) =>
    ["evaluations", "status", evaluationId] as const,

  summary: (evaluationId: string) =>
    ["evaluations", "summary", evaluationId] as const,

  results: (
    evaluationRunId: string,
    status?: string,
    offset?: number,
    limit?: number,
  ) =>
    [
      "evaluations",
      "results",
      evaluationRunId,
      status,
      offset,
      limit,
    ] as const,

  result: (resultId: string) =>
    ["evaluations", "result", resultId] as const,

  resultStatistics: (evaluationRunId: string) =>
    ["evaluations", "result-statistics", evaluationRunId] as const,
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

export function useCreateEvaluationRun() {
  const queryClient = useQueryClient();
  const { notify } = useNotification();

  return useMutation({
    mutationFn: (payload: CreateEvaluationRunPayload) =>
      createEvaluationRun(payload),

    onSuccess: (run) => {
      queryClient.setQueryData(
        evaluationKeys.detail(run.id),
        run,
      );

      void queryClient.invalidateQueries({
        queryKey: evaluationKeys.all,
      });

      notify("Evaluation created successfully.", "success");
    },

    onError: (error) => {
      notify(
        error instanceof Error
          ? error.message
          : "Unable to create evaluation.",
        "error",
      );
    },
  });
}

export function useExecuteEvaluationRun() {
  const queryClient = useQueryClient();
  const { notify } = useNotification();

  return useMutation({
    mutationFn: (evaluationId: string) =>
      executeEvaluationRun(evaluationId),

    onSuccess: (_data, evaluationId) => {
      void queryClient.invalidateQueries({
        queryKey: evaluationKeys.detail(evaluationId),
      });

      void queryClient.invalidateQueries({
        queryKey: evaluationKeys.status(evaluationId),
      });

      void queryClient.invalidateQueries({
        queryKey: evaluationKeys.all,
      });

      notify("Evaluation submitted to the queue.", "success");
    },

    onError: (error) => {
      notify(
        error instanceof Error
          ? error.message
          : "Unable to submit evaluation to the queue.",
        "error",
      );
    },
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

// -----------------------------------------------------------------------------
// Evaluation Summary
// -----------------------------------------------------------------------------

export function useEvaluationRunSummary(
  evaluationId: string | undefined,
) {
  return useQuery({
    queryKey: evaluationId
      ? evaluationKeys.summary(evaluationId)
      : ["evaluations", "summary", "disabled"],
    queryFn: () => getEvaluationRunSummary(evaluationId!),
    enabled: Boolean(evaluationId),
  });
}

// -----------------------------------------------------------------------------
// Individual Evaluation Results
// -----------------------------------------------------------------------------

export function useEvaluationResults(
  params: ListEvaluationResultsParams | undefined,
) {
  const evaluationRunId = params?.evaluationRunId;
  const status = params?.status;
  const offset = params?.offset ?? 0;
  const limit = params?.limit ?? 20;

  return useQuery({
    queryKey: evaluationRunId
      ? evaluationKeys.results(
        evaluationRunId,
        status,
        offset,
        limit,
      )
      : ["evaluations", "results", "disabled"],

    queryFn: () =>
      listEvaluationResults({
        evaluationRunId: evaluationRunId!,
        status,
        offset,
        limit,
      }),

    enabled: Boolean(evaluationRunId),
  });
}

export function useEvaluationResult(
  resultId: string | undefined,
) {
  return useQuery({
    queryKey: resultId
      ? evaluationKeys.result(resultId)
      : ["evaluations", "result", "disabled"],
    queryFn: () => getEvaluationResult(resultId!),
    enabled: Boolean(resultId),
  });
}

export function useEvaluationResultStatistics(
  evaluationRunId: string | undefined,
) {
  return useQuery({
    queryKey: evaluationRunId
      ? evaluationKeys.resultStatistics(evaluationRunId)
      : ["evaluations", "result-statistics", "disabled"],

    queryFn: () =>
      getEvaluationResultStatistics(evaluationRunId!),

    enabled: Boolean(evaluationRunId),
  });
}