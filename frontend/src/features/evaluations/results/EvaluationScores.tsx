import { Box, LinearProgress, Paper, Stack, Typography } from "@mui/material";
import { StatusChip } from "../../../components/common/StatusChip";

type MetricScore = {
  score?: unknown;
  status?: unknown;
  metadata?: unknown;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function metricLabel(value: string) {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function scoreColor(score: number): "success" | "warning" | "error" {
  if (score >= 0.8) return "success";
  if (score >= 0.5) return "warning";
  return "error";
}

function ScoreMetric({ name, value }: { name: string; value: MetricScore }) {
  const score = typeof value.score === "number" && Number.isFinite(value.score)
    ? Math.min(1, Math.max(0, value.score))
    : null;
  const notApplicable = value.status === "not_applicable";
  const metadata = isRecord(value.metadata) ? value.metadata : null;
  const reason = typeof metadata?.reason === "string" ? metadata.reason : null;

  return (
    <Paper variant="outlined" sx={{ p: 1.5, borderRadius: 2 }}>
      <Stack spacing={1}>
        <Stack direction="row" spacing={1} alignItems="center" justifyContent="space-between">
          <Typography variant="body2" fontWeight={600}>{metricLabel(name)}</Typography>
          {notApplicable ? (
            <StatusChip status="not_applicable" label="Not applicable" />
          ) : score !== null ? (
            <Typography variant="body2" fontWeight={700}>{(score * 100).toFixed(1)}%</Typography>
          ) : (
            <StatusChip status={typeof value.status === "string" ? value.status : "unknown"} label={typeof value.status === "string" ? metricLabel(value.status) : "No score"} />
          )}
        </Stack>
        {score !== null && !notApplicable && (
          <LinearProgress
            variant="determinate"
            value={score * 100}
            color={scoreColor(score)}
            sx={{ height: 7, borderRadius: 4 }}
          />
        )}
        {reason && <Typography variant="caption" color="text.secondary">{reason}</Typography>}
      </Stack>
    </Paper>
  );
}

export default function EvaluationScores({ value }: { value: unknown }) {
  if (!isRecord(value)) {
    return <Typography variant="body2" color="text.secondary">No scores available.</Typography>;
  }

  const overall = isRecord(value.overall) ? value.overall as MetricScore : null;
  const metrics = Object.entries(value).filter(
    ([name, score]) => name !== "overall" && isRecord(score),
  ) as [string, MetricScore][];

  if (!overall && metrics.length === 0) {
    return <Typography variant="body2" color="text.secondary">No scores available.</Typography>;
  }

  return (
    <Stack spacing={1.5}>
      {overall && (
        <Box>
          <Typography variant="subtitle2" sx={{ mb: 0.75 }}>Overall score</Typography>
          <ScoreMetric name="Overall" value={overall} />
        </Box>
      )}
      {metrics.length > 0 && (
        <Box>
          <Typography variant="subtitle2" sx={{ mb: 0.75 }}>Metrics</Typography>
          <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))" }, gap: 1 }}>
            {metrics.map(([name, score]) => <ScoreMetric key={name} name={name} value={score} />)}
          </Box>
        </Box>
      )}
    </Stack>
  );
}
