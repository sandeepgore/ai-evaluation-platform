import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { InfoOutlined } from "@mui/icons-material";
import { Alert, Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, Paper, Stack, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Typography } from "@mui/material";
import { apiClient } from "../../services/api/client";
import { StatusChip } from "../../components/common/StatusChip";
import { TableActionButton } from "../../components/common/TableActionButton";
import { LoadingState } from "../../components/common/LoadingState";

interface AuditEntry {
  id: string;
  actor_name: string | null;
  actor_email: string | null;
  action: string;
  resource: string;
  details: Record<string, unknown> | null;
  method: string;
  status_code: number;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
}

function auditValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "object") return JSON.stringify(value, null, 2) ?? String(value);
  return String(value);
}

function auditTarget(entry: AuditEntry): string {
  const entityType = entry.details?.entity_type;
  const entityName = entry.details?.entity_name;
  const userName = entry.details?.target_user_name;
  if (typeof userName === "string") return `User · ${userName}`;
  if (typeof entityName === "string") {
    return [entityType, entityName].filter((value) => typeof value === "string").join(" · ");
  }
  return entry.resource
    .split("/")
    .map((part) => (/^[0-9a-f]{8}-[0-9a-f-]{27,}$/i.test(part) ? "item" : part))
    .join("/");
}

function auditAction(entry: AuditEntry): string {
  const operation = entry.details?.operation;
  const entityType = entry.details?.entity_type;
  if (typeof operation === "string" && typeof entityType === "string") {
    const isFileImport = operation === "create" && Boolean(entry.details?.source_file);
    const verb = isFileImport ? "Imported" : operation === "create" ? "Created" : operation === "delete" ? "Deleted" : operation === "update" ? "Updated" : operation;
    const name = entry.details?.entity_name;
    const action = entry.status_code >= 400 ? `Attempted to ${operation}` : verb;
    return `${action} ${entityType}${typeof name === "string" ? `: ${name}` : ""}`;
  }
  return entry.action.replace(/[0-9a-f]{8}-[0-9a-f-]{27,}/gi, "item");
}

function AuditChangeDetails({ details }: { details: Record<string, unknown> }) {
  const changes = details.changes as Record<
    string,
    { from?: unknown; to?: unknown }
  > | undefined;
  const snapshot = (details.created ?? details.deleted) as
    | Record<string, unknown>
    | undefined;
  const rows = changes
    ? Object.entries(changes).map(([field, values]) => ({
        field,
        from: auditValue(values.from),
        to: auditValue(values.to),
      }))
    : snapshot
      ? Object.entries(snapshot).filter(([field]) => field !== "id" && !field.endsWith("_id")).map(([field, value]) => ({
          field,
          from: details.deleted ? auditValue(value) : "—",
          to: details.created ? auditValue(value) : "—",
        }))
      : Object.entries(details)
          .filter(([key]) => !["operation", "entity_type", "entity_id", "entity_name", "outcome", "source_file", "dataset_name"].includes(key))
          .map(([field, value]) => ({ field, from: "—", to: auditValue(value) }));

  const sourceFile = details.source_file as Record<string, unknown> | undefined;
  if (sourceFile) {
    for (const [field, value] of Object.entries(sourceFile)) {
      rows.push({ field: `File ${field.replaceAll("_", " ")}`, from: "-", to: auditValue(value) });
    }
  }
  if (typeof details.dataset_name === "string") {
    rows.push({ field: "Dataset", from: "-", to: details.dataset_name });
  }

  if (!rows.length) {
    return <Typography variant="body2" color="text.secondary">No field-level details were recorded for this event.</Typography>;
  }

  return <TableContainer component={Paper} variant="outlined">
    <Table size="small">
      <TableHead><TableRow>
        <TableCell>Field</TableCell><TableCell>From</TableCell><TableCell>To</TableCell>
      </TableRow></TableHead>
      <TableBody>{rows.map((row) => <TableRow key={row.field}>
        <TableCell sx={{ fontWeight: 600, whiteSpace: "nowrap" }}>{row.field}</TableCell>
        <TableCell sx={{ overflowWrap: "anywhere", whiteSpace: "pre-wrap" }}>{row.from}</TableCell>
        <TableCell sx={{ overflowWrap: "anywhere", whiteSpace: "pre-wrap" }}>{row.to}</TableCell>
      </TableRow>)}</TableBody>
    </Table>
  </TableContainer>;
}

