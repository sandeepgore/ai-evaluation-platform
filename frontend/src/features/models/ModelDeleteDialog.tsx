import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
} from "@mui/material";
import type { Model } from "./api";
import { useDeleteModel } from "./hooks";

interface ModelDeleteDialogProps {
  open: boolean;
  model: Model | null;
  onClose: () => void;
}

export function ModelDeleteDialog({
  open,
  model,
  onClose,
}: ModelDeleteDialogProps) {
  const deleteMutation = useDeleteModel();

  const handleDelete = async () => {
    if (!model) {
      return;
    }

    await deleteMutation.mutateAsync(model.id);

    onClose();
  };

  return (
    <Dialog
      open={open}
      onClose={deleteMutation.isPending ? undefined : onClose}
      fullWidth
      maxWidth="sm"
    >
      <DialogTitle>Delete Model</DialogTitle>

      <DialogContent>
        <DialogContentText>
          Are you sure you want to delete{" "}
          <strong>{model?.name}</strong>? This action cannot be
          undone.
        </DialogContentText>
      </DialogContent>

      <DialogActions>
        <Button
          onClick={onClose}
          disabled={deleteMutation.isPending}
        >
          Cancel
        </Button>

        <Button
          onClick={handleDelete}
          color="error"
          variant="contained"
          disabled={deleteMutation.isPending || !model}
        >
          {deleteMutation.isPending ? "Deleting..." : "Delete"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
