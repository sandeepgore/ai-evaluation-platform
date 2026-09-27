import { apiClient } from "../../services/api/client";

export interface Organization {
    id: string;
    name: string;
    slug: string;
    description: string | null;
    is_active: boolean;
}

export interface CreateOrganizationPayload {
    name: string;
    slug: string;
    description?: string | null;
}

export interface UpdateOrganizationPayload {
    name?: string | null;
    slug?: string | null;
    description?: string | null;
}

export async function listOrganizations(): Promise<Organization[]> {
    const response = await apiClient.get<Organization[]>("/api/v1/organizations");
    return response.data;
}

export async function createOrganization(
    payload: CreateOrganizationPayload,
): Promise<Organization> {
    const response = await apiClient.post<Organization>(
        "/api/v1/organizations",
        payload,
    );
    return response.data;
}

export async function getOrganization(
    organizationId: string,
): Promise<Organization> {
    const response = await apiClient.get<Organization>(
        `/api/v1/organizations/${organizationId}`,
    );
    return response.data;
}

export async function updateOrganization(
    organizationId: string,
    payload: UpdateOrganizationPayload,
): Promise<Organization> {
    const response = await apiClient.patch<Organization>(
        `/api/v1/organizations/${organizationId}`,
        payload,
    );
    return response.data;
}

export async function deleteOrganization(
    organizationId: string,
): Promise<void> {
    await apiClient.delete(`/api/v1/organizations/${organizationId}`);
}
