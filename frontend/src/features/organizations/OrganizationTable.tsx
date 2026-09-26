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
import type { Organization } from "./api";

interface OrganizationTableProps {
  organizations: Organization[];
  onEdit: (organization: Organization) => void;
  onDelete: (organization: Organization) => void;
}

export function OrganizationTable({
  organizations,
  onEdit,
  onDelete,
}: OrganizationTableProps) {
  return (
    <TableContainer component={Paper} variant="outlined">
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Organization</TableCell>
            <TableCell>Slug</TableCell>
            <TableCell>Description</TableCell>
            <TableCell>Status</TableCell>
            <TableCell align="right">Actions</TableCell>
          </TableRow>
        </TableHead>

        <TableBody>
          {organizations.map((organization) => (
            <TableRow
              key={organization.id}
              hover
              sx={{
                "&:last-child td, &:last-child th": {
                  border: 0,
                },
              }}
            >
              <TableCell>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  {organization.name}
                </Typography>
              </TableCell>

              <TableCell>
                <Typography
                  variant="body2"
                  color="text.secondary"
                >
                  {organization.slug}
                </Typography>
              </TableCell>

              <TableCell>
                <Typography
                  variant="body2"
                  color={
                    organization.description
                      ? "text.primary"
                      : "text.secondary"
                  }
                >
                  {organization.description ?? "No description"}
                </Typography>
              </TableCell>

              <TableCell>
                <StatusChip active={organization.is_active} />
              </TableCell>

              <TableCell align="right">
                <Tooltip title="Edit organization">
                  <IconButton
                    aria-label={`Edit ${organization.name}`}
                    onClick={() => onEdit(organization)}
                    size="small"
                  >
                    <EditOutlined fontSize="small" />
                  </IconButton>
                </Tooltip>

                <Tooltip title="Delete organization">
                  <IconButton
                    aria-label={`Delete ${organization.name}`}
                    onClick={() => onDelete(organization)}
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