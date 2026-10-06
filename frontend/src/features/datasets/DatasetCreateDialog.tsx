import CloseIcon from "@mui/icons-material/Close";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  Divider,
  IconButton,
  Stack,
  Typography,
  alpha,
  useTheme,
} from "@mui/material";
import { DatasetForm } from "./DatasetForm";
import type { CreateDatasetPayload } from "./api";
import { useCreateDataset } from "./hooks";

interface DatasetCreateDialogProps {
  open: boolean;
  projectId: string;
  onClose: () => void;
}

export function DatasetCreateDialog({
  open,
  projectId,
  onClose,
}: DatasetCreateDialogProps) {
  const theme = useTheme();
  const createMutation = useCreateDataset();

  const handleClose = () => {
    if (createMutation.isPending) return;
    createMutation.reset();
    onClose();
  };

  const handleSubmit = async (
    values: Parameters<React.ComponentProps<typeof DatasetForm>["onSubmit"]>[0],
  ) => {
    const payload: CreateDatasetPayload = {
      project_id: projectId,
      name: values.name,
      slug: values.slug,
      description: values.description || null,
      dataset_type: values.dataset_type,
    };

    await createMutation.mutateAsync(payload);
    handleClose();
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      fullWidth
      maxWidth="sm"
      aria-labelledby="dataset-create-dialog-title"
      slotProps={{
        paper: {
          elevation: 12,
          sx: {
            borderRadius: 2.5,
            overflow: "hidden",
          },
        },
      }}
    >
      <DialogTitle
        id="dataset-create-dialog-title"
        sx={{
          m: 0,
          px: 3,
          py: 2,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          bgcolor: (theme) =>
            theme.palette.mode === "dark"
              ? alpha(theme.palette.common.white, 0.03)
              : alpha(theme.palette.common.black, 0.02),
        }}
      >
        <Stack spacing={0.5}>
          <Typography
            variant="h6"
            sx={{ fontWeight: 600, fontSize: "1.125rem" }}
          >
            Create Dataset
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Add a new dataset collection to store evaluation cases
          </Typography>
        </Stack>

        <IconButton
          aria-label="close"
          onClick={handleClose}
          disabled={createMutation.isPending}
          size="small"
          sx={{
            color: theme.palette.text.secondary,
            "&:hover": {
              color: theme.palette.text.primary,
              bgcolor: alpha(theme.palette.text.primary, 0.06),
            },
          }}
        >
          <CloseIcon fontSize="small" />
        </IconButton>
      </DialogTitle>

      <Divider />

      <DialogContent sx={{ p: 3 }}>
        <DatasetForm
          submitting={createMutation.isPending}
          onSubmit={handleSubmit}
          onCancel={handleClose}
        />
      </DialogContent>
    </Dialog>
  );
}
