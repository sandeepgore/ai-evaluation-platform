import {
  Box,
  Button,
  Card,
  CardContent,
  Divider,
  Grid,
  Stack,
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
  const hasEvaluationData = data.case_count > 0;

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
            label: `Version v${data.version}`,
          },
        ]}
      />

      <Stack spacing={1}>
        <Stack
          direction={{ xs: "column", sm: "row" }}
          spacing={2}
          sx={{
            justifyContent: "space-between",
            alignItems: { xs: "flex-start", sm: "center" },
          }}
        >
          <Stack spacing={0.5}>
            <Typography variant="h5" sx={{ fontWeight: 700 }}>
              Dataset Version v{data.version}
            </Typography>

            <Typography variant="body2" color="text.secondary">
              {data.description ?? "No description"}
            </Typography>
          </Stack>

          <DatasetVersionStatusChip status={data.status} />
        </Stack>
      </Stack>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 4 }}>
          <Card sx={{ height: "100%" }}>
            <CardContent>
              <Stack spacing={0.75}>
                <Typography variant="body2" color="text.secondary">
                  Total Cases
                </Typography>

                <Typography variant="h4" sx={{ fontWeight: 700 }}>
                  {data.case_count}
                </Typography>

                <Typography variant="body2" color="text.secondary">
                  Evaluation cases in this version
                </Typography>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, md: 4 }}>
          <Card sx={{ height: "100%" }}>
            <CardContent>
              <Stack spacing={0.75}>
                <Typography variant="body2" color="text.secondary">
                  Reference Data
                </Typography>

                <Typography variant="h4" sx={{ fontWeight: 700 }}>
                  {analytics?.reference_count ?? 0}
                </Typography>

                <Typography variant="body2" color="text.secondary">
                  {analytics
                    ? `${(analytics.reference_coverage * 100).toFixed(1)}% of cases have reference data`
                    : "Coverage not available yet"}
                </Typography>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, md: 4 }}>
          <Card sx={{ height: "100%" }}>
            <CardContent>
              <Stack spacing={0.75}>
                <Typography variant="body2" color="text.secondary">
                  Context Data
                </Typography>

                <Typography variant="h4" sx={{ fontWeight: 700 }}>
                  {analytics?.context_count ?? 0}
                </Typography>

                <Typography variant="body2" color="text.secondary">
                  {analytics
                    ? `${(analytics.context_coverage * 100).toFixed(1)}% of cases have context`
                    : "Coverage not available yet"}
                </Typography>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Card>
        <CardContent>
          <Stack spacing={2}>
            <Stack spacing={0.5}>
              <Typography variant="h6" sx={{ fontWeight: 700 }}>
                {hasEvaluationData
                  ? "Evaluation Data Available"
                  : "No Evaluation Data"}
              </Typography>

              <Typography variant="body2" color="text.secondary">
                {hasEvaluationData
                  ? "Data available to evaluators when running this dataset version."
                  : "Add at least one case before this dataset version can be used for evaluation."}
              </Typography>
            </Stack>

            <Divider />

            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  Input
                </Typography>

                <Typography variant="body1" sx={{ fontWeight: 600 }}>
                  {hasEvaluationData ? "Available" : "No cases"}
                </Typography>
              </Grid>

              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  Expected Output
                </Typography>

                <Typography variant="body1" sx={{ fontWeight: 600 }}>
                  {hasEvaluationData
                    ? analytics && analytics.reference_count > 0
                      ? "Available"
                      : "Not available"
                    : "No cases"}
                </Typography>
              </Grid>

              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  Reference Coverage
                </Typography>

                <Typography variant="body1" sx={{ fontWeight: 600 }}>
                  {hasEvaluationData && analytics
                    ? `${(analytics.reference_coverage * 100).toFixed(1)}%`
                    : "—"}
                </Typography>
              </Grid>

              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  Context Coverage
                </Typography>

                <Typography variant="body1" sx={{ fontWeight: 600 }}>
                  {hasEvaluationData && analytics
                    ? `${(analytics.context_coverage * 100).toFixed(1)}%`
                    : "—"}
                </Typography>
              </Grid>
            </Grid>
          </Stack>
        </CardContent>
      </Card>

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
            <Stack spacing={0.5}>
              <Typography variant="h6" sx={{ fontWeight: 700 }}>
                Cases
              </Typography>

              <Typography variant="body2" color="text.secondary">
                View and manage the evaluation cases in this version.
              </Typography>
            </Stack>

            <Button
              variant="outlined"
              startIcon={
                <Box
                  component="img"
                  src="/svg/cases.svg"
                  alt=""
                  sx={{
                    width: 22,
                    height: 22,
                  }}
                />
              }
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

