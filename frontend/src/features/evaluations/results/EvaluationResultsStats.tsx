import { Box, Card, CardContent, Grid, Stack, Typography } from "@mui/material";
import {
  CheckCircleOutlined,
  ErrorOutlined,
  HourglassEmpty,
  Inventory2Outlined,
  NotInterested,
} from "@mui/icons-material";
import { EvaluationResultStatistics } from "../api";

interface EvaluationResultsStatsProps {
  statistics?: EvaluationResultStatistics;
  loading?: boolean;
}

const cards = [
  {
    key: "total",
    label: "Total results",
    icon: Inventory2Outlined,
    color: "text.primary",
  },
  {
    key: "completed",
    label: "Completed",
    icon: CheckCircleOutlined,
    color: "success.main",
  },
  {
    key: "failed",
    label: "Failed",
    icon: ErrorOutlined,
    color: "error.main",
  },
  {
    key: "pending",
    label: "Pending",
    icon: HourglassEmpty,
    color: "warning.main",
  },
  {
    key: "notApplicable",
    label: "Not applicable",
    icon: NotInterested,
    color: "text.secondary",
  },
] as const;

export default function EvaluationResultsStats({
  statistics,
  loading = false,
}: EvaluationResultsStatsProps) {
  const values: Record<(typeof cards)[number]["key"], number | undefined> = {
    total: statistics?.total,
    completed: statistics?.completed,
    failed: statistics?.failed,
    pending: statistics?.pending,
    notApplicable: statistics?.not_applicable,
  };

  return (
    <Grid container spacing={2}>
      {cards.map((card) => {
        const Icon = card.icon;
        const value = values[card.key];

        return (
          <Grid key={card.key} size={{ xs: 12, sm: 6, md: 4, lg: 2.4 }}>
            <Card variant="outlined" sx={{ height: "100%" }}>
              <CardContent>
                <Stack spacing={1}>
                  <Box
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                    }}
                  >
                    <Typography variant="body2" color="text.secondary">
                      {card.label}
                    </Typography>
                    <Icon fontSize="small" color="inherit" />
                  </Box>

                  <Typography
                    variant="h4"
                    sx={{
                      fontWeight: 700,
                      color: card.color,
                    }}
                  >
                    {loading ? "—" : (value ?? "—")}
                  </Typography>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        );
      })}
    </Grid>
  );
}
