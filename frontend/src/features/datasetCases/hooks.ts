import {
    useMutation,
    useQuery,
    useQueryClient,
} from "@tanstack/react-query";
import {
    createDatasetCase,
    deleteDatasetCase,
    getDatasetCase,
    listDatasetCases,
    updateDatasetCase,
    type CreateDatasetCasePayload,
    type UpdateDatasetCasePayload,
} from "./api";
import { useNotification } from "../../components/common/NotificationProvider";

const datasetCaseKeys = {
    all: ["datasetCases"] as const,
    list: (datasetVersionId: string) =>
        ["datasetCases", "list", datasetVersionId] as const,
    detail: (caseId: string) =>
        ["datasetCases", caseId] as const,
};

export function useDatasetCases(datasetVersionId: string | null) {
    return useQuery({
        queryKey: datasetVersionId
            ? datasetCaseKeys.list(datasetVersionId)
            : ["datasetCases", "disabled"],
        queryFn: () => listDatasetCases(datasetVersionId!),
        enabled: Boolean(datasetVersionId),
    });
}

export function useDatasetCase(caseId: string | null) {
    return useQuery({
        queryKey: caseId
            ? datasetCaseKeys.detail(caseId)
            : ["datasetCases", "disabled"],
        queryFn: () => getDatasetCase(caseId!),
        enabled: Boolean(caseId),
    });
}

export function useCreateDatasetCase() {
    const queryClient = useQueryClient();
    const { notify } = useNotification();

    return useMutation({
        mutationFn: (payload: CreateDatasetCasePayload) =>
            createDatasetCase(payload),

        onSuccess: (datasetCase) => {
            void queryClient.invalidateQueries({
                queryKey: datasetCaseKeys.list(
                    datasetCase.dataset_version_id,
                ),
            });
        },

        onError: (error) => {
            if (error instanceof Error) {
                notify(error.message, "error");
            }
        },
    });
}

export function useUpdateDatasetCase() {
    const queryClient = useQueryClient();
    const { notify } = useNotification();

    return useMutation({
        mutationFn: ({
            caseId,
            payload,
        }: {
            caseId: string;
            payload: UpdateDatasetCasePayload;
        }) => updateDatasetCase(caseId, payload),

        onSuccess: (datasetCase) => {
            queryClient.setQueryData(
                datasetCaseKeys.detail(datasetCase.id),
                datasetCase,
            );

            void queryClient.invalidateQueries({
                queryKey: datasetCaseKeys.list(
                    datasetCase.dataset_version_id,
                ),
            });
        },

        onError: (error) => {
            if (error instanceof Error) {
                notify(error.message, "error");
            }
        },
    });
}

export function useDeleteDatasetCase() {
    const queryClient = useQueryClient();
    const { notify } = useNotification();

    return useMutation({
        mutationFn: (caseId: string) =>
            deleteDatasetCase(caseId),

        onSuccess: (_data, caseId) => {
            queryClient.removeQueries({
                queryKey: datasetCaseKeys.detail(caseId),
            });

            void queryClient.invalidateQueries({
                queryKey: datasetCaseKeys.all,
            });
        },

        onError: (error) => {
            if (error instanceof Error) {
                notify(error.message, "error");
            }
        },
    });
}
