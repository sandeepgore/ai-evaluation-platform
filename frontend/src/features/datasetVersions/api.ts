import { apiClient } from "../../services/api/client";

export type DatasetVersionStatus =
  | "draft"
  | "ready"
  | "archived";

export interface DatasetVersion {
  id: string;
  dataset_id: string;
  version: number;
  status: DatasetVersionStatus;
  description: string | null;
  case_count: number;
  analytics: DatasetVersionAnalytics | null;
  is_active: boolean;
}

export interface DatasetVersionAnalytics {
  case_count: number;
  reference_count: number;
  context_count: number;
  reference_coverage: number;
  context_coverage: number;
}

export interface CreateDatasetVersionPayload {
  dataset_id: string;
  description?: string | null;
}

export interface UpdateDatasetVersionPayload {
  description?: string | null;
  is_active?: boolean | null;
}

export interface DatasetImportCase {
  input: string;
  expected_output?: string | null;
  metadata?: Record<string, unknown> | null;
}

export interface DatasetImportPayload {
  cases: DatasetImportCase[];
}

export async function listDatasetVersions(
  datasetId: string,
): Promise<DatasetVersion[]> {
  const response = await apiClient.get<DatasetVersion[]>(
    "/api/v1/dataset-versions",
    {
      params: {
        dataset_id: datasetId,
      },
    },
  );

  return response.data;
}

export async function getDatasetVersion(
  versionId: string,
): Promise<DatasetVersion> {
  const response = await apiClient.get<DatasetVersion>(
    `/api/v1/dataset-versions/${versionId}`,
  );

  return response.data;
}

export async function createDatasetVersion(
  payload: CreateDatasetVersionPayload,
): Promise<DatasetVersion> {
  const response = await apiClient.post<DatasetVersion>(
    "/api/v1/dataset-versions",
    payload,
  );

  return response.data;
}

export async function importDataset(
  datasetId: string,
  payload: DatasetImportPayload,
): Promise<DatasetVersion> {
  const response = await apiClient.post<DatasetVersion>(
    `/api/v1/datasets/${datasetId}/import`,
    payload,
  );

  return response.data;
}

export async function updateDatasetVersion(
  versionId: string,
  payload: UpdateDatasetVersionPayload,
): Promise<DatasetVersion> {
  const response = await apiClient.patch<DatasetVersion>(
    `/api/v1/dataset-versions/${versionId}`,
    payload,
  );

  return response.data;
}

export async function finalizeDatasetVersion(
  versionId: string,
): Promise<DatasetVersion> {
  const response = await apiClient.post<DatasetVersion>(
    `/api/v1/dataset-versions/${versionId}/finalize`,
  );

  return response.data;
}

export async function deleteDatasetVersion(
  versionId: string,
): Promise<void> {
  await apiClient.delete(
    `/api/v1/dataset-versions/${versionId}`,
  );
}
