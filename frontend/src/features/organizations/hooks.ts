import {
    useMutation,
    useQuery,
    useQueryClient,
} from "@tanstack/react-query";
import {
    createOrganization,
    deleteOrganization,
    getOrganization,
    listOrganizations,
    updateOrganization,
    type CreateOrganizationPayload,
    type UpdateOrganizationPayload,
} from "./api";
import { useNotification } from "../../components/common/NotificationProvider";

const organizationKeys = {
    all: ["organizations"] as const,
    detail: (organizationId: string) =>
        ["organizations", organizationId] as const,
};

export function useOrganizations() {
    return useQuery({
        queryKey: organizationKeys.all,
        queryFn: listOrganizations,
    });
}

export function useOrganization(organizationId: string | null) {
    return useQuery({
        queryKey: organizationId
            ? organizationKeys.detail(organizationId)
            : ["organizations", "disabled"],
        queryFn: () => getOrganization(organizationId!),
        enabled: Boolean(organizationId),
    });
}

export function useCreateOrganization() {
    const queryClient = useQueryClient();
    const { notify } = useNotification();

    return useMutation({
        mutationFn: (payload: CreateOrganizationPayload) =>
            createOrganization(payload),

        onSuccess: () => {
            void queryClient.invalidateQueries({
                queryKey: organizationKeys.all,
            });
        },

        onError: (error) => {
            if (error instanceof Error) {
                notify(error.message, "error");
            }
        },
    });
}

export function useUpdateOrganization() {
    const queryClient = useQueryClient();
    const { notify } = useNotification();

    return useMutation({
        mutationFn: ({
            organizationId,
            payload,
        }: {
            organizationId: string;
            payload: UpdateOrganizationPayload;
        }) => updateOrganization(organizationId, payload),

        onSuccess: (organization) => {
            queryClient.setQueryData(
                organizationKeys.detail(organization.id),
                organization,
            );

            void queryClient.invalidateQueries({
                queryKey: organizationKeys.all,
            });
        },

        onError: (error) => {
            if (error instanceof Error) {
                notify(error.message, "error");
            }
        },
    });
}

export function useDeleteOrganization() {
    const queryClient = useQueryClient();
    const { notify } = useNotification();

    return useMutation({
        mutationFn: (organizationId: string) =>
            deleteOrganization(organizationId),

        onSuccess: (_data, organizationId) => {
            queryClient.removeQueries({
                queryKey: organizationKeys.detail(organizationId),
            });

            void queryClient.invalidateQueries({
                queryKey: organizationKeys.all,
            });
        },

        onError: (error) => {
            if (error instanceof Error) {
                notify(error.message, "error");
            }
        },
    });
}
