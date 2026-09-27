import { useEffect } from "react";
import { useOrganizations } from "../../features/organizations/hooks";
import { useAppContextStore } from "../../store/appContextStore";

export function OrganizationContextInitializer() {
    const { data: organizations } = useOrganizations();
    const selectedOrganizationId = useAppContextStore(
        (state) => state.selectedOrganizationId,
    );
    const setSelectedOrganizationId = useAppContextStore(
        (state) => state.setSelectedOrganizationId,
    );

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

    return null;
}