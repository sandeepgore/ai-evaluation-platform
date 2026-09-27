import {
    Card,
    CardContent,
    FormControl,
    InputLabel,
    MenuItem,
    Select,
    Stack,
    Typography,
} from "@mui/material";
import { useOrganizations } from "../organizations/hooks";
import { useAppContextStore } from "../../store/appContextStore";

export function DashboardPage() {
    const { data: organizations = [] } = useOrganizations();

    const selectedOrganizationId = useAppContextStore(
        (state) => state.selectedOrganizationId,
    );
    const setSelectedOrganizationId = useAppContextStore(
        (state) => state.setSelectedOrganizationId,
    );

    return (
        <Stack spacing={3}>
            <Stack spacing={0.5}>
                <Typography variant="h5" sx={{ fontWeight: 700 }}>
                    Dashboard
                </Typography>

                <Typography variant="body2" color="text.secondary">
                    Overview of your AI evaluation workspace.
                </Typography>
            </Stack>

            <Card>
                <CardContent>
                    <Stack spacing={2}>
                        <Typography variant="h6">
                            Organization Context
                        </Typography>

                        <FormControl fullWidth>
                            <InputLabel id="dashboard-organization-label">
                                Organization
                            </InputLabel>

                            <Select
                                labelId="dashboard-organization-label"
                                value={selectedOrganizationId ?? ""}
                                label="Organization"
                                onChange={(event) => {
                                    setSelectedOrganizationId(
                                        event.target.value || null,
                                    );
                                }}
                                disabled={organizations.length === 0}
                            >
                                {organizations.map((organization) => (
                                    <MenuItem
                                        key={organization.id}
                                        value={organization.id}
                                    >
                                        {organization.name}
                                    </MenuItem>
                                ))}
                            </Select>
                        </FormControl>
                    </Stack>
                </CardContent>
            </Card>
        </Stack>
    );
}