import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import {
  createDatasetVersion,
  type DatasetImportPayload,
  deleteDatasetVersion,
  finalizeDatasetVersion,
  getDatasetVersion,
  importDataset,
  listDatasetVersions,
  updateDatasetVersion,
  type CreateDatasetVersionPayload,
  type UpdateDatasetVersionPayload,
} from "./api";

const datasetVersionKeys = {
  all: ["datasetVersions"] as const,
  list: (datasetId: string) =>
    ["datasetVersions", "list", datasetId] as const,
  detail: (versionId: string) =>
    ["datasetVersions", versionId] as const,
};

export function useDatasetVersions(datasetId: string | null) {
  return useQuery({
    queryKey: datasetId
      ? datasetVersionKeys.list(datasetId)
      : ["datasetVersions", "disabled"],
    queryFn: () => listDatasetVersions(datasetId!),
    enabled: Boolean(datasetId),
  });
}

export function useDatasetVersion(versionId: string | null) {
  return useQuery({
    queryKey: versionId
      ? datasetVersionKeys.detail(versionId)
      : ["datasetVersions", "disabled"],
    queryFn: () => getDatasetVersion(versionId!),
    enabled: Boolean(versionId),
  });
}

export function useCreateDatasetVersion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CreateDatasetVersionPayload) =>
      createDatasetVersion(payload),
    onSuccess: (version) => {
      void queryClient.invalidateQueries({
        queryKey: datasetVersionKeys.list(version.dataset_id),
      });
    },
  });
}

export function useUpdateDatasetVersion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      versionId,
      payload,
    }: {
      versionId: string;
      payload: UpdateDatasetVersionPayload;
    }) => updateDatasetVersion(versionId, payload),
    onSuccess: (version) => {
      queryClient.setQueryData(
        datasetVersionKeys.detail(version.id),
        version,
      );

      void queryClient.invalidateQueries({
        queryKey: datasetVersionKeys.list(version.dataset_id),
      });
    },
  });
}

export function useFinalizeDatasetVersion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (versionId: string) =>
      finalizeDatasetVersion(versionId),
    onSuccess: (version) => {
      queryClient.setQueryData(
        datasetVersionKeys.detail(version.id),
        version,
      );

      void queryClient.invalidateQueries({
        queryKey: datasetVersionKeys.list(version.dataset_id),
      });
    },
  });
}

export function useDeleteDatasetVersion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (versionId: string) =>
      deleteDatasetVersion(versionId),
    onSuccess: (_data, versionId) => {
      queryClient.removeQueries({
        queryKey: datasetVersionKeys.detail(versionId),
      });

      void queryClient.invalidateQueries({
        queryKey: datasetVersionKeys.all,
      });
    },
  });
}

export function useImportDataset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      datasetId,
      payload,
    }: {
      datasetId: string;
      payload: DatasetImportPayload;
    }) => importDataset(datasetId, payload),
    onSuccess: (version) => {
      void queryClient.invalidateQueries({
        queryKey: datasetVersionKeys.list(version.dataset_id),
      });
    },
  });
}