function AuditEventDialog({ entry: selectedEntry, onClose }: { entry: AuditEntry | null; onClose: () => void }) {
  const entry = selectedEntry
    ? {
        ...selectedEntry,
        actor_email: selectedEntry.actor_name ?? selectedEntry.actor_email,
        action: auditAction(selectedEntry),
        resource: auditTarget(selectedEntry),
      }
    : null;
  return <Dialog open={entry !== null} onClose={onClose} fullWidth maxWidth="md">
    <DialogTitle>Audit event details</DialogTitle>
    {entry && <DialogContent dividers sx={{ maxHeight: "70vh" }}>
      <Stack spacing={2}>
        <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))" }, gap: 1.5 }}>
          {[["Actor", entry.actor_email ?? "Unauthenticated"], ["Action", entry.action], ["Resource", entry.resource], ["Method", entry.method], ["Status", String(entry.status_code)], ["Time", new Date(entry.created_at).toLocaleString()], ["IP address", entry.ip_address ?? "—"], ["User agent", entry.user_agent ?? "—"]].map(([label, value]) =>
            <Box key={label}><Typography variant="caption" color="text.secondary">{label}</Typography><Typography variant="body2" sx={{ overflowWrap: "anywhere" }}>{value}</Typography></Box>
          )}
        </Box>
        {entry.details && <Box><Typography variant="subtitle2" fontWeight={700} sx={{ mb: 0.5 }}>Change details</Typography>
          <AuditChangeDetails details={entry.details} />
        </Box>}
      </Stack>
    </DialogContent>}
    <DialogActions><Button onClick={onClose}>Close</Button></DialogActions>
  </Dialog>;
}

export function AuditLogsPage() {
  const [selectedEntry, setSelectedEntry] = useState<AuditEntry | null>(null);
  const logs = useQuery({ queryKey: ["audit-logs"], queryFn: async () => (await apiClient.get<AuditEntry[]>("/api/v1/audit-logs?limit=200")).data });

  return <Box sx={{ p: 3 }}>
    <Box sx={{ mb: 3 }}><Typography variant="h4" fontWeight={700}>Audit log</Typography><Typography color="text.secondary">Recent account, access, and platform changes.</Typography></Box>
    {logs.isError && <Alert severity="error" sx={{ mb: 2 }}>{logs.error.message}</Alert>}
    {logs.isLoading ? <LoadingState message="Loading audit logs..." /> : <TableContainer component={Paper}>
      <Table size="small"><TableHead><TableRow>
        <TableCell>Time</TableCell><TableCell>Actor</TableCell><TableCell>Action</TableCell><TableCell>Target</TableCell><TableCell>Result</TableCell><TableCell>Details</TableCell>
      </TableRow></TableHead><TableBody>
        {logs.data?.length ? logs.data.map((entry) => <TableRow key={entry.id} hover>
          <TableCell sx={{ whiteSpace: "nowrap" }}>{new Date(entry.created_at).toLocaleString()}</TableCell>
          <TableCell>{entry.actor_name ?? entry.actor_email ?? "Unauthenticated"}</TableCell>
          <TableCell>{auditAction(entry)}</TableCell>
          <TableCell sx={{ maxWidth: 300, overflowWrap: "anywhere" }}>{auditTarget(entry)}</TableCell>
          <TableCell><StatusChip status={entry.status_code < 400 ? "success" : "error"} label={String(entry.status_code)} /></TableCell>
          <TableCell align="right"><TableActionButton label="View event details" icon={<InfoOutlined fontSize="small" />} onClick={() => setSelectedEntry(entry)} /></TableCell>
        </TableRow>) : <TableRow><TableCell colSpan={6} align="center">No audit events yet.</TableCell></TableRow>}
      </TableBody></Table>
    </TableContainer>}
    <AuditEventDialog entry={selectedEntry} onClose={() => setSelectedEntry(null)} />
  </Box>;
}
