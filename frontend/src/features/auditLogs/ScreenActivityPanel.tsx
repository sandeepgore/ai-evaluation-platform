import { useQuery } from "@tanstack/react-query";
import {
  Box,
  Chip,
  CircularProgress,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Paper,
  Stack,
  Tooltip,
  Typography,
} from "@mui/material";
import { ChevronLeftOutlined, ChevronRightOutlined } from "@mui/icons-material";
import { StatusChip } from "../../components/common/StatusChip";
import { apiClient } from "../../services/api/client";

export type ActivityScreen =
  | "organizations"
  | "projects"
  | "models"
  | "datasets"
  | "dataset_cases"
  | "dataset_versions"
  | "evaluations"
  | "experiments";

const SCREEN_LABELS: Record<ActivityScreen, string> = {
  organizations: "Organization",
  projects: "Project",
  models: "Model",
  datasets: "Dataset",
  dataset_cases: "Dataset case",
  dataset_versions: "Dataset version",
  evaluations: "Evaluation",
  experiments: "Experiment",
};

interface ActivityEntry {
  id: string;
  actor_name: string | null;
  actor_email: string | null;
  action: string;
  resource: string;
  details: Record<string, unknown> | null;
  method: string;
  status_code: number;
  created_at: string;
}

function describeChange(entry: ActivityEntry, screen: ActivityScreen) {
  const suffix = entry.resource.replace("/api/v1/", "").split("/").slice(1);
  const operation = suffix.find(
    (part) => !/^[0-9a-f]{8}-[0-9a-f-]{27,}$/i.test(part),
  );
  const method = entry.method.toUpperCase();
  const attempted = entry.status_code >= 400;
  if (entry.details?.source_file && method === "POST") {
    const noun = SCREEN_LABELS[screen].toLowerCase();
    return attempted ? `Attempted to import ${noun}` : `Imported ${noun}`;
  }
  if (operation === "execute")
    return attempted ? "Attempted to start evaluation" : "Started evaluation";
  if (operation === "cancel")
    return attempted
      ? "Attempted to cancel evaluation"
      : "Cancelled evaluation";
  if (operation === "snapshots")
    return attempted
      ? "Attempted to save experiment comparison"
      : "Saved experiment comparison";
  const noun = SCREEN_LABELS[screen].toLowerCase();
  const verb =
    method === "POST"
      ? attempted
        ? "create"
        : "Created"
      : method === "DELETE"
        ? attempted
          ? "delete"
          : "Deleted"
        : attempted
          ? "update"
          : "Updated";
  return `${attempted ? "Attempted to " : ""}${verb}${attempted ? "" : " "}${noun}`;
}

function auditValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "object") return JSON.stringify(value, null, 2) ?? String(value);
  return String(value);
}

function activityName(entry: ActivityEntry): string | null {
  const name = entry.details?.entity_name;
  return typeof name === "string" ? name : null;
}

function sourceFileDetails(entry: ActivityEntry): Array<[string, string]> {
  const sourceFile = entry.details?.source_file;
  if (!sourceFile || typeof sourceFile !== "object") return [];
  const file = sourceFile as Record<string, unknown>;
  const details: Array<[string, string]> = [];
  if (typeof file.name === "string") details.push(["Source file", file.name]);
  if (typeof file.format === "string") details.push(["Format", file.format.toUpperCase()]);
  if (typeof file.size_bytes === "number") {
    const size = file.size_bytes < 1024 * 1024
      ? `${(file.size_bytes / 1024).toFixed(1)} KB`
      : `${(file.size_bytes / (1024 * 1024)).toFixed(2)} MB`;
    details.push(["File size", size]);
  }
  if (typeof file.case_count === "number") details.push(["Cases imported", String(file.case_count)]);
  return details;
}

