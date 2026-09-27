import {
  DeleteOutlined,
  EditOutlined,
} from "@mui/icons-material";
import {
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
} from "@mui/material";
import { StatusChip } from "../../components/common/StatusChip";
import type { Model } from "./api";

interface ModelTableProps {
  models: Model[];
  onEdit: (model: Model) => void;
  onDelete: (model: Model) => void;
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

export function ModelTable({
  models,
  onEdit,
  onDelete,
}: ModelTableProps) {
  return (
    <TableContainer component={Paper} variant="outlined">
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Model</TableCell>
            <TableCell>Provider</TableCell>
            <TableCell>Identifier</TableCell>
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
                <Typography
                  variant="body2"
                  color="text.secondary"
                >
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
                  {model.pricing_currency}{" "}
                  {model.input_price_per_million} /{" "}
                  {model.output_price_per_million}
                </Typography>
                <Typography
                  variant="caption"
                  color="text.secondary"
                >
                  input / output per 1M
                </Typography>
              </TableCell>

              <TableCell>
                <StatusChip active={model.is_active} />
              </TableCell>

              <TableCell align="right">
                <Tooltip title="Edit model">
                  <IconButton
                    aria-label={`Edit ${model.name}`}
                    onClick={() => onEdit(model)}
                    size="small"
                  >
                    <EditOutlined fontSize="small" />
                  </IconButton>
                </Tooltip>

                <Tooltip title="Delete model">
                  <IconButton
                    aria-label={`Delete ${model.name}`}
                    onClick={() => onDelete(model)}
                    size="small"
                    color="error"
                  >
                    <DeleteOutlined fontSize="small" />
                  </IconButton>
                </Tooltip>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
