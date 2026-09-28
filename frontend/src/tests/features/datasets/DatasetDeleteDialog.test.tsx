import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { DatasetDeleteDialog } from "../../../features/datasets/DatasetDeleteDialog";
import type { Dataset } from "../../../features/datasets/api";

const mutateAsync = vi.fn();

vi.mock(
  "../../../features/datasets/hooks",
  () => ({
    useDeleteDataset: () => ({
      mutateAsync,
      isPending: false,
    }),
  }),
);

vi.mock(
  "../../../components/common/ConfirmDialog",
  () => ({
    ConfirmDialog: ({
      open,
      title,
      message,
      confirmLabel,
      onConfirm,
      onCancel,
    }: {
      open: boolean;
      title: string;
      message: string;
      confirmLabel: string;
      onConfirm: () => void;
      onCancel: () => void;
    }) =>
      open ? (
        <div role="dialog">
          <h2>{title}</h2>
          <p>{message}</p>
          <button type="button" onClick={onConfirm}>
            {confirmLabel}
          </button>
          <button type="button" onClick={onCancel}>
            Cancel
          </button>
        </div>
      ) : null,
  }),
);

const dataset: Dataset = {
  id: "dataset-1",
  project_id: "project-1",
  name: "RAG Evaluation",
  slug: "rag-evaluation",
  description: "RAG evaluation dataset",
  dataset_type: "rag",
  is_active: true,
};

describe("DatasetDeleteDialog", () => {
  it("renders the dataset confirmation message", () => {
    render(
      <DatasetDeleteDialog
        open
        dataset={dataset}
        onClose={vi.fn()}
      />,
    );

    expect(screen.getByText("Delete Dataset")).toBeInTheDocument();
    expect(
      screen.getByText(
        'Are you sure you want to delete "RAG Evaluation"? This action cannot be undone.',
      ),
    ).toBeInTheDocument();
  });

  it("does not render when closed", () => {
    render(
      <DatasetDeleteDialog
        open={false}
        dataset={dataset}
        onClose={vi.fn()}
      />,
    );

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("deletes the selected dataset", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    mutateAsync.mockReset();
    mutateAsync.mockResolvedValue(undefined);

    render(
      <DatasetDeleteDialog
        open
        dataset={dataset}
        onClose={onClose}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Delete" }));

    expect(mutateAsync).toHaveBeenCalledWith("dataset-1");
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("calls onClose when cancelled", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(
      <DatasetDeleteDialog
        open
        dataset={dataset}
        onClose={onClose}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
