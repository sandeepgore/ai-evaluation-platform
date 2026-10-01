import {
    useMutation,
    useQuery,
    useQueryClient,
} from "@tanstack/react-query";
import {
    createDataset,
    deleteDataset,
    getDataset,
    listDatasets,
    updateDataset,
    type CreateDatasetPayload,
    type UpdateDatasetPayload,
} from "./api";
import { useNotification } from "../../components/common/NotificationProvider";

const datasetKeys = {
    all: ["datasets"] as const,
    list: (projectId: string) =>
        ["datasets", "list", projectId] as const,
    detail: (datasetId: string) =>
        ["datasets", datasetId] as const,
};

export function useDatasets(projectId: string | null) {
    return useQuery({
        queryKey: projectId
            ? datasetKeys.list(projectId)
            : ["datasets", "disabled"],
        queryFn: () => listDatasets(projectId!),
        enabled: Boolean(projectId),
    });
}

export function useDataset(datasetId: string | null) {
    return useQuery({
        queryKey: datasetId
            ? datasetKeys.detail(datasetId)
            : ["datasets", "disabled"],
        queryFn: () => getDataset(datasetId!),
        enabled: Boolean(datasetId),
    });
}

export function useCreateDataset() {
    const queryClient = useQueryClient();
    const { notify } = useNotification();

    return useMutation({
        mutationFn: (payload: CreateDatasetPayload) =>
            createDataset(payload),

        onSuccess: (dataset) => {
            void queryClient.invalidateQueries({
                queryKey: datasetKeys.list(dataset.project_id),
            });
        },

        onError: (error) => {
            if (error instanceof Error) {
                notify(error.message, "error");
            }
        },
    });
}

export function useUpdateDataset() {
    const queryClient = useQueryClient();
    const { notify } = useNotification();

    return useMutation({
        mutationFn: ({
            datasetId,
            payload,
        }: {
            datasetId: string;
            payload: UpdateDatasetPayload;
        }) => updateDataset(datasetId, payload),

        onSuccess: (dataset) => {
            queryClient.setQueryData(
                datasetKeys.detail(dataset.id),
                dataset,
            );

            void queryClient.invalidateQueries({
                queryKey: datasetKeys.list(dataset.project_id),
            });
        },

        onError: (error) => {
            if (error instanceof Error) {
                notify(error.message, "error");
            }
        },
    });
}

export function useDeleteDataset() {
    const queryClient = useQueryClient();
    const { notify } = useNotification();

    return useMutation({
        mutationFn: (datasetId: string) =>
            deleteDataset(datasetId),

        onSuccess: (_data, datasetId) => {
            queryClient.removeQueries({
                queryKey: datasetKeys.detail(datasetId),
            });

            void queryClient.invalidateQueries({
                queryKey: datasetKeys.all,
            });
        },

        onError: (error) => {
            if (error instanceof Error) {
                notify(error.message, "error");
            }
        },
    });
}
