import { useEffect } from "react";
import { useOrganizations } from "../../features/organizations/hooks";
import { useProjects } from "../../features/projects/hooks";
import { useAppContextStore } from "../../store/appContextStore";

export function OrganizationContextInitializer() {
    const { data: organizations } = useOrganizations();

    const selectedOrganizationId = useAppContextStore(
        (state) => state.selectedOrganizationId,
    );
    const selectedProjectId = useAppContextStore(
        (state) => state.selectedProjectId,
    );

    const setSelectedOrganizationId = useAppContextStore(
        (state) => state.setSelectedOrganizationId,
    );
    const setSelectedProjectId = useAppContextStore(
        (state) => state.setSelectedProjectId,
    );

    const { data: projects } = useProjects(selectedOrganizationId);

    useEffect(() => {
        if (
            selectedOrganizationId === null &&
            organizations &&
            organizations.length > 0
        ) {
            setSelectedOrganizationId(organizations[0].id);
        }
    }, [
        organizations,
        selectedOrganizationId,
        setSelectedOrganizationId,
    ]);

    useEffect(() => {
        if (
            selectedOrganizationId !== null &&
            selectedProjectId === null &&
            projects &&
            projects.length > 0
        ) {
            setSelectedProjectId(projects[0].id);
        }
    }, [
        projects,
        selectedOrganizationId,
        selectedProjectId,
        setSelectedProjectId,
    ]);

    return null;
}
