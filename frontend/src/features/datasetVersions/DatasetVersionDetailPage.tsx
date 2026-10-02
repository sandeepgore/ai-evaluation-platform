import {
  CheckCircleOutlined,
  DataObjectOutlined,
  DatasetOutlined,
  HelpOutlined,
  ListAltOutlined,
} from "@mui/icons-material";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Divider,
  Grid,
  LinearProgress,
  Stack,
  Tooltip,
  Typography,
} from "@mui/material";
import { useNavigate, useParams } from "react-router-dom";
import { AppBreadcrumbs } from "../../components/common/AppBreadcrumbs";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import { useDataset } from "../datasets/hooks";
import { DatasetVersionStatusChip } from "./DatasetVersionStatusChip";
import { useDatasetVersion } from "./hooks";

export function DatasetVersionDetailPage() {
  const navigate = useNavigate();

  const { datasetId, versionId } = useParams<{
    datasetId: string;
    versionId: string;
  }>();

  const { data, isLoading, isError } = useDatasetVersion(versionId ?? null);
  const { data: dataset } = useDataset(datasetId ?? null);

  if (!versionId || !datasetId) {
    return <ErrorState message="Dataset version ID is missing." />;
  }

  if (isLoading) {
    return <LoadingState message="Loading dataset version..." />;
  }

  if (isError || !data) {
    return <ErrorState message="Unable to load dataset version." />;
  }

  const analytics = data.analytics;
  const totalCases = data.case_count;
  const isFinalized = data.status !== "draft";

  const referenceCount = analytics?.reference_count ?? 0;
  const contextCount = analytics?.context_count ?? 0;

  const referenceCoverage = analytics?.reference_coverage ?? 0;
  const contextCoverage = analytics?.context_coverage ?? 0;

  const hasEvaluationData = totalCases > 0;

  return (
    <Stack spacing={3}>
      <AppBreadcrumbs
        items={[
          {
            label: "Datasets",
            to: "/datasets",
          },
          {
            label: dataset?.name ?? "Dataset",
          },
          {
            label: "Versions",
            to: `/datasets/${datasetId}/versions`,
          },
          {
            label: `Version v${data.version}`,
          },
        ]}
      />

      {/* Header */}
      <Stack
        direction={{ xs: "column", sm: "row" }}
        spacing={2}
        sx={{
          justifyContent: "space-between",
          alignItems: { xs: "flex-start", sm: "center" },
        }}
      >
        <Stack direction="row" spacing={1.5} sx={{ alignItems: "flex-start" }}>
          <Box
            sx={{
              mt: 0.25,
              width: 40,
              height: 40,
              borderRadius: 2,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              bgcolor: "rgba(79, 70, 229, 0.08)",
              color: "primary.main",
              flexShrink: 0,
            }}
          >
            <DatasetOutlined />
          </Box>

          <Stack spacing={0.5}>
            <Typography variant="h5">
              Dataset Version v{data.version}
            </Typography>

            <Typography variant="body2" color="text.secondary">
              {data.description ?? "No description"}
            </Typography>
          </Stack>
        </Stack>

        <DatasetVersionStatusChip status={data.status} />
      </Stack>

      {/* Overview */}
      <Stack spacing={1.5}>
        <Stack direction="row" spacing={0.75} sx={{ alignItems: "center" }}>
          <Typography variant="h6">Overview</Typography>

          <Tooltip title="A summary of the evaluation data contained in this dataset version.">
            <HelpOutlined
              sx={{
                fontSize: 17,
                color: "text.disabled",
                cursor: "help",
              }}
            />
          </Tooltip>
        </Stack>

        {!isFinalized && (
          <Alert severity="info">
            <Typography variant="body2">
              <strong>Analytics are not available yet.</strong> This dataset
              version is still in Draft status. Finalize the version to generate
              and view reference and context analytics.
            </Typography>
          </Alert>
        )}

        <Grid container spacing={2}>
          <Grid size={{ xs: 12, md: isFinalized ? 4 : 12 }}>
            <Card sx={{ height: "100%" }}>
              <CardContent>
                <Stack spacing={1}>
                  <Stack
                    direction="row"
                    spacing={0.5}
                    sx={{ alignItems: "center" }}
                  >
                    <ListAltOutlined
                      sx={{ color: "text.secondary", fontSize: 21 }}
                    />

                    <Typography variant="body2" color="text.secondary">
                      Total Cases
                    </Typography>

                    <Tooltip title="The total number of evaluation scenarios contained in this dataset version.">
                      <HelpOutlined
                        sx={{
                          ml: "auto",
                          fontSize: 16,
                          color: "text.disabled",
                          cursor: "help",
                        }}
                      />
                    </Tooltip>
                  </Stack>

                  <Typography variant="h4">{totalCases}</Typography>

                  <Typography variant="body2" color="text.secondary">
                    Evaluation scenarios
                  </Typography>
                </Stack>
              </CardContent>
            </Card>
          </Grid>

          {isFinalized && (
            <>
              <Grid size={{ xs: 12, md: 4 }}>
                <Card sx={{ height: "100%" }}>
                  <CardContent>
                    <Stack spacing={1}>
                      <Stack
                        direction="row"
                        spacing={0.5}
                        sx={{ alignItems: "center" }}
                      >
                        <CheckCircleOutlined
                          sx={{ color: "text.secondary", fontSize: 21 }}
                        />

                        <Typography variant="body2" color="text.secondary">
                          Reference Data
                        </Typography>

                        <Tooltip title="Cases that contain an expected output or reference answer that can be used by evaluators.">
                          <HelpOutlined
                            sx={{
                              ml: "auto",
                              fontSize: 16,
                              color: "text.disabled",
                              cursor: "help",
                            }}
                          />
                        </Tooltip>
                      </Stack>

                      <Typography variant="h4">{referenceCount}</Typography>

                      <Typography variant="body2" color="text.secondary">
                        of {totalCases} cases
                      </Typography>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>

              <Grid size={{ xs: 12, md: 4 }}>
                <Card sx={{ height: "100%" }}>
                  <CardContent>
                    <Stack spacing={1}>
                      <Stack
                        direction="row"
                        spacing={0.5}
                        sx={{ alignItems: "center" }}
                      >
                        <DataObjectOutlined
                          sx={{ color: "text.secondary", fontSize: 21 }}
                        />

                        <Typography variant="body2" color="text.secondary">
                          Context Data
                        </Typography>

                        <Tooltip title="Cases that contain contextual information that can be used when evaluating context-dependent or RAG systems.">
                          <HelpOutlined
                            sx={{
                              ml: "auto",
                              fontSize: 16,
                              color: "text.disabled",
                              cursor: "help",
                            }}
                          />
                        </Tooltip>
                      </Stack>

                      <Typography variant="h4">{contextCount}</Typography>

                      <Typography variant="body2" color="text.secondary">
                        of {totalCases} cases
                      </Typography>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            </>
          )}
        </Grid>
      </Stack>

      {/* Evaluation Data */}
      <Card>
        <CardContent>
          <Stack spacing={2.5}>
            <Stack spacing={0.5}>
              <Stack
                direction="row"
                spacing={0.5}
                sx={{ alignItems: "center" }}
              >
                {hasEvaluationData ? (
                  <CheckCircleOutlined
                    sx={{ color: "success.main", fontSize: 22 }}
                  />
                ) : (
                  <DatasetOutlined
                    sx={{ color: "text.secondary", fontSize: 22 }}
                  />
                )}

                <Typography variant="h6">Evaluation Data</Typography>

                <Tooltip title="This section describes which types of data are available for evaluators when this dataset version is used.">
                  <HelpOutlined
                    sx={{
                      fontSize: 17,
                      color: "text.disabled",
                      cursor: "help",
                    }}
                  />
                </Tooltip>
              </Stack>

              <Typography variant="body2" color="text.secondary">
                {hasEvaluationData
                  ? "This version contains evaluation cases that can be used when running an evaluation."
                  : "This version does not contain any evaluation cases yet."}
              </Typography>
            </Stack>

            <Divider />

            <Grid container spacing={3}>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Stack spacing={0.75}>
                  <Typography variant="body2" color="text.secondary">
                    Input
                  </Typography>

                  <Typography variant="body1" sx={{ fontWeight: 600 }}>
                    {hasEvaluationData ? "Available" : "No cases"}
                  </Typography>

                  <Typography variant="caption" color="text.secondary">
                    Every evaluation case provides the input sent to the system.
                  </Typography>
                </Stack>
              </Grid>

              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Stack spacing={0.75}>
                  <Stack
                    direction="row"
                    spacing={0.5}
                    sx={{ alignItems: "center" }}
                  >
                    <Typography variant="body2" color="text.secondary">
                      Expected Output
                    </Typography>

                    <Tooltip title="The expected or reference answer associated with an evaluation case.">
                      <HelpOutlined
                        sx={{
                          fontSize: 15,
                          color: "text.disabled",
                          cursor: "help",
                        }}
                      />
                    </Tooltip>
                  </Stack>

                  <Typography variant="body1" sx={{ fontWeight: 600 }}>
                    {hasEvaluationData
                      ? `${referenceCount} / ${totalCases}`
                      : "No cases"}
                  </Typography>

                  <Typography variant="caption" color="text.secondary">
                    Cases with a reference answer.
                  </Typography>
                </Stack>
              </Grid>

              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Stack spacing={0.75}>
                  <Stack
                    direction="row"
                    spacing={0.5}
                    sx={{ alignItems: "center" }}
                  >
                    <Typography variant="body2" color="text.secondary">
                      Reference Coverage
                    </Typography>

                    <Tooltip title="The percentage of cases that contain an expected output or reference answer.">
                      <HelpOutlined
                        sx={{
                          fontSize: 15,
                          color: "text.disabled",
                          cursor: "help",
                        }}
                      />
                    </Tooltip>
                  </Stack>

                  <Typography variant="body1" sx={{ fontWeight: 600 }}>
                    {hasEvaluationData && analytics
                      ? `${(referenceCoverage * 100).toFixed(1)}%`
                      : "—"}
                  </Typography>

                  {hasEvaluationData && analytics && (
                    <LinearProgress
                      variant="determinate"
                      value={referenceCoverage * 100}
                      sx={{
                        height: 6,
                        borderRadius: 3,
                      }}
                    />
                  )}
                </Stack>
              </Grid>

              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Stack spacing={0.75}>
                  <Stack
                    direction="row"
                    spacing={0.5}
                    sx={{ alignItems: "center" }}
                  >
                    <Typography variant="body2" color="text.secondary">
                      Context Coverage
                    </Typography>

                    <Tooltip title="The percentage of cases that contain contextual information. This is especially relevant for RAG and context-dependent evaluations.">
                      <HelpOutlined
                        sx={{
                          fontSize: 15,
                          color: "text.disabled",
                          cursor: "help",
                        }}
                      />
                    </Tooltip>
                  </Stack>

                  <Typography variant="body1" sx={{ fontWeight: 600 }}>
                    {hasEvaluationData && analytics
                      ? `${(contextCoverage * 100).toFixed(1)}%`
                      : "—"}
                  </Typography>

                  {hasEvaluationData && analytics && (
                    <LinearProgress
                      variant="determinate"
                      value={contextCoverage * 100}
                      sx={{
                        height: 6,
                        borderRadius: 3,
                      }}
                    />
                  )}
                </Stack>
              </Grid>
            </Grid>
          </Stack>
        </CardContent>
      </Card>

      {/* Cases */}
      <Card>
        <CardContent>
          <Stack
            direction={{ xs: "column", sm: "row" }}
            spacing={2}
            sx={{
              alignItems: { xs: "stretch", sm: "center" },
              justifyContent: "space-between",
            }}
          >
            <Stack spacing={0.75}>
              <Stack
                direction="row"
                spacing={0.5}
                sx={{ alignItems: "center" }}
              >
                <ListAltOutlined
                  sx={{ color: "text.secondary", fontSize: 22 }}
                />

                <Typography variant="h6">Cases</Typography>

                <Tooltip title="Individual evaluation scenarios contained in this dataset version.">
                  <HelpOutlined
                    sx={{
                      fontSize: 17,
                      color: "text.disabled",
                      cursor: "help",
                    }}
                  />
                </Tooltip>
              </Stack>

              <Typography variant="body2" color="text.secondary">
                Inspect the individual inputs, expected outputs, context, and
                other case data.
              </Typography>
            </Stack>

            <Button
              variant="outlined"
              startIcon={<ListAltOutlined />}
              onClick={() =>
                navigate(`/datasets/${datasetId}/versions/${versionId}/cases`)
              }
            >
              View Cases
            </Button>
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  );
}
