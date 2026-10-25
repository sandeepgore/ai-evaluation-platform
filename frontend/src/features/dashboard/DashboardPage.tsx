import {
  AssessmentOutlined,
  BusinessOutlined,
  DatasetOutlined,
  FolderOutlined,
  KeyboardArrowRightOutlined,
  MemoryOutlined,
  ScienceOutlined,
} from "@mui/icons-material";
import {
  alpha,
  Button,
  Box,
  Card,
  CardActionArea,
  CardContent,
  Chip,
  FormControl,
  InputLabel,
  LinearProgress,
  MenuItem,
  Select,
  Stack,
  Typography,
  useTheme,
} from "@mui/material";
import { useQueries } from "@tanstack/react-query";
import { Link as RouterLink } from "react-router-dom";

import { useAppContextStore } from "../../store/appContextStore";
import { useOrganizations } from "../organizations/hooks";
import { useProjects } from "../projects/hooks";
import { useDatasets } from "../datasets/hooks";
import { listDatasetVersions } from "../datasetVersions/api";
import { useModels } from "../models/hooks";
import { useEvaluationRuns } from "../evaluations/hooks";
import { useExperiments } from "../experiments/hooks";
import { EvaluationCharts } from "./EvaluationCharts";
import { StatusChip } from "../../components/common/StatusChip";

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
  const datasetVersionQueries = useQueries({
    queries: datasets.map((dataset) => ({
      queryKey: ["datasetVersions", "list", dataset.id],
      queryFn: () => listDatasetVersions(dataset.id),
      enabled: Boolean(selectedProjectId),
    })),
  });
  const { data: models = [], isLoading: isModelsLoading } = useModels(
    selectedProjectId,
  );
  const { data: evaluationRuns = [], isLoading: isEvaluationsLoading } =
    useEvaluationRuns({ projectId: selectedProjectId });
  const { data: experiments = [], isLoading: isExperimentsLoading } =
    useExperiments("all", selectedProjectId);
  const selectedProject = projects.find(
    (project) => project.id === selectedProjectId,
  );
  const completedRuns = evaluationRuns.filter((run) => run.status === "completed").length;
  const processedCases = evaluationRuns.reduce(
    (total, run) => total + run.completed_cases + run.failed_cases + run.not_applicable_cases,
    0,
  );
  const totalCases = evaluationRuns.reduce((total, run) => total + run.total_cases, 0);
  const failedCases = evaluationRuns.reduce((total, run) => total + run.failed_cases, 0);
  const caseProgress = totalCases > 0 ? Math.min(100, (processedCases / totalCases) * 100) : 0;
  const activeDatasetVersions = datasetVersionQueries.flatMap((query) => query.data ?? []);
  const isDatasetInventoryLoading = isDatasetsLoading || datasetVersionQueries.some((query) => query.isLoading);
  const hasDatasetInventoryError = datasetVersionQueries.some((query) => query.isError);
  const activeVersionCaseCount = activeDatasetVersions
    .filter((version) => version.is_active)
    .reduce((total, version) => total + version.case_count, 0);
  const recentRuns = [...evaluationRuns]
    .sort((left, right) => new Date(right.created_at).getTime() - new Date(left.created_at).getTime())
    .slice(0, 5);
  const recentExperiments = [...experiments]
    .sort((left, right) => new Date(right.created_at).getTime() - new Date(left.created_at).getTime())
    .slice(0, 4);
  const activeExperimentCount = experiments.filter((experiment) => experiment.is_active).length;
  const modelNames = Object.fromEntries(models.map((model) => [model.id, model.name]));

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
      <Stack spacing={0.75}>
        <Typography variant="h4" sx={{ fontWeight: 700, letterSpacing: -0.5 }}>
          Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Track evaluation runs, dataset coverage, models, and experiment comparisons for your project.
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

      <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))", xl: "repeat(4, minmax(0, 1fr))" }, gap: 2 }}>
        {[
          { label: "Evaluation runs", value: isEvaluationsLoading ? "…" : selectedProjectId ? evaluationRuns.length : "—", detail: selectedProject?.name ?? "Select a project", progress: null as number | null },
          { label: "Completed runs", value: isEvaluationsLoading ? "…" : selectedProjectId ? completedRuns : "—", detail: selectedProjectId ? "Finished evaluations" : "Select a project", progress: null as number | null },
          { label: "Cases processed", value: isEvaluationsLoading ? "…" : selectedProjectId ? `${processedCases} / ${totalCases}` : "—", detail: selectedProjectId ? `${caseProgress.toFixed(0)}% of all run cases` : "Select a project", progress: caseProgress },
          { label: "Failed cases", value: isEvaluationsLoading ? "…" : selectedProjectId ? failedCases : "—", detail: selectedProjectId ? "Across evaluation runs" : "Select a project", progress: null as number | null },
        ].map((item) => (
          <Card key={item.label} variant="outlined" sx={{ borderColor: panelBorder, borderRadius: 3, minWidth: 0, height: "100%" }}>
            <CardContent sx={{ p: 2.5, "&:last-child": { pb: 2.5 } }}>
              <Typography variant="body2" color="text.secondary">{item.label}</Typography>
              <Typography variant="h4" sx={{ fontWeight: 700, mt: 0.75, overflowWrap: "anywhere" }}>{item.value}</Typography>
              <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 0.75 }}>{item.detail}</Typography>
              {item.progress !== null && <LinearProgress variant="determinate" value={selectedProjectId && !isEvaluationsLoading ? item.progress : 0} sx={{ mt: 1.5, height: 6, borderRadius: 3 }} />}
            </CardContent>
          </Card>
        ))}
      </Box>

      <Stack spacing={1.5}>
        <Box>
          <Typography variant="h6" fontWeight={700}>Datasets and models</Typography>
          <Typography variant="body2" color="text.secondary">
            Inventory and test case coverage for {selectedProject?.name ?? "the selected project"}.
          </Typography>
        </Box>
        <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))", xl: "repeat(4, minmax(0, 1fr))" }, gap: 2 }}>
          {[
            { label: "Datasets", value: isDatasetsLoading ? "…" : selectedProjectId ? datasets.filter((dataset) => dataset.is_active).length : "—", detail: "Active datasets" },
            { label: "Dataset versions", value: isDatasetInventoryLoading ? "…" : hasDatasetInventoryError ? "—" : selectedProjectId ? activeDatasetVersions.filter((version) => version.is_active).length : "—", detail: hasDatasetInventoryError ? "Version summary unavailable" : "Active versions" },
            { label: "Dataset cases", value: isDatasetInventoryLoading ? "…" : hasDatasetInventoryError ? "—" : selectedProjectId ? activeVersionCaseCount : "—", detail: "Cases in active versions" },
            { label: "Models", value: isModelsLoading ? "…" : selectedProjectId ? models.filter((model) => model.is_active).length : "—", detail: "Active model configurations" },
          ].map((item) => (
            <Card key={item.label} variant="outlined" sx={{ borderColor: panelBorder, borderRadius: 3, minWidth: 0, height: "100%" }}>
              <CardContent sx={{ p: 2.5, "&:last-child": { pb: 2.5 } }}>
                <Typography variant="body2" color="text.secondary">{item.label}</Typography>
                <Typography variant="h4" sx={{ mt: 0.75, fontWeight: 700 }}>{item.value}</Typography>
                <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 0.75 }}>{item.detail}</Typography>
              </CardContent>
            </Card>
          ))}
        </Box>
      </Stack>

      <EvaluationCharts runs={evaluationRuns} projectSelected={Boolean(selectedProjectId)} />

      <Card variant="outlined" sx={{ borderColor: panelBorder, borderRadius: 3, overflow: "hidden" }}>
        <CardContent sx={{ p: 0 }}>
          <Stack direction={{ xs: "column", sm: "row" }} spacing={1} justifyContent="space-between" alignItems={{ sm: "center" }} sx={{ p: 2.5, borderBottom: 1, borderColor: "divider" }}>
            <Box>
              <Typography variant="h6" fontWeight={700}>Recent evaluation runs</Typography>
              <Typography variant="body2" color="text.secondary">Latest activity in {selectedProject?.name ?? "the selected project"}.</Typography>
            </Box>
            <Stack direction="row" spacing={1} alignItems="center">
              <Chip size="small" variant="outlined" label={selectedProjectId ? `${evaluationRuns.length} total` : "No project selected"} />
              {selectedProjectId && <Button component={RouterLink} to="/evaluations" size="small" endIcon={<KeyboardArrowRightOutlined />}>View all</Button>}
            </Stack>
          </Stack>
          {!selectedProjectId ? (
            <Typography variant="body2" color="text.secondary" sx={{ p: 2.5 }}>Select a project to see its recent evaluations.</Typography>
          ) : isEvaluationsLoading ? (
            <Typography variant="body2" color="text.secondary" sx={{ p: 2.5 }}>Loading recent evaluations…</Typography>
          ) : recentRuns.length === 0 ? (
            <Typography variant="body2" color="text.secondary" sx={{ p: 2.5 }}>No evaluation runs have been created for this project yet.</Typography>
          ) : (
            <Stack>
              {recentRuns.map((run, index) => (
                <Box key={run.id} component={RouterLink} to={`/evaluations/${run.id}`} sx={{ display: "flex", flexDirection: { xs: "column", sm: "row" }, gap: 1.5, alignItems: { sm: "center" }, justifyContent: "space-between", px: 2.5, py: 1.75, borderBottom: index < recentRuns.length - 1 ? 1 : 0, borderColor: "divider", color: "inherit", textDecoration: "none", transition: "background-color 120ms ease", "&:hover": { bgcolor: "action.hover" } }}>
                  <Box sx={{ minWidth: 0, flex: 1 }}>
                    <Typography variant="body2" fontWeight={650} noWrap title={run.name}>{run.name}</Typography>
                    <Typography variant="caption" color="text.secondary" noWrap>
                      {modelNames[run.model_id] ?? "Unknown model"} · {run.evaluation_type.toUpperCase()} · {new Date(run.created_at).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" })}
                    </Typography>
                  </Box>
                  <Stack direction="row" spacing={1.5} useFlexGap flexWrap="wrap" alignItems="center">
                    <Typography variant="caption" color="text.secondary">{run.completed_cases + run.failed_cases + run.not_applicable_cases} / {run.total_cases} cases processed</Typography>
                    <StatusChip status={run.status} />
                  </Stack>
                </Box>
              ))}
            </Stack>
          )}
        </CardContent>
      </Card>

      <Card variant="outlined" sx={{ borderColor: panelBorder, borderRadius: 3, overflow: "hidden" }}>
        <CardContent sx={{ p: 0 }}>
          <Stack direction={{ xs: "column", sm: "row" }} spacing={1} justifyContent="space-between" alignItems={{ sm: "center" }} sx={{ p: 2.5, borderBottom: 1, borderColor: "divider" }}>
            <Box>
              <Typography variant="h6" fontWeight={700}>Recent experiments</Typography>
              <Typography variant="body2" color="text.secondary">
                {selectedProject ? `Comparisons in ${selectedProject.name}` : "Experiment workspaces for the selected project"}
              </Typography>
            </Box>
            <Stack direction="row" spacing={1} alignItems="center">
              <Chip size="small" variant="outlined" label={selectedProjectId ? `${activeExperimentCount} active · ${experiments.length} total` : "No project selected"} />
              {selectedProjectId && <Button component={RouterLink} to="/experiments" size="small" endIcon={<KeyboardArrowRightOutlined />}>View all</Button>}
            </Stack>
          </Stack>
          {!selectedProjectId ? (
            <Typography variant="body2" color="text.secondary" sx={{ p: 2.5 }}>Select a project to see its experiments.</Typography>
          ) : isExperimentsLoading ? (
            <Typography variant="body2" color="text.secondary" sx={{ p: 2.5 }}>Loading experiments…</Typography>
          ) : recentExperiments.length === 0 ? (
            <Typography variant="body2" color="text.secondary" sx={{ p: 2.5 }}>No experiments have been created for this project yet.</Typography>
          ) : (
            <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))", lg: "repeat(4, minmax(0, 1fr))" }, gap: 1.5, p: 2 }}>
              {recentExperiments.map((experiment) => (
                <Card key={experiment.id} variant="outlined" sx={{ borderRadius: 2, minWidth: 0, height: "100%" }}>
                  <CardActionArea component={RouterLink} to={`/experiments/${experiment.id}`} sx={{ height: "100%" }}>
                    <CardContent sx={{ p: 2, "&:last-child": { pb: 2 } }}>
                      <Stack spacing={1.25} sx={{ height: "100%" }}>
                        <Stack direction="row" spacing={1} alignItems="flex-start" justifyContent="space-between">
                          <Typography variant="subtitle2" fontWeight={700} sx={{ minWidth: 0, overflowWrap: "anywhere" }}>{experiment.name}</Typography>
                          <StatusChip active={experiment.is_active} />
                        </Stack>
                        <Typography variant="body2" color="text.secondary" sx={{ minHeight: 40, overflow: "hidden", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical" }}>
                          {experiment.description || "No description provided."}
                        </Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ mt: "auto" }}>
                          Created {new Date(experiment.created_at).toLocaleDateString(undefined, { dateStyle: "medium" })}
                        </Typography>
                      </Stack>
                    </CardContent>
                  </CardActionArea>
                </Card>
              ))}
            </Box>
          )}
        </CardContent>
      </Card>

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
