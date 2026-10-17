import {
  AssessmentOutlined,
  AutoAwesomeOutlined,
  BusinessOutlined,
  DatasetOutlined,
  FolderOutlined,
  KeyboardArrowRightOutlined,
  MemoryOutlined,
  ScienceOutlined,
} from "@mui/icons-material";
import {
  alpha,
  Box,
  Card,
  CardActionArea,
  CardContent,
  Chip,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Typography,
  useTheme,
} from "@mui/material";
import { Link as RouterLink } from "react-router-dom";

import { AppBreadcrumbs } from "../../components/common/AppBreadcrumbs";
import { useAppContextStore } from "../../store/appContextStore";
import { useOrganizations } from "../organizations/hooks";
import { useProjects } from "../projects/hooks";
import { useDatasets } from "../datasets/hooks";
import { useModels } from "../models/hooks";
import { useEvaluationRuns } from "../evaluations/hooks";
import { useExperiments } from "../experiments/hooks";

export function DashboardPage() {
  const theme = useTheme();
  const {
    data: organizations = [],
    isLoading: isOrganizationsLoading,
  } = useOrganizations();

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

  const { data: projects = [], isLoading: isProjectsLoading } = useProjects(
    selectedOrganizationId,
  );
  const { data: datasets = [], isLoading: isDatasetsLoading } = useDatasets(
    selectedProjectId,
  );
  const { data: models = [], isLoading: isModelsLoading } = useModels(
    selectedProjectId,
  );
  const { data: evaluationRuns = [], isLoading: isEvaluationsLoading } =
    useEvaluationRuns({ projectId: selectedProjectId });
  const { data: experiments = [], isLoading: isExperimentsLoading } =
    useExperiments("all", selectedProjectId);
  const selectedOrganization = organizations.find(
    (organization) => organization.id === selectedOrganizationId,
  );
  const selectedProject = projects.find(
    (project) => project.id === selectedProjectId,
  );

  const panelBorder = alpha(
    theme.palette.text.primary,
    theme.palette.mode === "dark" ? 0.14 : 0.09,
  );
  const shortcuts = [
    {
      label: "Organizations",
      description: "Manage your organization workspaces.",
      to: "/organizations",
      icon: BusinessOutlined,
      color: "primary" as const,
      count: organizations.length,
      isLoading: isOrganizationsLoading,
    },
    {
      label: "Projects",
      description: "Manage projects in the selected organization.",
      to: "/projects",
      icon: FolderOutlined,
      color: "info" as const,
      count: selectedOrganizationId ? projects.length : null,
      isLoading: Boolean(selectedOrganizationId) && isProjectsLoading,
    },
    {
      label: "Datasets",
      description: "Manage datasets, versions, and test cases.",
      to: "/datasets",
      icon: DatasetOutlined,
      color: "success" as const,
      count: selectedProjectId ? datasets.length : null,
      isLoading: isDatasetsLoading,
    },
    {
      label: "Models",
      description: "Configure models used in evaluations.",
      to: "/models",
      icon: MemoryOutlined,
      color: "info" as const,
      count: selectedProjectId ? models.length : null,
      isLoading: isModelsLoading,
    },
    {
      label: "Evaluations",
      description: "Run evaluations and review model results.",
      to: "/evaluations",
      icon: AssessmentOutlined,
      color: "primary" as const,
      count: selectedProjectId ? evaluationRuns.length : null,
      isLoading: isEvaluationsLoading,
    },
    {
      label: "Experiments",
      description: "Compare evaluation runs and saved snapshots.",
      to: "/experiments",
      icon: ScienceOutlined,
      color: "warning" as const,
      count: selectedProjectId ? experiments.length : null,
      isLoading: isExperimentsLoading,
    },
  ];

  return (
    <Stack spacing={3} sx={{ pb: 4 }}>
      <AppBreadcrumbs items={[{ label: "Dashboard" }]} />

      <Stack spacing={0.75}>
        <Typography variant="h4" sx={{ fontWeight: 700, letterSpacing: -0.5 }}>
          Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Your workspace for managing datasets, models, and evaluations.
        </Typography>
      </Stack>

      <Card variant="outlined" sx={{ borderColor: panelBorder, borderRadius: 3 }}>
        <CardContent sx={{ p: { xs: 2, sm: 3 }, "&:last-child": { pb: { xs: 2, sm: 3 } } }}>
          <Stack spacing={2.5}>
            <Stack direction="row" spacing={1.5} alignItems="center">
              <Box
                sx={{
                  width: 42,
                  height: 42,
                  borderRadius: 2,
                  display: "grid",
                  placeItems: "center",
                  color: "primary.main",
                  bgcolor: alpha(theme.palette.primary.main, 0.1),
                }}
              >
                <BusinessOutlined />
              </Box>
              <Box>
                <Typography variant="h6" sx={{ fontWeight: 650 }}>
                  Workspace
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Choose the organization and project you want to work in.
                </Typography>
              </Box>
            </Stack>

            <Box
              sx={{
                display: "grid",
                gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))" },
                gap: 2,
              }}
            >
              <FormControl fullWidth>
                <InputLabel id="dashboard-organization-label">Organization</InputLabel>
                <Select
                  labelId="dashboard-organization-label"
                  value={selectedOrganizationId ?? ""}
                  label="Organization"
                  onChange={(event) => {
                    setSelectedOrganizationId(event.target.value || null);
                  }}
                  disabled={organizations.length === 0}
                >
                  {organizations.map((organization) => (
                    <MenuItem key={organization.id} value={organization.id}>
                      {organization.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <FormControl fullWidth>
                <InputLabel id="dashboard-project-label">Project</InputLabel>
                <Select
                  labelId="dashboard-project-label"
                  value={selectedProjectId ?? ""}
                  label="Project"
                  onChange={(event) => {
                    setSelectedProjectId(event.target.value || null);
                  }}
                  disabled={selectedOrganizationId === null || projects.length === 0}
                >
                  {projects.map((project) => (
                    <MenuItem key={project.id} value={project.id}>
                      {project.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>
          </Stack>
        </CardContent>
      </Card>

      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: { xs: "1fr", sm: "repeat(3, minmax(0, 1fr))" },
          gap: 2,
        }}
      >
        {[
          {
            label: "Organizations",
            value: organizations.length,
            detail: "Available to your account",
            icon: BusinessOutlined,
            color: theme.palette.primary.main,
          },
          {
            label: "Projects",
            value: projects.length,
            detail: selectedOrganization?.name ?? "Select an organization",
            icon: FolderOutlined,
            color: theme.palette.info.main,
          },
          {
            label: "Current project",
            value: selectedProject?.name ?? "Not selected",
            detail: selectedOrganization?.name ?? "Choose a workspace above",
            icon: AutoAwesomeOutlined,
            color: theme.palette.success.main,
          },
        ].map((item) => {
          const Icon = item.icon;
          return (
            <Card
              key={item.label}
              variant="outlined"
              sx={{ borderColor: panelBorder, borderRadius: 3, height: "100%" }}
            >
              <CardContent sx={{ p: 2.5 }}>
                <Stack direction="row" justifyContent="space-between" spacing={2}>
                  <Box sx={{ minWidth: 0 }}>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      {item.label}
                    </Typography>
                    <Typography
                      variant={typeof item.value === "number" ? "h4" : "h6"}
                      sx={{ fontWeight: 700, overflowWrap: "anywhere" }}
                    >
                      {item.value}
                    </Typography>
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      sx={{ display: "block", mt: 0.75, overflowWrap: "anywhere" }}
                    >
                      {item.detail}
                    </Typography>
                  </Box>
                  <Box
                    sx={{
                      flex: "0 0 auto",
                      width: 42,
                      height: 42,
                      borderRadius: 2,
                      display: "grid",
                      placeItems: "center",
                      color: item.color,
                      bgcolor: alpha(item.color, 0.1),
                    }}
                  >
                    <Icon />
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          );
        })}
      </Box>

      <Stack spacing={1.5}>
        <Box>
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            Quick access
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Jump to a part of your evaluation workflow.
          </Typography>
        </Box>

        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))", xl: "repeat(3, minmax(0, 1fr))" },
            gap: 2,
          }}
        >
          {shortcuts.map((shortcut) => {
            const Icon = shortcut.icon;
            return (
              <Card
                key={shortcut.label}
                variant="outlined"
                sx={{ borderColor: panelBorder, borderRadius: 3 }}
              >
                <CardActionArea
                  component={RouterLink}
                  to={shortcut.to}
                  sx={{ height: "100%" }}
                >
                  <CardContent sx={{ p: 2.5 }}>
                    <Stack direction="row" spacing={2} alignItems="center">
                      <Box
                        sx={{
                          flex: "0 0 auto",
                          width: 44,
                          height: 44,
                          borderRadius: 2,
                          display: "grid",
                          placeItems: "center",
                          color: `${shortcut.color}.main`,
                          bgcolor: alpha(theme.palette[shortcut.color].main, 0.1),
                        }}
                      >
                        <Icon />
                      </Box>
                      <Box sx={{ flex: 1, minWidth: 0 }}>
                        <Typography variant="subtitle1" sx={{ fontWeight: 650 }}>
                          {shortcut.label}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {shortcut.description}
                        </Typography>
                      </Box>
                    <Chip
                      size="small"
                      label={shortcut.isLoading ? "…" : shortcut.count ?? "—"}
                      aria-label={`${shortcut.label} count`}
                      variant="outlined"
                      sx={{ minWidth: 38, fontWeight: 650 }}
                    />
                      <KeyboardArrowRightOutlined color="action" />
                    </Stack>
                  </CardContent>
                </CardActionArea>
              </Card>
            );
          })}
        </Box>
      </Stack>
    </Stack>
  );
}
