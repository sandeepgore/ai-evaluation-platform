import { DeleteOutlined, EditOutlined } from "@mui/icons-material";
import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { StatusChip } from "../../components/common/StatusChip";
import { TableActionButton } from "../../components/common/TableActionButton";
import { PermissionGate } from "../../components/common/PermissionGate";
import { DataTableSortLabel, type SortDirection } from "../../components/common/DataTableSortLabel";
import type { Model } from "./api";

interface ModelTableProps {
  models: Model[];
  onEdit: (model: Model) => void;
  onDelete: (model: Model) => void;
  sortField?: "name" | "provider" | "model_identifier";
  sortDirection?: SortDirection;
  onSort?: (field: "name" | "provider" | "model_identifier") => void;
}

const providerLabels: Record<Model["provider"], string> = {
  mock: "Mock",
  openai: "OpenAI",
  anthropic: "Anthropic",
  google: "Google",
  ollama: "Ollama",
  huggingface: "Hugging Face",
  azure_openai: "Azure OpenAI",
  custom: "Custom",
};

const modelTypeLabels: Record<Model["model_type"], string> = {
  chat: "Chat",
  completion: "Completion",
  embedding: "Embedding",
  reranker: "Reranker",
  custom: "Custom",
};

export function ModelTable({ models, onEdit, onDelete, sortField = "name", sortDirection = "asc", onSort = () => undefined }: ModelTableProps) {
  return (
    <TableContainer component={Paper} variant="outlined">
      <Table sx={{ minWidth: 1050 }}>
        <TableHead>
          <TableRow>
            <TableCell><DataTableSortLabel field="name" activeField={sortField} direction={sortDirection} label="Model" onSort={onSort} /></TableCell>
            <TableCell><DataTableSortLabel field="provider" activeField={sortField} direction={sortDirection} label="Provider" onSort={onSort} /></TableCell>
            <TableCell><DataTableSortLabel field="model_identifier" activeField={sortField} direction={sortDirection} label="Identifier" onSort={onSort} /></TableCell>
            <TableCell>Type</TableCell>
            <TableCell>Pricing</TableCell>
            <TableCell>Status</TableCell>
            <TableCell align="right">Actions</TableCell>
          </TableRow>
        </TableHead>

        <TableBody>
          {models.map((model) => (
            <TableRow
              key={model.id}
              hover
              sx={{
                "&:last-child td, &:last-child th": {
                  border: 0,
                },
              }}
            >
              <TableCell>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  {model.name}
                </Typography>
              </TableCell>

              <TableCell>
                <Typography variant="body2">
                  {providerLabels[model.provider]}
                </Typography>
              </TableCell>

              <TableCell>
                <Typography variant="body2" color="text.secondary">
                  {model.model_identifier}
                </Typography>
              </TableCell>

              <TableCell>
                <Typography variant="body2">
                  {modelTypeLabels[model.model_type]}
                </Typography>
              </TableCell>

              <TableCell>
                <Typography variant="body2">
                  {model.pricing_currency} {model.input_price_per_million} /{" "}
                  {model.output_price_per_million}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  input / output per 1M
                </Typography>
              </TableCell>

              <TableCell>
                <StatusChip active={model.is_active} />
              </TableCell>

              <TableCell align="right">
                <PermissionGate permission="write">
                  <TableActionButton label={`Edit ${model.name}`} icon={<EditOutlined fontSize="small" />} onClick={() => onEdit(model)} />
                  <TableActionButton label={`Delete ${model.name}`} icon={<DeleteOutlined fontSize="small" />} destructive onClick={() => onDelete(model)} />
                </PermissionGate>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
