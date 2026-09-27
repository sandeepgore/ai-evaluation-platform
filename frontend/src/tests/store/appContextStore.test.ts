import { beforeEach, describe, expect, it } from "vitest";
import { useAppContextStore } from "../../store/appContextStore";

describe("appContextStore", () => {
    beforeEach(() => {
        useAppContextStore.setState({
            selectedOrganizationId: null,
            selectedProjectId: null,
        });
    });

    it("starts with no selected organization or project", () => {
        const state = useAppContextStore.getState();

        expect(state.selectedOrganizationId).toBeNull();
        expect(state.selectedProjectId).toBeNull();
    });

    it("sets the selected organization", () => {
        useAppContextStore
            .getState()
            .setSelectedOrganizationId("org-1");

        expect(
            useAppContextStore.getState().selectedOrganizationId,
        ).toBe("org-1");
    });

    it("clears the selected project when organization changes", () => {
        useAppContextStore.setState({
            selectedOrganizationId: "org-1",
            selectedProjectId: "project-1",
        });

        useAppContextStore
            .getState()
            .setSelectedOrganizationId("org-2");

        const state = useAppContextStore.getState();

        expect(state.selectedOrganizationId).toBe("org-2");
        expect(state.selectedProjectId).toBeNull();
    });

    it("sets the selected project", () => {
        useAppContextStore
            .getState()
            .setSelectedProjectId("project-1");

        expect(
            useAppContextStore.getState().selectedProjectId,
        ).toBe("project-1");
    });

    it("clears the selected project", () => {
        useAppContextStore.setState({
            selectedOrganizationId: "org-1",
            selectedProjectId: "project-1",
        });

        useAppContextStore.getState().clearProject();

        expect(
            useAppContextStore.getState().selectedProjectId,
        ).toBeNull();
    });
});