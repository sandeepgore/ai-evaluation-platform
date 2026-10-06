import React from "react";
import {
  CheckCircleOutlined,
  DataObjectOutlined,
  DatasetOutlined,
  HelpOutlined,
  ListAltOutlined,
  ArrowBackOutlined,
  InfoOutlined,
  CheckCircle,
  WarningAmber,
} from "@mui/icons-material";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  Grid,
  LinearProgress,
  Paper,
  Stack,
  Tooltip,
  Typography,
  alpha,
  useTheme,
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
  const theme = useTheme();

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
    return <LoadingState message="Loading dataset version details..." />;
  }

  if (isError || !data) {
    return <ErrorState message="Unable to load dataset version details." />;
  }

  const analytics = data.analytics;
  const totalCases = data.case_count ?? 0;
  const isFinalized = data.status !== "draft";

  const referenceCount = analytics?.reference_count ?? 0;
  const contextCount = analytics?.context_count ?? 0;

  // Safe fallback coverage calculations
  const referenceCoverage =
    analytics?.reference_coverage ??
    (totalCases > 0 ? referenceCount / totalCases : 0);
  const contextCoverage =
    analytics?.context_coverage ??
    (totalCases > 0 ? contextCount / totalCases : 0);

  const hasEvaluationData = totalCases > 0;

  return (
    <Stack spacing={3.5} sx={{ pb: 4 }}>
      {/* Breadcrumb Navigation */}
      <AppBreadcrumbs
        items={[
          { label: "Datasets", to: "/datasets" },
          { label: dataset?.name ?? "Dataset" },
          { label: "Versions", to: `/datasets/${datasetId}/versions` },
          { label: `Version v${data.version}` },
        ]}
      />

      {/* Hero Header */}
      <Paper
        elevation={0}
        sx={{
          p: { xs: 2.5, sm: 3.5 },
          borderRadius: 3,
          border: "1px solid",
          borderColor: "divider",
          background: (theme) =>
            theme.palette.mode === "dark"
              ? `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.08)} 0%, ${alpha(
                  theme.palette.background.paper,
                  0.4,
                )} 100%)`
              : `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.03)} 0%, #FFFFFF 100%)`,
        }}
      >
        <Stack
          direction={{ xs: "column", md: "row" }}
          spacing={2.5}
          sx={{
            justifyContent: "space-between",
            alignItems: { xs: "flex-start", md: "center" },
          }}
        >
          <Stack direction="row" spacing={2.5} sx={{ alignItems: "center" }}>
            <Box
              sx={{
                width: 56,
                height: 56,
                borderRadius: 2.5,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                bgcolor: alpha(theme.palette.primary.main, 0.1),
                color: "primary.main",
                boxShadow: `0 0 0 1px ${alpha(theme.palette.primary.main, 0.2)}`,
                flexShrink: 0,
              }}
            >
              <DatasetOutlined sx={{ fontSize: 28 }} />
            </Box>

            <Stack spacing={0.75}>
              <Stack
                direction="row"
                spacing={1.5}
                sx={{ alignItems: "center" }}
              >
                <Typography
                  variant="h5"
                  sx={{ fontWeight: 700, letterSpacing: "-0.01em" }}
                >
                  Version {data.version}
                </Typography>
                <DatasetVersionStatusChip status={data.status} />
              </Stack>

              <Typography
                variant="body2"
                color="text.secondary"
                sx={{ maxWidth: 640 }}
              >
                {data.description ||
                  "No specific version release notes or description provided."}
              </Typography>
            </Stack>
          </Stack>

          <Stack
            direction="row"
            spacing={1.5}
            sx={{
              width: { xs: "100%", md: "auto" },
              justifyContent: { xs: "flex-start", md: "flex-end" },
            }}
          >
            <Button
              variant="outlined"
              color="inherit"
              startIcon={<ArrowBackOutlined fontSize="small" />}
              onClick={() => navigate(`/datasets/${datasetId}/versions`)}
              sx={{
                borderRadius: 2,
                textTransform: "none",
                fontWeight: 600,
                borderColor: "divider",
              }}
            >
              Back
            </Button>
            <Button
              variant="contained"
              disableElevation
              startIcon={<ListAltOutlined fontSize="small" />}
              onClick={() =>
                navigate(`/datasets/${datasetId}/versions/${versionId}/cases`)
              }
              sx={{
                borderRadius: 2,
                textTransform: "none",
                fontWeight: 600,
                px: 2.5,
              }}
            >
              View Cases
            </Button>
          </Stack>
        </Stack>
      </Paper>

      {/* Analytics Summary */}
      <Stack spacing={2}>
        <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
          <Typography variant="h6" sx={{ fontWeight: 700, fontSize: "1.1rem" }}>
            Overview Metrics
          </Typography>
          <Tooltip title="Core counts and data point availability across all scenarios in this version.">
            <HelpOutlined
              sx={{ fontSize: 16, color: "text.disabled", cursor: "help" }}
            />
          </Tooltip>
        </Stack>

        {!isFinalized && (
          <Alert
            severity="info"
            icon={<InfoOutlined fontSize="small" />}
            sx={{
              borderRadius: 2,
              border: "1px solid",
              borderColor: alpha(theme.palette.info.main, 0.2),
            }}
          >
            <Typography variant="body2">
              <strong>Draft Version:</strong> Complete context and reference
              analytics will automatically calculate once this version is
              finalized.
            </Typography>
          </Alert>
        )}

        <Grid container spacing={2.5}>
          {/* Total Cases Card */}
          <Grid size={{ xs: 12, md: isFinalized ? 4 : 12 }}>
            <Card
              variant="outlined"
              sx={{
                height: "100%",
                borderRadius: 2.5,
                transition: "border-color 0.2s",
                "&:hover": { borderColor: "text.secondary" },
              }}
            >
              <CardContent sx={{ p: 2.5 }}>
                <Stack spacing={1.5}>
                  <Stack
                    direction="row"
                    sx={{
                      alignItems: "center",
                      justifyContent: "space-between",
                    }}
                  >
                    <Stack
                      direction="row"
                      spacing={1}
                      sx={{ alignItems: "center" }}
                    >
                      <Box
                        sx={{
                          p: 0.75,
                          borderRadius: 1.5,
                          bgcolor: alpha(theme.palette.primary.main, 0.1),
                          color: "primary.main",
                          display: "flex",
                        }}
                      >
                        <ListAltOutlined fontSize="small" />
                      </Box>
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{ fontWeight: 600 }}
                      >
                        Total Scenarios
                      </Typography>
                    </Stack>
                    <Tooltip title="Total number of evaluation cases inside this version.">
                      <HelpOutlined
                        sx={{
                          fontSize: 16,
                          color: "text.disabled",
                          cursor: "help",
                        }}
                      />
                    </Tooltip>
                  </Stack>

                  <Typography variant="h3" sx={{ fontWeight: 800 }}>
                    {totalCases.toLocaleString()}
                  </Typography>

                  <Typography variant="caption" color="text.secondary">
                    Total evaluation test cases registered
                  </Typography>
                </Stack>
              </CardContent>
            </Card>
          </Grid>

          {isFinalized && (
            <>
              {/* Reference Data Card */}
              <Grid size={{ xs: 12, md: 4 }}>
                <Card
                  variant="outlined"
                  sx={{
                    height: "100%",
                    borderRadius: 2.5,
                    transition: "border-color 0.2s",
                    "&:hover": { borderColor: "text.secondary" },
                  }}
                >
                  <CardContent sx={{ p: 2.5 }}>
                    <Stack spacing={1.5}>
                      <Stack
                        direction="row"
                        sx={{
                          alignItems: "center",
                          justifyContent: "space-between",
                        }}
                      >
                        <Stack
                          direction="row"
                          spacing={1}
                          sx={{ alignItems: "center" }}
                        >
                          <Box
                            sx={{
                              p: 0.75,
                              borderRadius: 1.5,
                              bgcolor: alpha(theme.palette.success.main, 0.1),
                              color: "success.main",
                              display: "flex",
                            }}
                          >
                            <CheckCircleOutlined fontSize="small" />
                          </Box>
                          <Typography
                            variant="body2"
                            color="text.secondary"
                            sx={{ fontWeight: 600 }}
                          >
                            Reference Targets
                          </Typography>
                        </Stack>
                        <Tooltip title="Cases containing reference output ground truths.">
                          <HelpOutlined
                            sx={{
                              fontSize: 16,
                              color: "text.disabled",
                              cursor: "help",
                            }}
                          />
                        </Tooltip>
                      </Stack>

                      <Typography variant="h3" sx={{ fontWeight: 800 }}>
                        {referenceCount.toLocaleString()}
                      </Typography>

                      <Typography variant="caption" color="text.secondary">
                        Out of {totalCases.toLocaleString()} total test cases
                      </Typography>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>

              {/* Context Data Card */}
              <Grid size={{ xs: 12, md: 4 }}>
                <Card
                  variant="outlined"
                  sx={{
                    height: "100%",
                    borderRadius: 2.5,
                    transition: "border-color 0.2s",
                    "&:hover": { borderColor: "text.secondary" },
                  }}
                >
                  <CardContent sx={{ p: 2.5 }}>
                    <Stack spacing={1.5}>
                      <Stack
                        direction="row"
                        sx={{
                          alignItems: "center",
                          justifyContent: "space-between",
                        }}
                      >
                        <Stack
                          direction="row"
                          spacing={1}
                          sx={{ alignItems: "center" }}
                        >
                          <Box
                            sx={{
                              p: 0.75,
                              borderRadius: 1.5,
                              bgcolor: alpha(theme.palette.info.main, 0.1),
                              color: "info.main",
                              display: "flex",
                            }}
                          >
                            <DataObjectOutlined fontSize="small" />
                          </Box>
                          <Typography
                            variant="body2"
                            color="text.secondary"
                            sx={{ fontWeight: 600 }}
                          >
                            Context Support
                          </Typography>
                        </Stack>
                        <Tooltip title="Cases with contextual retrieval text attached.">
                          <HelpOutlined
                            sx={{
                              fontSize: 16,
                              color: "text.disabled",
                              cursor: "help",
                            }}
                          />
                        </Tooltip>
                      </Stack>

                      <Typography variant="h3" sx={{ fontWeight: 800 }}>
                        {contextCount.toLocaleString()}
                      </Typography>

                      <Typography variant="caption" color="text.secondary">
                        Out of {totalCases.toLocaleString()} total test cases
                      </Typography>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            </>
          )}
        </Grid>
      </Stack>

      {/* Dataset Capabilities Section */}
      <Card variant="outlined" sx={{ borderRadius: 3 }}>
        <CardContent sx={{ p: { xs: 2.5, sm: 3.5 } }}>
          <Stack spacing={3}>
            <Stack spacing={0.5}>
              <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                {hasEvaluationData ? (
                  <CheckCircle sx={{ color: "success.main", fontSize: 22 }} />
                ) : (
                  <WarningAmber sx={{ color: "warning.main", fontSize: 22 }} />
                )}

                <Typography
                  variant="h6"
                  sx={{ fontWeight: 700, fontSize: "1.1rem" }}
                >
                  Evaluation Readiness
                </Typography>
              </Stack>

              <Typography variant="body2" color="text.secondary">
                {hasEvaluationData
                  ? "This dataset version is fully configured for automated model evaluation runs."
                  : "No evaluation scenarios have been added to this dataset version yet."}
              </Typography>
            </Stack>

            <Divider />

            <Grid container spacing={3}>
              {/* Input Feature */}
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Stack spacing={1.25}>
                  <Stack
                    direction="row"
                    sx={{
                      alignItems: "center",
                      justifyContent: "space-between",
                    }}
                  >
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      sx={{ fontWeight: 700, letterSpacing: 0.8 }}
                    >
                      PROMPT INPUT
                    </Typography>
                    <Chip
                      label={hasEvaluationData ? "Ready" : "Empty"}
                      size="small"
                      color={hasEvaluationData ? "success" : "default"}
                      variant="outlined"
                      sx={{
                        height: 20,
                        fontSize: "0.6875rem",
                        fontWeight: 700,
                      }}
                    />
                  </Stack>

                  <Typography variant="body1" sx={{ fontWeight: 600 }}>
                    {hasEvaluationData
                      ? "Input Prompts Present"
                      : "No Input Data"}
                  </Typography>

                  <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{ lineHeight: 1.5 }}
                  >
                    Every case provides an input payload sent directly to
                    evaluator models.
                  </Typography>
                </Stack>
              </Grid>

              {/* Expected Output Feature */}
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Stack spacing={1.25}>
                  <Stack
                    direction="row"
                    sx={{
                      alignItems: "center",
                      justifyContent: "space-between",
                    }}
                  >
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      sx={{ fontWeight: 700, letterSpacing: 0.8 }}
                    >
                      EXPECTED OUTPUT
                    </Typography>
                    <Chip
                      label={referenceCount > 0 ? "Available" : "Optional"}
                      size="small"
                      color={referenceCount > 0 ? "primary" : "default"}
                      variant="outlined"
                      sx={{
                        height: 20,
                        fontSize: "0.6875rem",
                        fontWeight: 700,
                      }}
                    />
                  </Stack>

                  <Typography variant="body1" sx={{ fontWeight: 600 }}>
                    {hasEvaluationData
                      ? `${referenceCount} / ${totalCases} cases`
                      : "No Reference"}
                  </Typography>

                  <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{ lineHeight: 1.5 }}
                  >
                    Reference output target answers for correctness evaluation
                    metrics.
                  </Typography>
                </Stack>
              </Grid>

              {/* Reference Coverage Progress */}
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Stack spacing={1.25}>
                  <Stack
                    direction="row"
                    sx={{
                      alignItems: "center",
                      justifyContent: "space-between",
                    }}
                  >
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      sx={{ fontWeight: 700, letterSpacing: 0.8 }}
                    >
                      REFERENCE COVERAGE
                    </Typography>
                    <Typography variant="caption" sx={{ fontWeight: 700 }}>
                      {hasEvaluationData
                        ? `${(referenceCoverage * 100).toFixed(1)}%`
                        : "—"}
                    </Typography>
                  </Stack>

                  <Typography variant="body1" sx={{ fontWeight: 600 }}>
                    {hasEvaluationData
                      ? `${(referenceCoverage * 100).toFixed(0)}% Coverage`
                      : "Not Calculated"}
                  </Typography>

                  {hasEvaluationData ? (
                    <LinearProgress
                      variant="determinate"
                      value={Math.min(referenceCoverage * 100, 100)}
                      color="success"
                      sx={{
                        height: 6,
                        borderRadius: 3,
                        bgcolor: alpha(theme.palette.success.main, 0.12),
                      }}
                    />
                  ) : (
                    <Box
                      sx={{
                        height: 6,
                        bgcolor: "action.hover",
                        borderRadius: 3,
                      }}
                    />
                  )}
                </Stack>
              </Grid>

              {/* Context Coverage Progress */}
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Stack spacing={1.25}>
                  <Stack
                    direction="row"
                    sx={{
                      alignItems: "center",
                      justifyContent: "space-between",
                    }}
                  >
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      sx={{ fontWeight: 700, letterSpacing: 0.8 }}
                    >
                      CONTEXT COVERAGE
                    </Typography>
                    <Typography variant="caption" sx={{ fontWeight: 700 }}>
                      {hasEvaluationData
                        ? `${(contextCoverage * 100).toFixed(1)}%`
                        : "—"}
                    </Typography>
                  </Stack>

                  <Typography variant="body1" sx={{ fontWeight: 600 }}>
                    {hasEvaluationData
                      ? `${(contextCoverage * 100).toFixed(0)}% Coverage`
                      : "Not Calculated"}
                  </Typography>

                  {hasEvaluationData ? (
                    <LinearProgress
                      variant="determinate"
                      value={Math.min(contextCoverage * 100, 100)}
                      color="info"
                      sx={{
                        height: 6,
                        borderRadius: 3,
                        bgcolor: alpha(theme.palette.info.main, 0.12),
                      }}
                    />
                  ) : (
                    <Box
                      sx={{
                        height: 6,
                        bgcolor: "action.hover",
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
    </Stack>
  );
}
