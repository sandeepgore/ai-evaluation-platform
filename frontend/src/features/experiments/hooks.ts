import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNotification } from "../../components/common/NotificationProvider";
import {
  createExperiment,
  createExperimentSnapshot,
  deleteExperiment,
  getExperiment,
  listExperimentSnapshots,
  listExperiments,
  type CreateExperimentPayload,
} from "./api";

const experimentKeys = {
  all: ["experiments"] as const,
  list: (scope: "recent" | "all", projectId?: string | null) => ["experiments", "list", scope, projectId] as const,
  detail: (id: string, projectId?: string | null) => ["experiments", "detail", id, projectId] as const,
  snapshots: (id: string) => ["experiments", id, "snapshots"] as const,
};

export function useExperiments(
  scope: "recent" | "all" = "all",
  projectId?: string | null,
) {
  return useQuery({
    queryKey: experimentKeys.list(scope, projectId),
    queryFn: () => listExperiments(scope, projectId!),
    enabled: Boolean(projectId),
  });
}

export function useExperiment(experimentId: string | undefined) {
  return useQuery({
    queryKey: experimentId
      ? experimentKeys.detail(experimentId)
      : ["experiments", "detail", "disabled"],
    queryFn: () => getExperiment(experimentId!),
    enabled: Boolean(experimentId),
  });
}

export function useExperimentSnapshots(experimentId: string | undefined) {
  return useQuery({
    queryKey: experimentId
      ? experimentKeys.snapshots(experimentId)
      : ["experiments", "snapshots", "disabled"],
    queryFn: () => listExperimentSnapshots(experimentId!),
    enabled: Boolean(experimentId),
  });
}

export function useCreateExperiment() {
  const queryClient = useQueryClient();
  const { notify } = useNotification();

  return useMutation({
    mutationFn: (payload: CreateExperimentPayload) => createExperiment(payload),
    onSuccess: (experiment) => {
      queryClient.setQueryData(experimentKeys.detail(experiment.id), experiment);
      void queryClient.invalidateQueries({ queryKey: experimentKeys.all });
      notify("Experiment created.", "success");
    },
    onError: (error) => {
      notify(error instanceof Error ? error.message : "Unable to create experiment.", "error");
    },
  });
}

export function useDeleteExperiment() {
  const queryClient = useQueryClient();
  const { notify } = useNotification();

  return useMutation({
    mutationFn: deleteExperiment,
    onSuccess: (_data, experimentId) => {
      queryClient.removeQueries({ queryKey: experimentKeys.detail(experimentId) });
      void queryClient.invalidateQueries({ queryKey: experimentKeys.all });
      notify("Experiment deleted.", "success");
    },
    onError: (error) => {
      notify(error instanceof Error ? error.message : "Unable to delete experiment.", "error");
    },
  });
}

export function useCreateExperimentSnapshot(experimentId: string) {
  const queryClient = useQueryClient();
  const { notify } = useNotification();

  return useMutation({
    mutationFn: (runIds: string[]) => createExperimentSnapshot(experimentId, runIds),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: experimentKeys.snapshots(experimentId),
      });
      notify("Comparison snapshot saved.", "success");
    },
    onError: (error) => {
      notify(error instanceof Error ? error.message : "Unable to create comparison snapshot.", "error");
    },
  });
}
