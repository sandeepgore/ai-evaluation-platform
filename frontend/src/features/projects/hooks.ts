import {
    useMutation,
    useQuery,
    useQueryClient,
} from "@tanstack/react-query";
import {
    createProject,
    deleteProject,
    getProject,
    listProjects,
    updateProject,
    type CreateProjectPayload,
    type UpdateProjectPayload,
} from "./api";

const projectKeys = {
    all: ["projects"] as const,
    list: (organizationId: string) =>
        ["projects", "list", organizationId] as const,
    detail: (projectId: string) => ["projects", projectId] as const,
};

export function useProjects(organizationId: string | null) {
    return useQuery({
        queryKey: organizationId
            ? projectKeys.list(organizationId)
            : ["projects", "disabled"],
        queryFn: () => listProjects(organizationId!),
        enabled: Boolean(organizationId),
    });
}

export function useProject(projectId: string | null) {
    return useQuery({
        queryKey: projectId
            ? projectKeys.detail(projectId)
            : ["projects", "disabled"],
        queryFn: () => getProject(projectId!),
        enabled: Boolean(projectId),
    });
}

export function useCreateProject() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (payload: CreateProjectPayload) =>
            createProject(payload),
        onSuccess: (project) => {
            void queryClient.invalidateQueries({
                queryKey: projectKeys.list(project.organization_id),
            });
        },
    });
}

export function useUpdateProject() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            projectId,
            payload,
        }: {
            projectId: string;
            payload: UpdateProjectPayload;
        }) => updateProject(projectId, payload),
        onSuccess: (project) => {
            queryClient.setQueryData(
                projectKeys.detail(project.id),
                project,
            );

            void queryClient.invalidateQueries({
                queryKey: projectKeys.list(project.organization_id),
            });
        },
    });
}

export function useDeleteProject() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (projectId: string) => deleteProject(projectId),
        onSuccess: (_data, projectId) => {
            queryClient.removeQueries({
                queryKey: projectKeys.detail(projectId),
            });

            void queryClient.invalidateQueries({
                queryKey: projectKeys.all,
            });
        },
    });
}
