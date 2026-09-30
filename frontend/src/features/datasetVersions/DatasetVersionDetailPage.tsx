import {
  Button,
  Card,
  CardContent,
  Divider,
  Grid,
  Stack,
  Typography,
} from "@mui/material";
import { useNavigate, useParams } from "react-router-dom";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import { DatasetVersionStatusChip } from "./DatasetVersionStatusChip";
import { useDatasetVersion } from "./hooks";

export function DatasetVersionDetailPage() {
  const navigate = useNavigate();
  const { datasetId, versionId } = useParams<{
    datasetId: string;
    versionId: string;
  }>();

  const { data, isLoading, isError } = useDatasetVersion(versionId ?? null);

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

  return (
    <Stack spacing={3}>
      <Stack spacing={1}>
        <Button
          variant="text"
          onClick={() => navigate(`/datasets/${datasetId}/versions`)}
          sx={{ alignSelf: "flex-start" }}
        >
          ← Back to Versions
        </Button>

        <Stack
          direction="row"
          spacing={2}
          sx={{
            justifyContent: "space-between",
            alignItems: "center",
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

      <Card>
        <CardContent>
          <Stack spacing={2}>
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              Analytics
            </Typography>

            <Divider />

            {analytics ? (
              <Grid container spacing={2}>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <Typography variant="body2" color="text.secondary">
                    Cases
                  </Typography>
                  <Typography variant="h6">{analytics.case_count}</Typography>
                </Grid>

                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <Typography variant="body2" color="text.secondary">
                    Reference Cases
                  </Typography>
                  <Typography variant="h6">
                    {analytics.reference_count}
                  </Typography>
                </Grid>

                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <Typography variant="body2" color="text.secondary">
                    Reference Coverage
                  </Typography>
                  <Typography variant="h6">
                    {(analytics.reference_coverage * 100).toFixed(1)}%
                  </Typography>
                </Grid>

                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <Typography variant="body2" color="text.secondary">
                    Context Cases
                  </Typography>
                  <Typography variant="h6">
                    {analytics.context_count}
                  </Typography>
                </Grid>

                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <Typography variant="body2" color="text.secondary">
                    Context Coverage
                  </Typography>
                  <Typography variant="h6">
                    {(analytics.context_coverage * 100).toFixed(1)}%
                  </Typography>
                </Grid>
              </Grid>
            ) : (
              <Typography variant="body2" color="text.secondary">
                Analytics are not available for this version yet.
              </Typography>
            )}
          </Stack>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            Cases
          </Typography>
        </CardContent>
      </Card>
    </Stack>
  );
}
