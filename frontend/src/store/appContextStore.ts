import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AppContextState {
    selectedOrganizationId: string | null;
    selectedProjectId: string | null;

    setSelectedOrganizationId: (organizationId: string | null) => void;
    setSelectedProjectId: (projectId: string | null) => void;
    clearProject: () => void;
}

export const useAppContextStore = create<AppContextState>()(
    persist(
        (set) => ({
            selectedOrganizationId: null,
            selectedProjectId: null,

            setSelectedOrganizationId: (organizationId) =>
                set({
                    selectedOrganizationId: organizationId,
                    selectedProjectId: null,
                }),

            setSelectedProjectId: (projectId) =>
                set({
                    selectedProjectId: projectId,
                }),

            clearProject: () =>
                set({
                    selectedProjectId: null,
                }),
        }),
        {
            name: "ai-evaluation-app-context",
        },
    ),
);