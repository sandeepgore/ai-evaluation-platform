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
import type { Dataset, UpdateDatasetPayload } from "./api";
import { useUpdateDataset } from "./hooks";

interface DatasetEditDialogProps {
  open: boolean;
  dataset: Dataset | null;
  onClose: () => void;
}

export function DatasetEditDialog({
  open,
  dataset,
  onClose,
}: DatasetEditDialogProps) {
  const theme = useTheme();
  const updateMutation = useUpdateDataset();

  const handleClose = () => {
    if (updateMutation.isPending) return;
    updateMutation.reset();
    onClose();
  };

  const handleSubmit = async (
    values: Parameters<React.ComponentProps<typeof DatasetForm>["onSubmit"]>[0],
  ) => {
    if (!dataset) return;

    const payload: UpdateDatasetPayload = {
      name: values.name,
      slug: values.slug,
      description: values.description || null,
      dataset_type: values.dataset_type,
    };

    await updateMutation.mutateAsync({
      datasetId: dataset.id,
      payload,
    });

    handleClose();
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      fullWidth
      maxWidth="sm"
      aria-labelledby="dataset-edit-dialog-title"
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
        id="dataset-edit-dialog-title"
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
            Edit Dataset
          </Typography>
          {dataset && (
            <Typography variant="caption" color="text.secondary">
              Update configurations for &quot;{dataset.name}&quot;
            </Typography>
          )}
        </Stack>

        <IconButton
          aria-label="close"
          onClick={handleClose}
          disabled={updateMutation.isPending}
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
        {dataset && (
          <DatasetForm
            dataset={dataset}
            submitting={updateMutation.isPending}
            onSubmit={handleSubmit}
            onCancel={handleClose}
          />
        )}
      </DialogContent>
    </Dialog>
  );
}
