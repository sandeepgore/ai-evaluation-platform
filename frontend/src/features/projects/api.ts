import { apiClient } from "../../services/api/client";

export interface Project {
    id: string;
    organization_id: string;
    name: string;
    slug: string;
    description: string | null;
    is_active: boolean;
}

export interface CreateProjectPayload {
    organization_id: string;
    name: string;
    slug: string;
    description?: string | null;
}

export interface UpdateProjectPayload {
    name?: string | null;
    slug?: string | null;
    description?: string | null;
}

export async function listProjects(
    organizationId: string,
): Promise<Project[]> {
    const response = await apiClient.get<Project[]>("/api/v1/projects", {
        params: {
            organization_id: organizationId,
        },
    });
    return response.data;
}

export async function createProject(
    payload: CreateProjectPayload,
): Promise<Project> {
    const response = await apiClient.post<Project>(
        "/api/v1/projects",
        payload,
    );
    return response.data;
}

export async function getProject(projectId: string): Promise<Project> {
    const response = await apiClient.get<Project>(
        `/api/v1/projects/${projectId}`,
    );
    return response.data;
}

export async function updateProject(
    projectId: string,
    payload: UpdateProjectPayload,
): Promise<Project> {
    const response = await apiClient.patch<Project>(
        `/api/v1/projects/${projectId}`,
        payload,
    );
    return response.data;
}

export async function deleteProject(projectId: string): Promise<void> {
    await apiClient.delete(`/api/v1/projects/${projectId}`);
}
