import { apiClient } from "../../services/api/client";

export interface DatasetCase {
    id: string;
    dataset_version_id: string;
    input: string;
    expected_output: string | null;
    case_metadata: Record<string, unknown> | null;
    has_reference: boolean;
    has_context: boolean;
    position: number;
    is_active: boolean;
}

export interface CreateDatasetCasePayload {
    dataset_version_id: string;
    input: string;
    expected_output?: string | null;
    case_metadata?: Record<string, unknown> | null;
}

export interface UpdateDatasetCasePayload {
    input?: string | null;
    expected_output?: string | null;
    case_metadata?: Record<string, unknown> | null;
    position?: number | null;
}

export async function listDatasetCases(
    datasetVersionId: string,
): Promise<DatasetCase[]> {
    const response = await apiClient.get<DatasetCase[]>(
        "/api/v1/dataset-cases",
        {
            params: {
                dataset_version_id: datasetVersionId,
            },
        },
    );

    return response.data;
}

export async function getDatasetCase(
    caseId: string,
): Promise<DatasetCase> {
    const response = await apiClient.get<DatasetCase>(
        `/api/v1/dataset-cases/${caseId}`,
    );

    return response.data;
}

export async function createDatasetCase(
    payload: CreateDatasetCasePayload,
): Promise<DatasetCase> {
    const response = await apiClient.post<DatasetCase>(
        "/api/v1/dataset-cases",
        payload,
    );

    return response.data;
}

export async function updateDatasetCase(
    caseId: string,
    payload: UpdateDatasetCasePayload,
): Promise<DatasetCase> {
    const response = await apiClient.patch<DatasetCase>(
        `/api/v1/dataset-cases/${caseId}`,
        payload,
    );

    return response.data;
}

export async function deleteDatasetCase(
    caseId: string,
): Promise<void> {
    await apiClient.delete(`/api/v1/dataset-cases/${caseId}`);
}
