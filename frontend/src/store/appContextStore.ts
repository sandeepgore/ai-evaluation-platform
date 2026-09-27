import { create } from "zustand";

interface AppContextState {
    selectedOrganizationId: string | null;
    selectedProjectId: string | null;

    setSelectedOrganizationId: (organizationId: string | null) => void;
    setSelectedProjectId: (projectId: string | null) => void;
    clearProject: () => void;
}

export const useAppContextStore = create<AppContextState>((set) => ({
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
}));