function readableFieldName(field: string): string {
  const labels: Record<string, string> = {
    is_active: "Active",
    case_count: "Cases",
    dataset_name: "Dataset",
  };
  return labels[field] ?? field.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function readableSnapshotValue(field: string, value: unknown): string {
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (field === "status" && typeof value === "string") {
    return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
  }
  if (field === "case_count" && typeof value === "number") {
    return `${value} ${value === 1 ? "case" : "cases"}`;
  }
  return auditValue(value);
}

function snapshotDetails(entry: ActivityEntry): Array<[string, unknown]> {
  const snapshot = entry.details?.created ?? entry.details?.deleted;
  if (!snapshot || typeof snapshot !== "object") return [];
  return Object.entries(snapshot as Record<string, unknown>).filter(([key, value]) =>
    key !== "id" && !key.endsWith("_id") &&
    !(key === "case_count" && entry.details?.source_file) &&
    !["created_at", "updated_at"].includes(key) && value !== null && value !== "",
  );
}

export function ScreenActivityPanel({
  screen,
  expanded,
  onToggle,
}: {
  screen: ActivityScreen;
  expanded: boolean;
  onToggle: () => void;
}) {
  const activity = useQuery({
    queryKey: ["screen-activity", screen],
    queryFn: async () =>
      (
        await apiClient.get<ActivityEntry[]>("/api/v1/audit-logs/activity", {
          params: { screen, limit: 12 },
        })
      ).data,
    refetchInterval: 10_000,
  });
  const newestFirst = [...(activity.data ?? [])].sort(
    (a, b) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  );

  if (!expanded) {
    return (
      <Paper
        variant="outlined"
        sx={{
          width: 48,
          minHeight: 48,
          borderRadius: 3,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          justifySelf: { xs: "end", xl: "stretch" },
        }}
      >
        <Tooltip title="Expand recent changes" placement="left">
          <IconButton
            size="small"
            aria-label="Expand recent changes"
            onClick={onToggle}
          >
            <ChevronLeftOutlined fontSize="small" />
          </IconButton>
        </Tooltip>
      </Paper>
    );
  }

  return (
    <Paper
      variant="outlined"
      sx={{
        borderRadius: 3,
        overflow: "hidden",
        alignSelf: "start",
        minWidth: 0,
      }}
    >
      <Stack
        direction="row"
        alignItems="center"
        spacing={1}
        sx={{ px: 2, py: 1.25, borderBottom: 1, borderColor: "divider" }}
      >
        <Typography variant="subtitle2" fontWeight={700} sx={{ flex: 1 }}>
          Recent changes
        </Typography>
        <Chip
          size="small"
          variant="outlined"
          label={activity.data?.length ?? 0}
        />
        <Tooltip title="Collapse to right side" placement="left">
          <IconButton
            size="small"
            aria-label="Collapse recent changes to right side"
            aria-expanded={expanded}
            onClick={onToggle}
          >
            <ChevronRightOutlined fontSize="small" />
          </IconButton>
        </Tooltip>
      </Stack>

      {activity.isLoading ? (
        <Box sx={{ display: "flex", justifyContent: "center", py: 3 }}>
          <CircularProgress size={22} />
        </Box>
      ) : activity.isError ? (
        <Typography variant="body2" color="text.secondary" sx={{ p: 2 }}>
          Activity could not be loaded.
        </Typography>
      ) : newestFirst.length ? (
        <List disablePadding>
          {newestFirst.map((entry, index) => (
            <ListItem
              key={entry.id}
              alignItems="flex-start"
              divider={index < newestFirst.length - 1}
              sx={{ px: 2, py: 1.25, gap: 1, alignItems: "flex-start" }}
            >
              <ListItemText
                sx={{ my: 0, minWidth: 0 }}
                primary={
                  <Stack direction="row" spacing={1} alignItems="flex-start" justifyContent="space-between">
                    <Typography variant="body2" fontWeight={600} sx={{ minWidth: 0, overflowWrap: "anywhere" }}>
                      {describeChange(entry, screen)}
                      {activityName(entry) ? `: ${activityName(entry)}` : ""}
                    </Typography>
                    <StatusChip
                      status={entry.status_code < 400 ? "success" : "error"}
                      label={entry.status_code < 400 ? "Saved" : "Failed"}
                    />
                  </Stack>
                }
                secondary={
                  <Box component="div">
                    <Typography
                      component="span"
                      variant="caption"
                      color="text.secondary"
                      display="block"
                    >
                      {entry.actor_name ?? entry.actor_email ?? "System"} ·{" "}
                      {new Date(entry.created_at).toLocaleString()}
                    </Typography>
                    {(sourceFileDetails(entry).length > 0 || snapshotDetails(entry).length > 0) && (
                      <Box
                        sx={{
                          mt: 0.75,
                          p: 1,
                          borderRadius: 1.5,
                          bgcolor: "action.hover",
                          display: "grid",
                          gridTemplateColumns: "1fr",
                          gap: 0.5,
                        }}
                      >
                        {sourceFileDetails(entry).map(([label, value]) => (
                          <Box key={`file-${label}`} sx={{ minWidth: 0, display: "grid", gridTemplateColumns: "minmax(96px, auto) minmax(0, 1fr)", columnGap: 1.5, alignItems: "baseline" }}>
                            <Typography variant="caption" color="text.secondary" fontWeight={600}>
                              {label}:
                            </Typography>
                            <Typography variant="caption" color="text.primary" sx={{ overflowWrap: "anywhere" }}>
                              {value}
                            </Typography>
                          </Box>
                        ))}
                        {snapshotDetails(entry).map(([field, value]) => (
                          <Box key={`snapshot-${field}`} sx={{ minWidth: 0 }}>
                            <Box sx={{ display: "grid", gridTemplateColumns: "minmax(96px, auto) minmax(0, 1fr)", columnGap: 1.5, alignItems: "baseline" }}>
                              <Typography variant="caption" color="text.secondary" fontWeight={600}>
                                {readableFieldName(field)}:
                              </Typography>
                              <Typography
                                variant="caption"
                                color="text.primary"
                                sx={{ overflowWrap: "anywhere", whiteSpace: "pre-wrap" }}
                              >
                                {readableSnapshotValue(field, value)}
                              </Typography>
                            </Box>
                          </Box>
                        ))}
                      </Box>
                    )}
                    {entry.details?.changes &&
                      typeof entry.details.changes === "object" && (
                        <Box sx={{ mt: 0.5 }}>
                          {Object.entries(
                            entry.details.changes as Record<
                              string,
                              { from?: unknown; to?: unknown }
                            >,
                          )
                            .slice(0, 3)
                            .map(([field, change]) => (
                              <Typography
                                key={field}
                                component="span"
                                variant="caption"
                                color="text.secondary"
                                display="block"
                                sx={{ overflowWrap: "anywhere", whiteSpace: "pre-wrap" }}
                              >
                                {field}: {auditValue(change.from)} → {auditValue(change.to)}
                              </Typography>
                            ))}
                        </Box>
                      )}
                    {!entry.details?.changes &&
                      !entry.details?.created &&
                      !entry.details?.deleted &&
                      Array.isArray(entry.details?.changed_fields) &&
                      entry.details.changed_fields.length > 0 && (
                        <Typography
                          component="span"
                          variant="caption"
                          color="text.secondary"
                          display="block"
                          sx={{ mt: 0.25, overflowWrap: "anywhere" }}
                        >
                          Changed: {entry.details.changed_fields.join(", ")}
                        </Typography>
                      )}
                  </Box>
                }
              />
            </ListItem>
          ))}
        </List>
      ) : (
        <Typography variant="body2" color="text.secondary" sx={{ p: 2 }}>
          No changes recorded for this screen yet.
        </Typography>
      )}
    </Paper>
  );
}
