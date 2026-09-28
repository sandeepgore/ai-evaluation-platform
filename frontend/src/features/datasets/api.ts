import { apiClient } from "../../services/api/client";

export type DatasetType =
    | "generation"
    | "classification"
    | "rag"
    | "conversation"
    | "custom";

export interface Dataset {
    id: string;
    project_id: string;
    name: string;
    slug: string;
    description: string | null;
    dataset_type: DatasetType;
    is_active: boolean;
}

export interface CreateDatasetPayload {
    project_id: string;
    name: string;
    slug: string;
    description?: string | null;
    dataset_type?: DatasetType;
}

export interface UpdateDatasetPayload {
    name?: string | null;
    slug?: string | null;
    description?: string | null;
    dataset_type?: DatasetType | null;
}

export async function listDatasets(
    projectId: string,
): Promise<Dataset[]> {
    const response = await apiClient.get<Dataset[]>("/api/v1/datasets", {
        params: {
            project_id: projectId,
        },
    });

    return response.data;
}

export async function createDataset(
    payload: CreateDatasetPayload,
): Promise<Dataset> {
    const response = await apiClient.post<Dataset>(
        "/api/v1/datasets",
        payload,
    );

    return response.data;
}

export async function getDataset(
    datasetId: string,
): Promise<Dataset> {
    const response = await apiClient.get<Dataset>(
        `/api/v1/datasets/${datasetId}`,
    );

    return response.data;
}

export async function updateDataset(
    datasetId: string,
    payload: UpdateDatasetPayload,
): Promise<Dataset> {
    const response = await apiClient.patch<Dataset>(
        `/api/v1/datasets/${datasetId}`,
        payload,
    );

    return response.data;
}

export async function deleteDataset(
    datasetId: string,
): Promise<void> {
    await apiClient.delete(`/api/v1/datasets/${datasetId}`);
}