import { Box, Card, CardContent, Chip, Stack, Typography, useTheme } from "@mui/material";
import {
  Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from "recharts";
import type { EvaluationRun } from "../evaluations/api";

export function EvaluationCharts({ runs, projectSelected }: { runs: EvaluationRun[]; projectSelected: boolean }) {
  const theme = useTheme();
  const statusColors: Record<string, string> = {
    completed: theme.palette.success.main,
    failed: theme.palette.error.main,
    running: theme.palette.primary.main,
    pending: theme.palette.warning.main,
    cancelled: theme.palette.grey[500],
  };
  const counts = new Map<string, number>();
  runs.forEach((run) => counts.set(run.status, (counts.get(run.status) ?? 0) + 1));
  const statusData = [...counts].map(([name, value]) => ({ name, value }));
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const start = new Date(today);
  start.setDate(start.getDate() - 6);
  const activity = Array.from({ length: 7 }, (_, index) => {
    const date = new Date(start);
    date.setDate(date.getDate() + index);
    const key = date.toDateString();
    return {
      day: new Intl.DateTimeFormat(undefined, { weekday: "short" }).format(date),
      runs: runs.filter((run) => new Date(run.created_at).toDateString() === key).length,
    };
  });
  const hasData = runs.length > 0;

  return <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "repeat(2, minmax(0, 1fr))" }, gap: 2 }}>
    <Card variant="outlined" sx={{ borderRadius: 3 }}><CardContent>
      <Stack direction="row" useFlexGap flexWrap="wrap" justifyContent="space-between" alignItems="center" spacing={1} sx={{ mb: 1 }}>
        <Typography variant="h6" fontWeight={700}>Run status</Typography>
        <Chip size="small" variant="outlined" label={`${runs.length} total`} sx={{ flexShrink: 0 }} />
      </Stack>
      {!projectSelected || !hasData ? <Box sx={{ height: 220, display: "grid", placeItems: "center" }}><Typography color="text.secondary">{projectSelected ? "No evaluation runs yet" : "Select a project to see runs"}</Typography></Box> :
        <Box sx={{ width: "100%", height: 220 }}><ResponsiveContainer>
          <PieChart><Pie data={statusData} dataKey="value" nameKey="name" innerRadius={55} outerRadius={82} paddingAngle={3}>
            {statusData.map((entry) => <Cell key={entry.name} fill={statusColors[entry.name] ?? theme.palette.grey[500]} />)}
          </Pie><Tooltip formatter={(value, name) => [value, String(name).replace(/^./, (letter) => letter.toUpperCase())]} /></PieChart>
        </ResponsiveContainer></Box>}
      <Stack direction="row" spacing={1.5} useFlexGap flexWrap="wrap" sx={{ mt: 1 }}>
        {statusData.map(({ name, value }) => <Stack key={name} direction="row" spacing={0.75} alignItems="center">
          <Box sx={{ width: 9, height: 9, borderRadius: "50%", bgcolor: statusColors[name] ?? theme.palette.grey[500] }} />
          <Typography variant="caption" color="text.secondary">{name} {value}</Typography>
        </Stack>)}
      </Stack>
    </CardContent></Card>

    <Card variant="outlined" sx={{ borderRadius: 3 }}><CardContent>
      <Stack direction="row" useFlexGap flexWrap="wrap" justifyContent="space-between" alignItems="center" spacing={1} sx={{ mb: 1 }}>
        <Typography variant="h6" fontWeight={700}>Evaluation activity</Typography>
        <Chip size="small" variant="outlined" label="Last 7 days" sx={{ flexShrink: 0 }} />
      </Stack>
      {!projectSelected || !hasData ? <Box sx={{ height: 220, display: "grid", placeItems: "center" }}><Typography color="text.secondary">{projectSelected ? "No recent activity" : "Select a project to see activity"}</Typography></Box> :
        <Box sx={{ width: "100%", height: 220 }}><ResponsiveContainer>
          <BarChart data={activity} margin={{ top: 8, right: 8, left: -22, bottom: 0 }}>
            <CartesianGrid stroke={theme.palette.divider} vertical={false} />
            <XAxis dataKey="day" tickLine={false} axisLine={false} />
            <YAxis allowDecimals={false} tickLine={false} axisLine={false} />
            <Tooltip />
            <Bar dataKey="runs" name="Runs" fill={theme.palette.primary.main} radius={[5, 5, 0, 0]} maxBarSize={36} />
          </BarChart>
        </ResponsiveContainer></Box>}
    </CardContent></Card>
  </Box>;
}
